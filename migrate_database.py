"""
Database migration script to add new columns for detailed issue/PR tracking.

Run this script once to update existing database with new columns.
"""
from sqlalchemy import create_engine, text, inspect
from app.database import SQLALCHEMY_DATABASE_URL
import os

def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_database():
    """Add new columns to repositories table if they don't exist"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    
    with engine.begin() as conn:
        # Check if table exists first
        inspector = inspect(engine)
        if 'repositories' not in inspector.get_table_names():
            print("Repositories table does not exist. It will be created automatically on first run.")
            return
        
        # Check and add columns if they don't exist
        columns_to_add = [
            ('issues_open', 'INTEGER DEFAULT 0'),
            ('issues_closed', 'INTEGER DEFAULT 0'),
            ('prs_open', 'INTEGER DEFAULT 0'),
            ('prs_closed', 'INTEGER DEFAULT 0')
        ]
        
        for column_name, column_def in columns_to_add:
            if not column_exists(conn, 'repositories', column_name):
                try:
                    conn.execute(text(f"""
                        ALTER TABLE repositories 
                        ADD COLUMN {column_name} {column_def}
                    """))
                    print(f"[OK] Added {column_name} column")
                except Exception as e:
                    print(f"[ERROR] Error adding {column_name} column: {e}")
            else:
                print(f"[SKIP] Column {column_name} already exists")
        
        print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate_database()

