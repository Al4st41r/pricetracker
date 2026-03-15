import sqlite3
import argparse
from werkzeug.security import generate_password_hash
import os

# --- Configuration ---
# The database path is now determined relative to the script's location.
DATABASE_NAME = 'pricetracker.db'
# Assumes the script is in the root of the project directory
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', DATABASE_NAME)

# --------------------

def reset_password(db_path, username, new_password):
    """
    Resets the password for a user in the pricetracker database.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'")
        return

    try:
        # Generate the new password hash
        password_hash = generate_password_hash(new_password)

        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Find the user
        cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
        user_record = cursor.fetchone()

        if user_record:
            user_id = user_record[0]
            
            # Update the password
            cursor.execute("UPDATE user SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            conn.commit()
            
            print(f"Successfully updated password for user '{username}'.")
        else:
            print(f"Error: User '{username}' not found in the database.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Reset a user's password for the Price Tracker application.")
    parser.add_argument("username", help="The username of the user whose password you want to reset.")
    parser.add_argument("new_password", help="The new password for the user.")
    args = parser.parse_args()

    reset_password(DATABASE_PATH, args.username, args.new_password)