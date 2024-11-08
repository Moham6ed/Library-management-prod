import pytest
from flask_app import model, data


def test_add_and_get_user():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.add_user(connection,'name1' ,'test1@example.com', '1Secret1234**')
    model.add_user(connection, 'name2','test2@example.com', '2Secret1234**')
    user1 = model.get_user(connection,'test1@example.com', '1Secret1234**')
    user2 = model.get_user(connection, 'test2@example.com', '2Secret1234**')
    assert user1 == {'id' : 1, 'email' : 'test1@example.com', 'name': 'name1'}
    assert user2 == {'id' : 2, 'email' : 'test2@example.com', 'name': 'name2'}


def test_get_user_exception():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.add_user(connection, 'name','test@example.com', 'Secret1234**')
    with pytest.raises(Exception) as exception_info:
        model.get_user(connection, 'test1@example.com', 'Secret1234**')
    assert str(exception_info.value) == 'Utilisateur inconnu'
    with pytest.raises(Exception) as exception_info:
        model.get_user(connection, 'test@example.com', '1Secret1234**')
    assert str(exception_info.value) == 'Utilisateur inconnu'
    with pytest.raises(Exception) as exception_info:
        model.get_user(connection, 'test1@example.com', '1Secret1234**')
    assert str(exception_info.value) == 'Utilisateur inconnu'


def test_add_user_email_unique():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.create_database(connection)
    model.add_user(connection, 'name1','test1@example.com', '1Secret1234**')
    with pytest.raises(Exception) as exception_info:
        model.add_user(connection, 'name4','test1@example.com', '2Secret1234**')
    assert str(exception_info.value) == 'UNIQUE constraint failed: users.email'


def test_change_password():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.add_user(connection, 'name','test@example.com', '1Secret1234**')
    model.change_password(connection, 'test@example.com', '1Secret1234**', '2Secret1234**')
    user = model.get_user(connection, 'test@example.com', '2Secret1234**')
    assert user == {'id' : 1, 'email' : 'test@example.com', 'name' : 'name'}
    with pytest.raises(Exception) as exception_info:
        model.get_user(connection, 'test@example.com', '1Secret1234**')
    assert str(exception_info.value) == 'Utilisateur inconnu'


def test_change_password_old_password_check():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.add_user(connection, 'name','test@example.com', '1Secret1234**')
    with pytest.raises(Exception) as exception_info:
        model.change_password(connection, 'test@example.com', '2Secret1234**', '3Secret1234**')
    assert str(exception_info.value) == 'Utilisateur inconnu'


def test_check_password_strength_length():       # A revoir à la fin
    with pytest.raises(Exception) as exception_info:
        model.check_password_strength('aaa')
    assert str(exception_info.value) == 'Mot de passe trop court'


def test_get_book_and_insert_book() :
    connection = model.connect(":memory:")
    model.create_database(connection)
    books = data.books()
    model.insert_book(connection,books[0])
    book_id = books[0]['id']
    book = model.get_book(connection, book_id)
    assert book == books[0]

def test_get_books_in_list():
    # Création de la connexion en mémoire
    connection = model.connect(":memory:")
    model.create_database(connection)
    
    # Insertion des données de test
    for book in data.books():
        model.insert_book(connection, book)
    for book_list in data.book_lists():
        model.insert_book_list(connection, book_list)
    for relation in data.book_list_relations():
        model.insert_book_list_relation(connection, {'book_id': relation[0], 'list_id': relation[1]})
    
    # Test pour la liste avec list_id = 1
    books = model.get_books_in_list(connection, 1)
    assert len(books) > 0
    for book in books:
        assert 'id' in book
        assert 'title' in book
        assert 'author' in book
        assert 'genre' in book
        assert 'publication_date' in book
        assert 'isbn' in book
        assert 'description' in book
        assert 'stock' in book

def test_get_lists_of_book():
    # Création de la connexion en mémoire
    connection = model.connect(":memory:")
    model.create_database(connection)
    
    # Insertion des données de test
    for book in data.books():
        model.insert_book(connection, book)
    for book_list in data.book_lists():
        model.insert_book_list(connection, book_list)
    for relation in data.book_list_relations():
        model.insert_book_list_relation(connection, {'book_id': relation[0], 'list_id': relation[1]})
    
    # Test pour le livre avec book_id = 1
    lists = model.get_lists_of_book(connection, 1)
    assert len(lists) > 0
    for book_list in lists:
        assert 'id' in book_list
        assert 'list_name' in book_list
        assert 'description' in book_list

def test_get_lists():
    connection = model.connect(":memory:")
    model.create_database(connection)
    
    # Insère toutes les listes dans la base de données
    for book_list in data.book_lists():
        model.insert_book_list(connection, book_list)
    
    # Récupère toutes les listes depuis la base de données
    retrieved_lists = model.get_lists(connection)
    
    # Vérifie que toutes les listes insérées sont bien présentes et dans le même ordre
    assert retrieved_lists == data.book_lists()
