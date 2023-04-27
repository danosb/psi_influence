/* 

    Populate and run in terminal:

    export MYSQL_USER=value
    export MYSQL_PASSWORD=value
    export MYSQL_HOST=value
    export MYSQL_DB=value
*/

CREATE DATABASE IF NOT EXISTS myDatabase;

USE myDatabase;

CREATE TABLE IF NOT EXISTS trial_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    trial INT,
    cumulative_sv FLOAT,
    created_datetime DATETIME

);

CREATE TABLE IF NOT EXISTS subtrial_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    trial INT,
    subtrial_number INT,
    numbers_generated TEXT,
    bidirectional_count INT,
    number_steps INT,
    bidirectional_is_pos BOOLEAN,
    x1 FLOAT,
    x2 FLOAT,
    x3 FLOAT,
    y1 FLOAT,
    y2 FLOAT,
    y3 FLOAT,
    a FLOAT,
    b FLOAT,
    c FLOAT,
    CDF_calculated FLOAT,
    SV FLOAT,
    created_datetime DATETIME,
    trial_data_id INT,
    FOREIGN KEY (trial_data_id) REFERENCES trial_data(id)
);
