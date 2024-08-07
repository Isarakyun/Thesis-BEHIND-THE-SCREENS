DROP DATABASE IF EXISTS behindthescreens;
CREATE DATABASE behindthescreens;
USE behindthescreens;

CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL,
    password VARCHAR(1000) NOT NULL,
    email VARCHAR(150) NOT NULL,
    profile_pic VARCHAR(150),
    confirmed_email BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(1000) NOT NULL
);

CREATE TABLE youtube_url (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(150) NOT NULL,
    video_name VARCHAR(500) NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comment VARCHAR(50000) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (url_id) REFERENCES youtube_url(id)
);

CREATE TABLE summarized_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    summary VARCHAR(50000) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (url_id) REFERENCES youtube_url(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE frequent_words (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(150) NOT NULL,
    count INT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (url_id) REFERENCES youtube_url(id)
);

CREATE TABLE sentiment_counter (
    id INT AUTO_INCREMENT PRIMARY KEY,
    positive INT NOT NULL,
    negative INT NOT NULL,
    neutral INT NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (url_id) REFERENCES youtube_url(id)
);

CREATE TABLE word_cloud (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_positive_data LONGBLOB,
    image_negative_data LONGBLOB,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (url_id) REFERENCES youtube_url(id)
);

CREATE TABLE audit_trail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL,
    action VARCHAR(500) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert admin user with plaintext password
INSERT INTO admin (email, password) VALUES ('admin', '1234');

-- Insert users with plaintext passwords
-- INSERT INTO user (username, password, email, profile_pic) VALUES 
-- ('user1', 'password1', 'user1@example.com', 'default.jpg'),
-- ('user2', 'password2', 'user2@example.com', 'default.jpg'),
-- ('user3', 'password3', 'user3@example.com', 'default.jpg'),
-- ('user4', 'password4', 'user4@example.com', 'default.jpg'),
-- ('user5', 'password5', 'user5@example.com', 'default.jpg');
