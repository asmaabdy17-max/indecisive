import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import QueuePool
from config.settings import Settings
from .models import Base

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = None
        self.SessionLocal = None
        self.init_db()

    def init_db(self):
        """Initialize database engine and create tables."""
        try:
            self.engine = create_engine(
                self.settings.database_url,
                poolclass=QueuePool,
                pool_size=self.settings.db_pool_size,
                max_overflow=self.settings.db_max_overflow,
                echo=False,
                pool_pre_ping=True,
            )

            # Create all tables
            Base.metadata.create_all(self.engine)

            # Create session factory
            self.SessionLocal = scoped_session(sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            ))

            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def close(self):
        """Close database connection."""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()

    def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False


# Global database instance
_db_instance = None


def init_database(settings: Settings = None) -> Database:
    """Initialize and return database instance."""
    global _db_instance
    if not settings:
        settings = Settings()
    _db_instance = Database(settings)
    return _db_instance


def get_db() -> Database:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = init_database()
    return _db_instance


def get_session() -> Session:
    """Get a new database session from the global instance."""
    return get_db().get_session()
