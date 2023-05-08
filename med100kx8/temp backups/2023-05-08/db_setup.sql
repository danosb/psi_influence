DROP TABLE IF EXISTS supertrial_data;
DROP TABLE IF EXISTS window_data;
DROP TABLE IF EXISTS subtrial_data;
DROP TABLE IF EXISTS trial_data;

/* 
    Populate and run in terminal:

    export MYSQL_USER=value
    export MYSQL_PASSWORD=value
    export MYSQL_HOST=value
    export MYSQL_DB=value
*/

CREATE DATABASE IF NOT EXISTS myDatabase;

USE myDatabase;

CREATE TABLE IF NOT EXISTS supertrial_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    number_steps INT,
    window_size INT,
    count_trials_completed INT,
    significance_threshold FLOAT,
    participant_name VARCHAR(255),
    created_datetime DATETIME
);


CREATE TABLE IF NOT EXISTS window_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    created_by_trial INT,
    window_z_value FLOAT,
    window_p_value FLOAT,
    window_SV FLOAT,
    window_result_significant BOOLEAN,
    count_window_total INT,
    count_window_hit INT,
    window_total_p FLOAT,
    window_total_SV FLOAT,
    created_datetime DATETIME
);

CREATE TABLE IF NOT EXISTS trial_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    trial INT,
    trial_cum_sv FLOAT,
    trial_weighted_sv FLOAT,
    trial_norm_weighted_sv FLOAT,
    p_value FLOAT,
    z_value FLOAT,
    created_datetime DATETIME
);

CREATE TABLE IF NOT EXISTS subtrial_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    trial INT,
    subtrial_number INT,
    int_array TEXT,
    bidirectional_count INT,
    bidirectional_is_pos BOOLEAN,
    number_steps INT,
    x1 FLOAT,
    x2 FLOAT,
    x3 FLOAT,
    y1 FLOAT,
    y2 FLOAT,
    y3 FLOAT,
    a FLOAT,
    b FLOAT,
    c FLOAT,
    p_calculated FLOAT,
    SV FLOAT,
    created_datetime DATETIME
);

ALTER TABLE trial_data ADD INDEX supertrial_index (supertrial);

