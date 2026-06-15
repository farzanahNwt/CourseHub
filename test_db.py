from database import get_connection

try:
    db = get_connection()
    print("Database Connected Successfully!")
    db.close()
except Exception as e:
    print("Error:", e)