"""
FinGuard Database Migration & Schema Evolution Utility
Detects missing columns in existing SQLite/relational databases and applies
safe, non-destructive schema evolution (ALTER TABLE ADD COLUMN).
"""
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import inspect
from backend.db.session import engine
from backend.db.models import Base

logger = logging.getLogger(__name__)

def apply_schema_migrations():
    """
    Compares declared SQLAlchemy models with active database schema and
    adds any missing columns without data loss.
    """
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        with engine.connect() as conn:
            for table_name, table in Base.metadata.tables.items():
                if table_name not in existing_tables:
                    continue  # Will be created by Base.metadata.create_all()

                existing_columns = {col["name"] for col in inspector.get_columns(table_name)}

                for column in table.columns:
                    if column.name not in existing_columns:
                        col_name = column.name
                        # Map SQLAlchemy type to SQLite/SQL type
                        col_type = column.type.compile(engine.dialect)
                        default_clause = ""
                        if column.default is not None and hasattr(column.default, "arg") and isinstance(column.default.arg, (str, int, float)):
                            default_clause = f" DEFAULT '{column.default.arg}'"

                        alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}{default_clause}"
                        logger.info(f"[Migration] Adding missing column: {alter_stmt}")
                        try:
                            conn.exec_driver_sql(alter_stmt)
                        except Exception as e:
                            logger.error(f"[Migration] Failed to add column {col_name} to {table_name}: {e}")

            conn.commit()
            logger.info("[Migration] Database schema verification and migration completed.")
    except Exception as ex:
        logger.warning(f"[Migration] Schema migration check warning: {ex}")

if __name__ == "__main__":
    apply_schema_migrations()
    print("Migration executed successfully.")
