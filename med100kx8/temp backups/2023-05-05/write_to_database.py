import queue
import json
from datetime import datetime
import math
import pymysql


# If DB writing is needed this function is called. It runs in its own thread, uses an async queue, and uses connection pooling
def write_to_database(mysql_pool, data_queue):
    while True:

        data = data_queue.get()
        if data is None:  # We use None as a sentinel value to indicate that we're done
            break

        # Get connection from the connection pool
        cnx1 = mysql_pool.connection()
        cursor = cnx1.cursor()

        # Extract the table name and remove it from the data dictionary
        table = data.pop('table')
        
        # Prepare the SQL query
        fields = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        add_data = f"INSERT INTO {table} ({fields}) VALUES ({placeholders})"
        
        cursor = cnx1.cursor()

        # Execute the SQL command
        cursor.execute(add_data, list(data.values()))

        # Commit your changes in the database
        cnx1.commit()

        cursor.close()
        cnx1.close()
