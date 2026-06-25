-- Active: 1782302077412@@127.0.0.1@3306@studynova

-- =========================================
-- CREATE DATABASE
-- =========================================

CREATE DATABASE IF NOT EXISTS studynova;

USE studynova;

-- =========================================
-- CREATE USERS TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS users (
                                     id INT PRIMARY KEY AUTO_INCREMENT,
                                     username VARCHAR(100) NOT NULL,
                                     email VARCHAR(150) UNIQUE NOT NULL,
                                     password VARCHAR(255) NOT NULL
);

-- =========================================
-- INSERT DEMO USER
-- =========================================

INSERT IGNORE INTO users (username, email, password)
VALUES (
           'Sharanabasu',
           'demo@studynova.com',
           'studynova123'
       );

-- =========================================
-- VIEW ALL USERS
-- =========================================

SELECT * FROM users;

-- =========================================
-- UPDATE USER PASSWORD
-- =========================================

UPDATE users
SET password = 'newpassword123'
WHERE email = 'demo@studynova.com';

-- =========================================
-- DELETE USER
-- =========================================

DELETE FROM users
WHERE email = 'delete@gmail.com';

-- =========================================
-- CREATE NOTES TABLE
-- =========================================

CREATE TABLE IF NOT EXISTS notes (
                                     id INT PRIMARY KEY AUTO_INCREMENT,
                                     title VARCHAR(255) NOT NULL,
                                     filename VARCHAR(255) NOT NULL,
                                     category VARCHAR(100) NOT NULL,
                                     upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- INSERT SAMPLE NOTE
-- =========================================

INSERT IGNORE INTO notes (title, filename, category)
VALUES (
           'Python Basics',
           'python_notes.pdf',
           'Python'
       );

-- =========================================
-- VIEW ALL NOTES
-- =========================================

SELECT * FROM notes;

-- =========================================
-- DELETE NOTE
-- =========================================

DELETE FROM notes
WHERE id = 1;

-- =========================================
-- SEARCH NOTES
-- =========================================

SELECT * FROM notes
WHERE category = 'Python';

-- =========================================
-- COUNT TOTAL USERS
-- =========================================

SELECT COUNT(*) AS total_users
FROM users;

SELECT COUNT(*) AS total_notes
FROM notes;