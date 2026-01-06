"""
PHASE 6 - CLEANUP & RELIABILITY: Database Configuration and Management

This module provides enhanced database configuration with foreign key enforcement,
connection pooling, and production-ready database management features.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sqlite3
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_database_engine():
    """
    PHASE 6: Create database engine with enhanced configuration.
    
    Configures database engine with proper connection pooling,
    foreign key enforcement, and production-ready settings.
    """
    
    # SQLite-specific configuration
    if settings.DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            settings.DATABASE_URL,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,  # 30 second timeout
            },
            echo=settings.DEBUG,  # Log SQL queries in debug mode
            echo_pool=settings.DEBUG,  # Log connection pool events
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections every hour
        )
        
        # Enable foreign key constraints for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Enable foreign key constraints and other SQLite optimizations."""
            cursor = dbapi_connection.cursor()
            
            # PHASE 6: Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Performance optimizations - Production Ready
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging (enables concurrent reads)
            cursor.execute("PRAGMA synchronous=NORMAL")  # Balance safety and speed (WAL allows NORMAL)
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache (negative = KB, positive = pages)
            cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
            cursor.execute("PRAGMA page_size=4096")  # 4KB page size (optimal for most systems)
            cursor.execute("PRAGMA optimize")  # Run optimization analysis
            cursor.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
            
            cursor.close()
            logger.info("SQLite pragmas configured: foreign_keys=ON, WAL mode enabled")
    
    else:
        # PostgreSQL/MySQL configuration
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            echo_pool=settings.DEBUG,
            pool_size=20,  # Connection pool size
            max_overflow=30,  # Additional connections beyond pool_size
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "connect_timeout": 30,
            }
        )
        logger.info("Database engine configured for PostgreSQL/MySQL")
    
    return engine


def create_session_factory(engine):
    """
    PHASE 6: Create session factory with proper configuration.
    
    Creates a sessionmaker with appropriate settings for
    production use including autocommit and autoflush behavior.
    """
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,  # Manual flush control for better performance
        expire_on_commit=False,  # Keep objects accessible after commit
    )


def verify_database_connection(engine):
    """
    PHASE 6: Verify database connection and constraints.
    
    Tests database connectivity and verifies that foreign key
    constraints are properly enabled.
    """
    try:
        with engine.connect() as connection:
            # Test basic connectivity
            result = connection.execute("SELECT 1").fetchone()
            if result[0] != 1:
                raise Exception("Database connectivity test failed")
            
            # Check foreign key enforcement (SQLite specific)
            if settings.DATABASE_URL.startswith("sqlite"):
                fk_result = connection.execute("PRAGMA foreign_keys").fetchone()
                if fk_result[0] != 1:
                    logger.warning("Foreign key constraints are not enabled!")
                    return False
                else:
                    logger.info("Foreign key constraints are properly enabled")
            
            logger.info("Database connection verified successfully")
            return True
            
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        return False


def get_database_info(engine):
    """
    PHASE 6: Get database information for monitoring.
    
    Returns database configuration and status information
    for monitoring and debugging purposes.
    """
    try:
        with engine.connect() as connection:
            info = {
                "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL,
                "pool_size": getattr(engine.pool, 'size', 'N/A'),
                "pool_checked_out": getattr(engine.pool, 'checkedout', 'N/A'),
                "pool_overflow": getattr(engine.pool, 'overflow', 'N/A'),
                "pool_checked_in": getattr(engine.pool, 'checkedin', 'N/A'),
            }
            
            # SQLite specific information
            if settings.DATABASE_URL.startswith("sqlite"):
                pragma_results = {}
                pragmas = [
                    "foreign_keys", "journal_mode", "synchronous", 
                    "cache_size", "temp_store", "mmap_size"
                ]
                
                for pragma in pragmas:
                    try:
                        result = connection.execute(f"PRAGMA {pragma}").fetchone()
                        pragma_results[pragma] = result[0] if result else "unknown"
                    except Exception:
                        pragma_results[pragma] = "error"
                
                info["sqlite_pragmas"] = pragma_results
            
            return info
            
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"error": str(e)}


# Global database engine and session factory
engine = create_database_engine()
SessionLocal = create_session_factory(engine)

# Verify database connection on module import
if not verify_database_connection(engine):
    logger.error("Database connection verification failed during startup!")
else:
    logger.info("Database configuration completed successfully")