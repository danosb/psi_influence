import pymysql
import json
from datetime import datetime
import sys


# Looks up the max supertrial number so we can properly assign supertrial for our run
def get_supertrial(mysql_pool):

    supertrial = 0

    try:
        # Get connection from the connection pool
        cnx1 = mysql_pool.connection()
        cursor = cnx1.cursor()

        # Get the current max supertrial
        cursor.execute("SELECT MAX(supertrial) FROM trial_data")
        result = cursor.fetchone()

        # Store supertrial number
        if result is not None and result[0] is not None and isinstance(result[0], int):
            supertrial = result[0] + 1
        else:
            supertrial = 1

        print(f"supertrial:", (supertrial))

        return supertrial

        # Close the cursor and connection
        cursor.close()
        cnx1.close()

    except pymysql.Error as err:
        print("Error accessing MySQL database: {}".format(err))
        return None