import sqlite3

def run_migration():
    conn = sqlite3.connect('finguard.db')
    cursor = conn.cursor()

    def add_col_if_missing(table, col, defn):
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cursor.fetchall()]
        if col not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
            print(f"Added {col} to {table}")
        else:
            print(f"{col} already exists in {table}")

    add_col_if_missing('transactions', 'source', "VARCHAR(30) DEFAULT 'seed'")
    add_col_if_missing('transactions', 'is_test', 'BOOLEAN DEFAULT 0')
    add_col_if_missing('investigation_cases', 'submitted_by', 'VARCHAR(50)')
    add_col_if_missing('investigation_cases', 'source', "VARCHAR(30) DEFAULT 'seed'")
    add_col_if_missing('investigation_cases', 'is_test', 'BOOLEAN DEFAULT 0')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    run_migration()
