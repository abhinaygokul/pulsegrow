import sqlite3

def check_db_schema():
    try:
        conn = sqlite3.connect('pulsegrow.db')
        cursor = conn.cursor()
        
        print("Checking 'videos' table schema...")
        cursor.execute("PRAGMA table_info(videos)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Columns: {columns}")
        
        if "analysis_status" in columns:
            print("SUCCESS: 'analysis_status' column exists.")
        else:
            print("FAILURE: 'analysis_status' column MISSING!")
            # Attempt to add it
            print("Attempting to add column...")
            try:
                cursor.execute("ALTER TABLE videos ADD COLUMN analysis_status VARCHAR DEFAULT 'pending'")
                conn.commit()
                print("SUCCESS: Added 'analysis_status' column.")
            except Exception as e:
                print(f"ERROR adding column: {e}")
                
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    check_db_schema()
