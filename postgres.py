import psycopg2
from psycopg2 import sql, connect
from datetime import datetime, timedelta

class UserLimitChecker:
    def __init__(self, db_params):
        self.conn = connect(**db_params)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(255) PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone_number VARCHAR(20) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id),
            plan VARCHAR(10) CHECK (plan IN ('free', 'premium')) DEFAULT 'free',
            start_date DATE DEFAULT CURRENT_DATE,
            end_date DATE,
            UNIQUE (user_id)
        );

        CREATE TABLE IF NOT EXISTS request_limits (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id),
            daily_limit INTEGER,
            requests_today INTEGER DEFAULT 0,
            last_request_date DATE,
            UNIQUE (user_id)
        );
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def create_user(self, id, username, email, phone_number):
        insert_query = sql.SQL("""
        INSERT INTO users (id, username, email, phone_number)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """)
        self.cursor.execute(insert_query, (id, username, email, phone_number))
        user_id = self.cursor.fetchone()[0]

        insert_subscription_query = sql.SQL("""
        INSERT INTO subscriptions (user_id, plan, end_date)
        VALUES (%s, 'free', NULL)
        """)
        self.cursor.execute(insert_subscription_query, (user_id,))

        # Set initial request limit
        insert_limit_query = sql.SQL("""
        INSERT INTO request_limits (user_id, daily_limit, last_request_date)
        VALUES (%s, 5, CURRENT_DATE)
        """)
        self.cursor.execute(insert_limit_query, (user_id,))

        self.conn.commit()
        return user_id

    def update_subscription(self, user_id, plan, duration_months):
        if plan not in ['free', 'premium']:
            raise ValueError("Invalid plan type. Must be 'free' or 'premium'.")

        end_date = datetime.now().date() + timedelta(days=30*duration_months) if plan == 'premium' else None
        daily_limit = None if plan == 'premium' else 5

        update_subscription_query = sql.SQL("""
        UPDATE subscriptions
        SET plan = %s, start_date = CURRENT_DATE, end_date = %s
        WHERE user_id = %s
        """)
        self.cursor.execute(update_subscription_query, (plan, end_date, user_id))

        update_limit_query = sql.SQL("""
        UPDATE request_limits
        SET daily_limit = %s, requests_today = 0, last_request_date = CURRENT_DATE
        WHERE user_id = %s
        """)
        self.cursor.execute(update_limit_query, (daily_limit, user_id))

        self.conn.commit()

    def check_user_limit(self, id):
        check_query = sql.SQL("""
        SELECT u.id, r.daily_limit, r.requests_today, r.last_request_date, s.plan, s.end_date
        FROM users u
        JOIN request_limits r ON u.id = r.user_id
        JOIN subscriptions s ON u.id = s.user_id
        WHERE u.id = %s
        """)
        self.cursor.execute(check_query, (id,))
        result = self.cursor.fetchone()

        if not result:
            return False, "User not found"

        user_id, daily_limit, requests_today, last_request_date, plan, end_date = result
        today = datetime.now().date()

        # Check if premium subscription has expired
        if plan == 'premium' and end_date and end_date < today:
            self.update_subscription(user_id, 'free', 0)  # Revert to free plan
            plan = 'free'
            daily_limit = 5

        # Reset count if it's a new day
        if last_request_date != today:
            requests_today = 0

        # For premium users, always return True with None as remaining (unlimited)
        if plan == 'premium':
            return True, None

        # For free users, check against the daily limit
        if requests_today >= daily_limit:
            return False, 0

        # Increment the request count
        new_count = requests_today + 1
        update_query = sql.SQL("""
        UPDATE request_limits
        SET requests_today = %s, last_request_date = CURRENT_DATE
        WHERE user_id = %s
        """)
        self.cursor.execute(update_query, (new_count, user_id))
        self.conn.commit()

        return True, daily_limit - new_count
    
    def get_user_info(self, id):
        query = sql.SQL("""
        SELECT u.*, s.plan, s.end_date, r.daily_limit, r.requests_today
        FROM users u
        JOIN subscriptions s ON u.id = s.user_id
        JOIN request_limits r ON u.id = r.user_id
        WHERE u.id = %s
        """)
        self.cursor.execute(query, (id,))
        return self.cursor.fetchone()

    def close(self):
        self.cursor.close()
        self.conn.close()