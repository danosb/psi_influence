# Retrieves and sets supertrial number
import sys
import mysql.connector
import os

def get_supertrial():
    # Get MySQL creds from environment variables. Here we connect to DB to get supertrial.
    username = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    host = os.getenv('MYSQL_HOST')
    database = os.getenv('MYSQL_DB')

    # Connect to the MySQL database
    connection = mysql.connector.connect(user=username, password=password,
                              host=host, database=database)
    cursor = connection.cursor()

    # Get the current max supertrial
    cursor.execute("SELECT MAX(supertrial) FROM subtrial_data")
    result = cursor.fetchone()

    # Store supertrial number
    if result[0] is None:
        supertrial = 1
    else:
        supertrial = result[0] + 1

    return supertrial