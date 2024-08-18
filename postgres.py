import psycopg2
from psycopg2 import sql, connect
from datetime import datetime, timedelta


class TarotDatabase:
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

        CREATE TABLE IF NOT EXISTS session (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id),
            question TEXT,
            stage VARCHAR(25),
            response_id INTEGER,
            current_card INTEGER,
            session_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS response (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES session(id),
            cards TEXT,
            summary TEXT
        );
        


        CREATE TABLE IF NOT EXISTS current_session (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id),
            session_id INTEGER REFERENCES session(id)
        );

        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def create_user(self, id, username, email, phone_number):
        insert_query = sql.SQL(
            """
        INSERT INTO users (id, username, email, phone_number)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """
        )
        self.cursor.execute(insert_query, (id, username, email, phone_number))
        user_id = self.cursor.fetchone()[0]

        insert_subscription_query = sql.SQL(
            """
        INSERT INTO subscriptions (user_id, plan, end_date)
        VALUES (%s, 'free', NULL)
        """
        )
        self.cursor.execute(insert_subscription_query, (user_id,))

        self.conn.commit()
        return user_id

    def create_session(self, user_id, stage):
        insert_query = sql.SQL(
            """
            INSERT INTO session (user_id,stage)
            VALUES (%s , %s)
            RETURNING id
            """
        )
        self.cursor.execute(insert_query, (user_id, stage))

        # Retrieve the newly created session ID
        session_id = self.cursor.fetchone()[0]

        insert_current_session_query = sql.SQL(
            """
            INSERT INTO current_session (user_id, session_id)
            VALUES (%s, %s)
            """
        )
        self.cursor.execute(insert_current_session_query, (user_id, session_id))

        # Commit the transaction
        self.conn.commit()

        return session_id

    def create_response(
        self, session_id, cards, summary, stage, current_card, question
    ):
        insert_query = sql.SQL(
            """
            INSERT INTO response (session_id, cards,summary)
            VALUES (%s, %s , %s)
            RETURNING id
            """
        )
        self.cursor.execute(insert_query, (session_id, cards, summary))

        # Retrieve the newly created session ID
        response_id = self.cursor.fetchone()[0]

        self.update_session(
            session_id=session_id,
            response_id=response_id,
            stage=stage,
            current_card=current_card,
            question=question,
        )

        # update_query = sql.SQL(
        #     """
        #     UPDATE session
        #     SET
        #         response_id = COALESCE(%s, response_id),
        #         stage = COALESCE(%s, stage),
        #         current_card = COALESCE(%s, current_card)
        #     WHERE id = %s
        #     """
        # )
        # self.cursor.execute(
        #     update_query, (response_id, stage, current_card, session_id)
        # )

        # Commit the transaction
        self.conn.commit()

        return session_id

    def update_subscription(self, user_id, plan, duration_months):
        if plan not in ["free", "premium"]:
            raise ValueError("Invalid plan type. Must be 'free' or 'premium'.")

        end_date = (
            datetime.now().date() + timedelta(days=30 * duration_months)
            if plan == "premium"
            else None
        )
        # daily_limit = None if plan == "premium" else 5

        update_subscription_query = sql.SQL(
            """
        UPDATE subscriptions
        SET plan = %s, start_date = CURRENT_DATE, end_date = %s
        WHERE user_id = %s
        """
        )
        self.cursor.execute(update_subscription_query, (plan, end_date, user_id))

        self.conn.commit()

    def update_session(
        self, session_id, question=None, current_card=None, stage=None, response_id=None
    ):
        # Construct the SQL query using COALESCE
        update_query = sql.SQL(
            """
            UPDATE session
            SET 
                question = COALESCE(%s, question),
                current_card = COALESCE(%s, current_card),
                stage = COALESCE(%s, stage),
                response_id = COALESCE(%s, response_id)
            WHERE id = %s
            """
        )

        # Execute the query with the provided parameters
        self.cursor.execute(
            update_query, (question, current_card, stage, response_id, session_id)
        )

        # Commit the transaction
        self.conn.commit()

    def get_user_info(self, id):
        query = sql.SQL(
            """
        SELECT u.*, s.plan, s.end_date, r.daily_limit, r.requests_today
        FROM users u
        JOIN subscriptions s ON u.id = s.user_id
        JOIN request_limits r ON u.id = r.user_id
        WHERE u.id = %s
        """
        )
        self.cursor.execute(query, (id,))
        return self.cursor.fetchone()

    def get_plan(self, phone_number):
        try:
            query = sql.SQL(
                """
                SELECT 
                    u.id AS user_id, 
                    s.plan, 
                    
                    s.end_date
                FROM 
                    users u
                JOIN 
                    subscriptions s ON u.id = s.user_id
                WHERE 
                    u.phone_number = %s
                """
            )
            self.cursor.execute(query, (phone_number,))
            return self.cursor.fetchone()
        except psycopg2.Error as e:
                self.conn.rollback()  # Rollback the transaction in case of error
                print(f"Error occurred: {e}")
                return None

    def get_usage(self, user_id):
        query = sql.SQL(
            """
            SELECT 
                COUNT(*) AS session_count
            FROM 
                session
            WHERE 
                user_id = %s
                AND session_created >= CURRENT_DATE - INTERVAL '7 days'
                AND stage = 'end'
            """
        )
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchone()[0]

    def get_question(self, user_id):
        query = sql.SQL(
            """
            SELECT 
                question
            FROM 
                session
            WHERE 
                user_id = %s
                AND session_created >= CURRENT_DATE - INTERVAL '7 days'
            """
        )
        self.cursor.execute(query, (user_id,))
        return self.cursor.fetchall()

    def get_session(self, user_id):
        query = sql.SQL(
            """
            WITH session_info AS (
                SELECT 
                    s.id AS session_id,
                    s.stage,
                    s.current_card,
                    s.question
                FROM 
                    current_session cs
                JOIN 
                    session s ON cs.session_id = s.id
                WHERE 
                    cs.user_id = %s
            )
            SELECT 
                si.session_id,
                si.stage, 
                si.current_card,
                si.question
            FROM 
                session_info si
            LIMIT 1;
            """
        )
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        if result:
            return result
        return None

    def get_response(self,session_id):
        query = sql.SQL(
            """
            SELECT cards, summary
            FROM response
            WHERE session_id = %s
            LIMIT 1
            """
        )
        try:
            self.cursor.execute(query, (session_id,))
            results = self.cursor.fetchone()
            return results
        except psycopg2.Error as e:
            print(f"Error occurred: {e}")
            return None
        except Exception as e:
            print(e)
            return None
        
    def end_session(self, session_id):
        delete_query = sql.SQL(
            """
            DELETE FROM current_session
            WHERE session_id = %s
            """
        )

        # Execute the query with the provided session_id
        self.cursor.execute(delete_query, (session_id,))

        self.update_session(session_id=session_id,stage='end')
        # Commit the transaction
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()
