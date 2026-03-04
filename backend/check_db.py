import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'contract_analyzer.db')

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Database: {db_path}\n")
    print(f"{'Table Name':<20} | {'Rows':<10}")
    print("-" * 35)
    
    for table_name_tuple in tables:
        table_name = table_name_tuple[0]
        # skip sqlite internal tables
        if table_name.startswith('sqlite_'):
            continue
            
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name:<20} | {count:<10}")
        
    conn.close()
