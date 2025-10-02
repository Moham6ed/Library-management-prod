-- Schéma PostgreSQL pour Library Management System
-- Adapté depuis build.sql (SQLite) vers PostgreSQL

DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS book_list_relations CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS book_lists CASCADE;

-- Table des utilisateurs
CREATE TABLE users(
    id SERIAL PRIMARY KEY,
    name VARCHAR(32) NOT NULL,
    email VARCHAR(128) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    totp VARCHAR(32)
);

-- Table des livres
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    genre VARCHAR(100),
    publication_date DATE,
    isbn VARCHAR(20) UNIQUE,
    description TEXT,
    image_url VARCHAR(255)
);

-- Table des listes de livres
CREATE TABLE book_lists (
    id SERIAL PRIMARY KEY,
    list_name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(255)
);

-- Table de relations entre livres et listes
CREATE TABLE book_list_relations (
    id SERIAL PRIMARY KEY,
    book_id INTEGER,
    list_id INTEGER,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (list_id) REFERENCES book_lists(id) ON DELETE CASCADE
);

-- Index pour améliorer les performances
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_books_genre ON books(genre);
CREATE INDEX idx_book_list_relations_book_id ON book_list_relations(book_id);
CREATE INDEX idx_book_list_relations_list_id ON book_list_relations(list_id);
CREATE INDEX idx_users_email ON users(email);
