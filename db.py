import mysql.connector

conn = mysql.connector.connect(
    host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    port=4000,
    user="2oYHttVxiPJa1jB.root",
    password="E3CPPMmOVah4zjqeu",
    database="sys",
    ssl_ca="ca.pem"
)

cursor = conn.cursor()

print("✅ TiDB Connected Successfully")