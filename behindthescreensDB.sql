DROP DATABASE IF EXISTS behindthescreens;
CREATE DATABASE behindthescreens;
USE behindthescreens;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL,
    password VARCHAR(1000) NOT NULL,
    email VARCHAR(150) NOT NULL,
    confirmed_email BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(1000) NOT NULL
);

CREATE TABLE get_url (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(150) NOT NULL,
    attempt VARCHAR(150) NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE youtube_url (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(150) NOT NULL,
    video_name VARCHAR(500) NOT NULL,
    video_id VARCHAR(150) NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comment VARCHAR(50000) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (url_id) REFERENCES youtube_url(id) ON DELETE CASCADE
);

CREATE TABLE summarized_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    summary VARCHAR(50000) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (url_id) REFERENCES youtube_url(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE frequent_words (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(150) NOT NULL,
    count INT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (url_id) REFERENCES youtube_url(id) ON DELETE CASCADE
);

CREATE TABLE sentiment_counter (
    id INT AUTO_INCREMENT PRIMARY KEY,
    positive INT NOT NULL,
    negative INT NOT NULL,
    neutral INT NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (url_id) REFERENCES youtube_url(id) ON DELETE CASCADE
);

CREATE TABLE word_cloud (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_positive_data VARCHAR(1000),
    image_negative_data VARCHAR(1000),
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (url_id) REFERENCES youtube_url(id) ON DELETE CASCADE
);

-- USER AUDIT TRAIL
CREATE TABLE user_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    users VARCHAR(150) NOT NULL, -- username of the user, will get from the users table
    action VARCHAR(500) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL -- NOT FOREIGN KEY, but it will still get the user_id from the users table
);

-- ADMIN AUDIT TRAIL
CREATE TABLE admin_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(500) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    admin_id INT NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE
);
