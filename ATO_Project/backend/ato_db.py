import sqlite3
import os
from datetime import datetime
import json

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ato_storage.db")

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Decisions Log Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            model_name TEXT,
            sector TEXT,
            timestamp TEXT,
            demographic_group TEXT,
            demographic_tag TEXT,
            outcome INTEGER, -- 1 for approved, 0 for rejected
            score REAL,
            has_alert INTEGER,
            alert_reason TEXT,
            logic_steps TEXT
        )
    ''')
    
    # Feature Importance (XAI) Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS feature_importance (
            decision_id TEXT,
            feature_name TEXT,
            importance_weight REAL,
            input_value REAL,
            FOREIGN KEY(decision_id) REFERENCES decisions(id)
        )
    ''')
    
    # Compliance Logs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS compliance_logs (
            tstamp TEXT,
            level TEXT,
            message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def db_log_compliance(level, message):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO compliance_logs (tstamp, level, message) VALUES (?, ?, ?)",
              (datetime.now().isoformat(), level, message))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE) # Reset for testing
    init_db()
    print("ATO SQLite Data Layer Initialized.")
