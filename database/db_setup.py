import mysql.connector
from database.config import db_config
def create_connection():
    return mysql.connector.connect(**db_config)

db = mysql.connector.connect(**db_config)
cursor = db.cursor(dictionary=True)
