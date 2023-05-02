# Reports summary of results at end of supertrial
import time
import mysql.connector
import os
import pymysql


def final_output(supertrial, elapsed_time, n, trial_count, count_subtrial_per_trial):
    print(f"---------")
    print(f"")
    print(f"Trials complete. Total time taken: {elapsed_time} seconds")
    print(f"")
    print(f"Defined bound: ", n)
    print(f"Defined trial count: ", trial_count)
    print(f"Defined # subtrials per trial: ", count_subtrial_per_trial)
    print(f"")

    # Get MySQL creds from environment variables
    username = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    host = os.getenv('MYSQL_HOST')
    database = os.getenv('MYSQL_DB')

    # Connect to the MySQL database
    connection = pymysql.connect(user=username, password=password, host=host, database=database)

    cursor2 = connection.cursor()

    # Retrieve all trial and cumulative_sv values associated with supertrial
    query = "SELECT trial, trial_norm_weighted_sv FROM trial_data WHERE supertrial = %s"
    cursor2.execute(query, (supertrial,))

    # Get column names
    columns = [column[0] for column in cursor2.description]

    # Fetch all rows
    results = cursor2.fetchall()

    # Print column names
    print('\t'.join(columns))

    # Print rows
    for row in results:
        print('\t'.join(str(elem) for elem in row))

    # Close the cursor and the connection
    cursor2.close()
    connection.close()