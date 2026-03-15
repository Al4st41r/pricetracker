import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'pricetracker.db')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'query_items.log')
USERNAME = 'aogle'

def query_items(db_path, username, log_file):
    if not os.path.exists(db_path):
        with open(log_file, 'w') as f:
            f.write(f"Error: Database file not found at '{db_path}'")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Find the user id for the given username
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        user_record = cursor.fetchone()

        if user_record:
            user_id = user_record[0]

            # Query the tracked items for the user
            cursor.execute("SELECT * FROM tracked_item WHERE user_id = ?", (user_id,))
            items = cursor.fetchall()

            with open(log_file, 'w') as f:
                f.write(f"Tracked items for user '{username}':\n")
                for item in items:
                    f.write(str(item) + '\n')
        else:
            with open(log_file, 'w') as f:
                f.write(f"Error: User '{username}' not found in the database.")

    except sqlite3.Error as e:
        with open(log_file, 'w') as f:
            f.write(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    query_items(DATABASE_PATH, USERNAME, LOG_FILE)
