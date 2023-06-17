DROP TABLE IF EXISTS supertrial_data;
DROP TABLE IF EXISTS paricipant;
DROP TABLE IF EXISTS solar_data;
DROP TABLE IF EXISTS local_data;
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
    influence_type VARCHAR(255),
    number_steps INT,
    count_subtrial_per_trial INT,
    duration_seconds INT,
    window_size INT,
    count_trials_completed INT,
    significance_threshold FLOAT,
    created_datetime DATETIME
);

CREATE TABLE IF NOT EXISTS participant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    participant_name VARCHAR(255),
    age INT,
    gender VARCHAR(255),
    feeling INT,
    energy_level INT,
    focus_level INT,
    meditated BOOLEAN,
    eaten_recently BOOLEAN,
    technique_description VARCHAR(255),
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
    window_total_reached_target INT,
    created_datetime DATETIME
);

CREATE TABLE IF NOT EXISTS solar_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    dst_index INT,
    kp_index FLOAT,
    BSR INT,
    ap_small INT,
    ap_big INT,
    SN INT,
    F10_7obs FLOAT,
    F10_7adj FLOAT,
    created_datetime DATETIME
);

CREATE TABLE IF NOT EXISTS local_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supertrial INT,
    local_temp_fahrenheit FLOAT,
    local_humidity_percent FLOAT,
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
    p_calculated FLOAT,
    SV FLOAT,
    created_datetime DATETIME
);

ALTER TABLE trial_data ADD INDEX supertrial_index (supertrial);

/*
    select
          s.supertrial as 'Supertrial ID'
        , s.number_steps as 'Configured n bound'
        , s.window_size as 'Configured window size'
        , s.significance_threshold as 'Configured significance threshold'
        , s.count_subtrial_per_trial as 'Configured count subtrial per trial'
        , s.duration_seconds as 'Configured duration in seconds'
        , t.trial as 'Trial ID'
        , t.trial_cum_sv as 'Trial cumulative SV'
        , t.trial_weighted_sv as 'Trial weighted SV'
        , t.trial_norm_weighted_sv as 'Trial normalized weighted SV'
        , t.z_value as 'Trial z-value'
        , t.p_value as 'Trial p-value'
        , w.window_z_value as 'Window z-value'
        , w.window_p_value as 'Window p-value'
        , w.window_SV as 'Window SV'
        , w.window_result_significant as 'Window result significant?'
        , w.count_window_total as 'Cumulative window count'
        , w.count_window_hit as 'Cumulative window hit count'
        , w.window_total_p as 'Cumulative window p-value'
        , w.window_total_SV as 'Cumulative window SV'
        , w.window_total_reached_target as 'Cumulative number windows that reached target'
    from trial_data t
    left join window_data w on w.created_by_trial = t.trial and w.supertrial = t.supertrial
    left join supertrial_data s on s.supertrial = t.supertrial
    where s.supertrial=12
/*