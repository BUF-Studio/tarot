import psycopg2
# from psycopg2 import IntegrityError, sql, connect
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

class TarotDatabase:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.create_table()

    def create_table(self):
        print('create_engine')
        
        # Check if the gender enum type exists
        check_enum_exists_query = """
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'gender'
            ) AS enum_exists;
        """

        # Create type enums if they do not exist
        create_enum_query = """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gender') THEN
                    CREATE TYPE gender AS ENUM ('Male', 'Female', 'Prefer not to say');
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'model') THEN
                    CREATE TYPE model AS ENUM ('gpt-4o', 'gpt-4o-mini', 'llama3.1');
                END IF;
            END $$;
        """

        # Create tables if they do not exist
        create_table_query = """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone_number VARCHAR(20) UNIQUE NOT NULL,
                age INT,
                gender gender,
                model model DEFAULT 'gpt-4o',
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

        # Execute the queries
        with self.engine.connect() as conn:
            with conn.begin() as transaction:
                try:
                    # Check and create enums
                    conn.execute(text(check_enum_exists_query))
                    conn.execute(text(create_enum_query))

                    # Create tables
                    conn.execute(text(create_table_query))

                except Exception as e:
                    transaction.rollback()
                    print(f"Error occurred: {e}")
                    raise

    def create_user(
            self, id, username, email, phone_number, age=None, gender=None, model=None
        ):
        try:
            # SQL query to insert a user
            insert_user_query = """
            INSERT INTO users (id, username, email, phone_number, age, gender, model)
            VALUES (:id, :username, :email, :phone_number, :age, :gender, :model)
            RETURNING id
            """
            
            # SQL query to insert a default subscription
            insert_subscription_query = """
            INSERT INTO subscriptions (user_id, plan, end_date)
            VALUES (:user_id, 'free', NULL)
            """
            
            with self.engine.connect() as conn:
                transaction = conn.begin()
                # Insert user and get the generated user ID
                user_id_result = conn.execute(
                    text(insert_user_query), {
                        "id": id, 
                        "username": username, 
                        "email": email, 
                        "phone_number": phone_number,
                        "age": age, 
                        "gender": gender, 
                        "model": model
                    }
                )
                user_id = user_id_result.fetchone()[0]

                # Insert default subscription
                conn.execute(
                    text(insert_subscription_query), {"user_id": user_id}
                )

                print(f"Default subscription inserted for user ID: {user_id}")
                transaction.commit()
                return user_id, None  # Return user_id and no error message

        except IntegrityError as e:
            error_message = str(e.orig)
            if "users_email_key" in error_message:
                return None, "Email already exists"
            elif "users_phone_number_key" in error_message:
                return None, "Phone number already exists"
            elif "users_pkey" in error_message:
                return None, "User ID already exists"
            else:
                return None, "An error occurred while creating the user"

        except Exception as e:
            return None, f"An unexpected error occurred: {str(e)}"
        
    def create_session(self, user_id, stage):
        # SQL query to insert a new session
        insert_session_query = """
        INSERT INTO session (user_id, stage)
        VALUES (:user_id, :stage)
        RETURNING id
        """

        # SQL query to update the current session
        insert_current_session_query = """
        INSERT INTO current_session (user_id, session_id)
        VALUES (:user_id, :session_id)
        """

        # Use a transaction to ensure atomicity
        with self.engine.connect() as conn:
            # Begin a transaction
            with conn.begin():
                # Insert the session and get the session ID
                result = conn.execute(
                    text(insert_session_query), 
                    {"user_id": user_id, "stage": stage}
                )
                session_id = result.fetchone()[0]

                # Insert into the current_session table
                conn.execute(
                    text(insert_current_session_query), 
                    {"user_id": user_id, "session_id": session_id}
                )

        return session_id

    def create_response(
            self, session_id, cards, summary, stage, current_card, question
        ):
        # SQL query to insert a new response
        insert_response_query = """
        INSERT INTO response (session_id, cards, summary)
        VALUES (:session_id, :cards, :summary)
        RETURNING id
        """

        # Use a transaction to ensure atomicity
        with self.engine.connect() as conn:
            with conn.begin():  # Start a transaction
                # Insert the response and get the response ID
                result = conn.execute(
                    text(insert_response_query), 
                    {"session_id": session_id, "cards": cards, "summary": summary}
                )
                response_id = result.fetchone()[0]

                # Update the session with the response ID and other details
                self.update_session(
                    session_id=session_id,
                    response_id=response_id,
                    stage=stage,
                    current_card=current_card,
                    question=question,
                )

        return session_id

    def update_subscription(self, user_id, plan, duration_months):
        if plan not in ["free", "premium"]:
            raise ValueError("Invalid plan type. Must be 'free' or 'premium'.")

        # Calculate end date for premium plan
        end_date = (
            datetime.now().date() + timedelta(days=30 * duration_months)
            if plan == "premium"
            else None
        )

        update_subscription_query = """
        UPDATE subscriptions
        SET plan = :plan, start_date = CURRENT_DATE, end_date = :end_date
        WHERE user_id = :user_id
        """

        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text(update_subscription_query), 
                    {"plan": plan, "end_date": end_date, "user_id": user_id}
                )

    def update_model(self, user_id, model):
        if model not in ["gpt-4o", "gpt-4o-mini", "llama3.1"]:
            raise ValueError("Invalid model. Must be 'gpt-4o', 'gpt-4o-mini', 'llama3.1'.")

        update_model_query = """
        UPDATE users
        SET model = :model
        WHERE id = :user_id
        """

        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text(update_model_query), 
                    {"model": model, "user_id": user_id}
                )

    def update_session(
        self, session_id, question=None, current_card=None, stage=None, response_id=None
    ):
        # SQLAlchemy query using COALESCE to update the session
        update_query = """
        UPDATE session
        SET 
            question = COALESCE(:question, question),
            current_card = COALESCE(:current_card, current_card),
            stage = COALESCE(:stage, stage),
            response_id = COALESCE(:response_id, response_id)
        WHERE id = :session_id
        """

        # Execute the query with the provided parameters
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text(update_query),
                    {
                        "question": question,
                        "current_card": current_card,
                        "stage": stage,
                        "response_id": response_id,
                        "session_id": session_id
                    }
                )

    def get_user_info(self, user_id):
        try:
            # SQLAlchemy query to retrieve user info and session usage count
            query = """
            SELECT 
                u.username, 
                u.email, 
                u.phone_number, 
                u.age, 
                u.gender, 
                u.model, 
                u.created_at, 
                s.plan, 
                s.start_date, 
                s.end_date,
                (SELECT COUNT(*) 
                FROM session 
                WHERE user_id = u.id 
                AND session_created >= CURRENT_DATE - INTERVAL '7 days'
                AND stage = 'end') AS usage_count
            FROM 
                users u
            JOIN 
                subscriptions s ON u.id = s.user_id
            WHERE 
                u.id = :user_id;
            """

            # Execute the query and pass the user_id as a parameter
            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(
                        text(query), 
                        {"user_id": user_id}
                    ).fetchone()

            if result is None:
                logging.info(f"No user found for user ID: {user_id}")
                return None

            # Return the fetched user information
            return result

        except Exception as e:
            logging.error(f"Database error occurred: {e}")
            return None
    
    def update_user(self, user_id, username, phone_number, age, gender):
        update_query = """
        UPDATE users
        SET username = :username, phone_number = :phone_number, age = :age, gender = :gender
        WHERE id = :user_id
        """

        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text(update_query),
                    {
                        "username": username,
                        "phone_number": phone_number,
                        "age": age,
                        "gender": gender,
                        "user_id": user_id
                    }
                )

    def get_plan(self, phone_number):
        try:
            query = """
            SELECT 
                u.id AS user_id, 
                u.age,
                u.gender,
                s.plan, 
                s.end_date
            FROM 
                users u
            JOIN 
                subscriptions s ON u.id = s.user_id
            WHERE 
                u.phone_number = :phone_number
            """

            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(
                        text(query),
                        {"phone_number": phone_number}
                    ).fetchone()

            return result

        except Exception as e:
            logging.error(f"Error occurred: {e}")
            return None
   
    def get_model(self, user_id):
        query = """
        SELECT 
            model
        FROM 
            users
        WHERE 
            id = :user_id
        """

        with self.engine.connect() as conn:
            with conn.begin():
                result = conn.execute(
                    text(query),
                    {"user_id": user_id}
                ).fetchone()

        return result[0] if result else None

    def get_usage(self, user_id):
        query = """
        SELECT 
            COUNT(*) AS session_count
        FROM 
            session
        WHERE 
            user_id = :user_id
            AND session_created >= CURRENT_DATE - INTERVAL '7 days'
            AND stage = 'end'
        """

        with self.engine.connect() as conn:
            with conn.begin():
                result = conn.execute(
                    text(query),
                    {"user_id": user_id}
                ).fetchone()

        return result[0] if result else 0
   
    def get_question(self, user_id):
        query = """
        SELECT 
            question
        FROM 
            session
        WHERE 
            user_id = :user_id
            AND session_created >= CURRENT_DATE - INTERVAL '7 days'
        """

        with self.engine.connect() as conn:
            with conn.begin():
                result = conn.execute(
                    text(query),
                    {"user_id": user_id}
                ).fetchall()

        return result


    def get_session(self, user_id):
        query = """
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
                cs.user_id = :user_id
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

        with self.engine.connect() as conn:
            with conn.begin():
                result = conn.execute(
                    text(query),
                    {"user_id": user_id}
                ).fetchone()

        return result
  
    def get_response(self, session_id):
        query = """
        SELECT cards, summary
        FROM response
        WHERE session_id = :session_id
        LIMIT 1
        """

        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(
                        text(query),
                        {"session_id": session_id}
                    ).fetchone()

            return result

        except Exception as e:
            logging.error(f"Error occurred: {e}")
            return None
  
    def end_session(self, session_id):
        delete_query = """
        DELETE FROM current_session
        WHERE session_id = :session_id
        """

        with self.engine.connect() as conn:
            with conn.begin():
            # Delete from current_session
                conn.execute(
                    text(delete_query),
                    {"session_id": session_id}
                )

            # Update session stage to "end"
                self.update_session(session_id=session_id, stage="end")
  
    def get_user_session(self, user_id):
        try:
            query = """
            SELECT 
                session.id,
                session.question,
                session.stage,
                session.session_created,
                response.cards,
                response.summary
            FROM 
                session
            JOIN 
                response ON session.response_id = response.id
            WHERE 
                session.user_id = :user_id;
            """

            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(
                        text(query),
                        {"user_id": user_id}
                    ).fetchall()

            if not result:
                logging.info(f"No session found for user ID: {user_id}")
                return None

            return result

        except Exception as e:
            logging.error(f"Database error occurred: {e}")
            return None
  
    def get_user_session_by_id(self, session_id):
        try:
            query = """
            SELECT 
                session.id,
                session.question,
                session.stage,
                session.session_created,
                response.cards,
                response.summary
            FROM 
                session
            JOIN 
                response ON session.response_id = response.id
            WHERE 
                session.id = :session_id;
            """

            with self.engine.connect() as conn:
                with conn.begin():
                    result = conn.execute(
                        text(query),
                        {"session_id": session_id}
                    ).fetchone()

            if not result:
                logging.info(f"No session found with session ID: {session_id}")
                return None

            return result

        except Exception as e:
            logging.error(f"Database error occurred: {e}")
            return None
