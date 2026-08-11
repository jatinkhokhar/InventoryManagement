import mysql.connector

conn = mysql.connector.connect(
    host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    port=4000,
    user="2oYHttVxiPJa1jB.root",
    password="rE0fXO2tsl5Qp1pM",
    database="sys",
    ssl_ca="ca.pem"
)

cursor = conn.cursor()

print("✅ TiDB Connected Successfully")