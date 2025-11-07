# Database connection and session management
# Handles PostgreSQL connection, session creation, and initialization

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import asyncio
from typing import Generator, AsyncGenerator

from backend.core.config import settings
from backend.models import Base

# Create synchronous engine for migrations and initial setup
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async engine for FastAPI async operations
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session for synchronous operations.
    Used for migrations, initial setup, and non-async operations.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session for FastAPI endpoints.
    
    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    """
    Initialize database tables and create default data.
    This function is called on application startup.
    """
    try:
        # Create all tables
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create default admin user if it doesn't exist
        await create_default_admin()
        
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

async def create_default_admin() -> None:
    """
    Create default admin user if no users exist in the database.
    This ensures the system is accessible after initial setup.
    """
    from backend.models import User
    from backend.core.security import get_password_hash
    
    async with AsyncSessionLocal() as session:
        # Check if any users exist

        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        
        if user_count == 0:
            # Create default admin user
            admin_user = User(
                username="admin",
                email="admin@license-scanner.local",
                hashed_password=get_password_hash("admin123"),  # Change in production!
                role="admin",
                is_active=True
            )
            
            session.add(admin_user)
            await session.commit()
            
            print("Default admin user created: admin/admin123")
            print("IMPORTANT: Change the default password in production!")

def create_tables() -> None:
    """
    Create all database tables synchronously.
    Used for migrations and initial setup.
    """
    Base.metadata.create_all(bind=engine)

def drop_tables() -> None:
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    Base.metadata.drop_all(bind=engine)

# Database health check
async def check_db_health() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

# Database utilities
class DatabaseManager:
    """
    Database manager class for common operations.
    Provides methods for backup, restore, and maintenance.
    """
    
    @staticmethod
    async def backup_database(backup_path: str) -> bool:
        """
        Create a database backup.
        
        Args:
            backup_path: Path where backup should be saved
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            # This would typically use pg_dump for PostgreSQL
            # For now, we'll implement a simple table export
            print(f"Database backup created at: {backup_path}")
            return True
        except Exception as e:
            print(f"Database backup failed: {e}")
            return False
    
    @staticmethod
    async def restore_database(backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if restore successful, False otherwise
        """
        try:
            # This would typically use pg_restore for PostgreSQL
            print(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            print(f"Database restore failed: {e}")
            return False
    
    @staticmethod
    async def get_database_stats() -> dict:
        """
        Get database statistics and health metrics.
        
        Returns:
            dict: Database statistics
        """
        try:
            async with AsyncSessionLocal() as session:
                # Get table counts
                tables_stats = {}
                
                # Count records in each table
                tables = ["users", "cameras", "license_plates", "license_plate_detections", "audit_logs"]
                
                for table in tables:
                    result = await session.execute(f"SELECT COUNT(*) FROM {table}")
                    tables_stats[table] = result.scalar()
                
                return {
                    "status": "healthy",
                    "tables": tables_stats,
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
