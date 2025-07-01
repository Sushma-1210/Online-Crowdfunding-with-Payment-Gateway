# init.py

import sqlite3

# Connect to SQLite database (this creates a new database file if it doesn't exist)
conn = sqlite3.connect('crowdconnect_new.db')
conn.execute("PRAGMA foreign_keys = ON")  # Enforce foreign key constraints
cursor = conn.cursor()

# Recreate schema if needed (safe to disable in production)
RECREATE_SCHEMA = True

if RECREATE_SCHEMA:
    print("🧨 Dropping and recreating tables...")
    cursor.execute("DROP TABLE IF EXISTS donations")
    cursor.execute("DROP TABLE IF EXISTS projects")
    cursor.execute("DROP TABLE IF EXISTS users")

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    mobile TEXT NOT NULL,
    password TEXT NOT NULL
);
''')

# Create projects table
cursor.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0
);
''')

# Create donations table
cursor.execute('''
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);
''')

# Insert sample data if projects table is empty
cursor.execute("SELECT COUNT(*) FROM projects")
if cursor.fetchone()[0] == 0:
    sample_projects = [
        ("Clean Water Initiative", "Providing clean water in rural areas.", 10000),
        ("Tree Planting Campaign", "Planting 1,000 trees to combat deforestation.", 5000),
        ("Open Source Dev Fund", "Support indie open-source developers.", 3000)
    ]
    cursor.executemany(
        "INSERT INTO projects (title, description, target_amount) VALUES (?, ?, ?)",
        sample_projects
    )
    print("🌱 Sample projects inserted!")

# Commit changes and close the connection
conn.commit()
conn.close()
print("\n🎉 Database initialized and verified!")
