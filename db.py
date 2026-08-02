import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Jatin#6099",
    database="inventory_db"
)

cursor = conn.cursor()

print("✅ Database Connected Successfully")