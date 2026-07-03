import sys
from sqlalchemy import text
# Clean import since the script is right next to the app folder
from app.database import engine

print("⏳ Verifying cloud container connection to MySQL via local tunnel...")
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT bank_name, COUNT(*) FROM customers GROUP BY bank_name;"))
        print("\n✅ Success! The Cloudera AI Cloud environment is securely connected.")
        for row in result:
            print(f"   - Bank: {row[0]} | Seeded Records: {row[1]}")
except Exception as e:
    print("\n❌ Cloud Connection Failed!")
    print(f"Error Details: {e}")
    sys.exit(1)