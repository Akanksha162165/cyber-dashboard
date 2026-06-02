import sqlite3, csv, os
from werkzeug.security import generate_password_hash

DB_PATH  = os.path.join("data", "cyber.db")
CSV_PATH = os.path.join("data", "cyberattacks.csv")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("Old database removed.")

conn = sqlite3.connect(DB_PATH)
c    = conn.cursor()

c.execute('''
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT UNIQUE,
    date TEXT, time TEXT,
    attack_type TEXT, source_country TEXT, target_country TEXT,
    sector TEXT, severity TEXT, status TEXT,
    duration_minutes INTEGER, data_breach TEXT
)''')

c.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT "guest",
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

with open(CSV_PATH, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        c.execute('''
            INSERT OR IGNORE INTO incidents
            (incident_id,date,time,attack_type,source_country,target_country,
             sector,severity,status,duration_minutes,data_breach)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            row['incident_id'], row['date'], row.get('time',''),
            row['attack_type'], row['source_country'], row['target_country'],
            row['sector'], row['severity'], row['status'],
            int(row['duration_minutes']) if row.get('duration_minutes','').isdigit() else 0,
            row['data_breach']
        ))

defaults = [
    ("admin",   generate_password_hash("admin123"),   "admin"),
    ("analyst", generate_password_hash("analyst123"), "analyst"),
    ("guest",   generate_password_hash("guest123"),   "guest"),
]
c.executemany(
    "INSERT OR IGNORE INTO users (username,password_hash,role) VALUES (?,?,?)",
    defaults
)

conn.commit()
count = c.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
print(f"Database created with {count} incidents and 3 default users.")
conn.close()