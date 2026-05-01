"""Database migrations module."""

import logging
from pathlib import Path
from importlib import import_module

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db_adapter):
        """Initialize migration manager."""
        self.db_adapter = db_adapter
        self.migrations_dir = Path(__file__).parent
    
    async def run_all_pending_migrations(self):
        """Run all pending migrations."""
        logger.info("🔄 Checking for pending migrations...")
        
        # Get list of migration files
        migration_files = sorted([
            f.stem for f in self.migrations_dir.glob("migration_*.py")
            if f.is_file() and f.stem != "__init__"
        ])
        
        logger.info(f"📋 Found {len(migration_files)} migration files: {migration_files}")
        
        if not migration_files:
            logger.info("✅ No migrations found")
            return
        
        # Create migrations table if it doesn't exist
        await self.db_adapter.conn.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)
        await self.db_adapter.conn.commit()
        
        # Get applied migrations
        async with self.db_adapter.conn.execute("SELECT name FROM migrations") as cursor:
            applied = {row['name'] for row in await cursor.fetchall()}
        
        logger.info(f"📋 Already applied migrations: {applied}")
        
        # Run pending migrations
        pending_count = 0
        for migration_name in migration_files:
            if migration_name not in applied:
                await self._run_migration(migration_name)
                pending_count += 1
        
        if pending_count == 0:
            logger.info("✅ All migrations already applied")
        else:
            logger.info(f"✅ Applied {pending_count} pending migrations")
    
    async def _run_migration(self, migration_name: str):
        """Run a specific migration."""
        try:
            logger.info(f"🔄 Running migration: {migration_name}...")
            
            # Import migration module
            module = import_module(f"src.data.migrations.{migration_name}")
            
            # Run migrate_up
            if hasattr(module, 'migrate_up'):
                await module.migrate_up(self.db_adapter)
            
            # Record migration
            from datetime import datetime
            await self.db_adapter.conn.execute(
                "INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
                (migration_name, datetime.now().isoformat())
            )
            await self.db_adapter.conn.commit()
            
            logger.info(f"✅ Migration completed: {migration_name}")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {migration_name} - {e}")
            raise
    
    async def rollback_migration(self, migration_name: str):
        """Rollback a specific migration."""
        try:
            logger.info(f"🔄 Rolling back migration: {migration_name}...")
            
            # Import migration module
            module = import_module(f"src.data.migrations.{migration_name}")
            
            # Run migrate_down
            if hasattr(module, 'migrate_down'):
                await module.migrate_down(self.db_adapter)
            
            # Remove migration record
            await self.db_adapter.conn.execute(
                "DELETE FROM migrations WHERE name = ?",
                (migration_name,)
            )
            await self.db_adapter.conn.commit()
            
            logger.info(f"✅ Rollback completed: {migration_name}")
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {migration_name} - {e}")
            raise
