import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'pricetracker.db')

def print_users(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM user")
        users = cursor.fetchall()
        print("Users in the database:")
        for user in users:
            print(user[0])
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    print_users(DATABASE_PATH)
