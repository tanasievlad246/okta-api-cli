import sqlite3
import logging
import os

logger = logging.getLogger(__name__)


class SqliteDatabase:
    """
    SQLite database manager for the Okta CLI.

    Handles database connection and schema initialization.
    """

    def __init__(self, db_path: str = "oktacli.db") -> None:
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access to rows
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """
        Initializes the database schema if tables don't exist.
        """
        try:
            cursor = self.connection.cursor()

            # Create tables with IF NOT EXISTS to avoid errors on subsequent runs
            # Config table for storing Okta credentials
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    api_key TEXT NOT NULL,
                    app_url TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_types (
                    id TEXT PRIMARY KEY
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    status TEXT,
                    created TEXT,
                    activated TEXT,
                    statusChanged TEXT,
                    lastLogin TEXT,
                    lastUpdated TEXT,
                    passwordChanged TEXT,
                    placementOrg TEXT,
                    type_id TEXT,
                    FOREIGN KEY (type_id) REFERENCES user_types(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    reportGroupList TEXT,
                    firstName TEXT,
                    lastName TEXT,
                    mobilePhone TEXT,
                    portalAccessGroup TEXT,
                    secondEmail TEXT,
                    ackNewBusiness INTEGER,
                    login TEXT,
                    email TEXT,
                    placementOrg TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for frequently queried columns
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_login ON user_profiles(login)
            """)

            self.connection.commit()
            logger.info("Database schema initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Error initializing database schema: {e}")
            raise

    def get_db_connection(self) -> sqlite3.Connection:
        """
        Returns the database connection.

        Returns:
            sqlite3.Connection: The database connection
        """
        return self.connection

    def close(self) -> None:
        """
        Closes the database connection.
        """
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


# Global database instance
database = SqliteDatabase()
