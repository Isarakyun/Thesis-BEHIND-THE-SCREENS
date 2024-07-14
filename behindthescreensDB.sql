DROP DATABASE IF EXISTS behindthescreens;
CREATE DATABASE behindthescreens;
USE behindthescreens;

CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL,
    password VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    profile_pic VARCHAR(150),
    confirmed_email BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE youtube_url (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url VARCHAR(150) NOT NULL,
    video_name VARCHAR(150) NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comment VARCHAR(150) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (url_id) REFERENCES youtube_url(id)
);

CREATE TABLE labeled_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comments_id INT NOT NULL,
    sentiment VARCHAR(150) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (comments_id) REFERENCES comments(id),
    FOREIGN KEY (url_id) REFERENCES youtube_url(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE summarized_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    summary VARCHAR(150) NOT NULL,
    url_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (url_id) REFERENCES youtube_url(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

CREATE TABLE frequent_words (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(150) NOT NULL,
    count INT NOT NULL,
    sentiment VARCHAR(150) NOT NULL,
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