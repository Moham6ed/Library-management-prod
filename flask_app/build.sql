DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS book_list_relations;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS book_lists;


CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(32) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    totp VARCHAR(32)
);

CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    genre VARCHAR(100),
    publication_date DATE,
    isbn VARCHAR(20) UNIQUE,
    description TEXT,
    image_url VARCHAR(255)
);

CREATE TABLE book_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    list_name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(255)
);

CREATE TABLE book_list_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    list_id INTEGER,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (list_id) REFERENCES book_lists(id)
);