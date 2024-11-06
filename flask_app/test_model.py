import pytest
from flask_app import model


def test_add_and_get_user():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.add_user(connection, 'test1@example.com', '1Secret1234**')
    model.add_user(connection, 'test2@example.com', '2Secret1234**')
    user1 = model.get_user(connection, 'test1@example.com', '1Secret1234**')
    user2 = model.get_user(connection, 'test2@example.com', '2Secret1234**')
    assert user1 == {'id' : 1, 'email' : 'test1@example.com'}
    assert user2 == {'id' : 2, 'email' : 'test2@example.com'}


def test_get_user_exception():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.add_user(connection, 'test@example.com', 'Secret1234**')
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
    model.add_user(connection, 'test1@example.com', '1Secret1234**')
    with pytest.raises(Exception) as exception_info:
        model.add_user(connection, 'test1@example.com', '2Secret1234**')
    assert str(exception_info.value) == 'UNIQUE constraint failed: users.email'


def test_change_password():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.add_user(connection, 'test@example.com', '1Secret1234**')
    model.change_password(connection, 'test@example.com', '1Secret1234**', '2Secret1234**')
    user = model.get_user(connection, 'test@example.com', '2Secret1234**')
    assert user == {'id' : 1, 'email' : 'test@example.com'}
    with pytest.raises(Exception) as exception_info:
        model.get_user(connection, 'test@example.com', '1Secret1234**')
    assert str(exception_info.value) == 'Utilisateur inconnu'


def test_change_password_old_password_check():
    connection = model.connect(":memory:")
    model.create_database(connection)
    model.add_user(connection, 'test@example.com', '1Secret1234**')
    with pytest.raises(Exception) as exception_info:
        model.change_password(connection, 'test@example.com', '2Secret1234**', '3Secret1234**')
    assert str(exception_info.value) == 'Utilisateur inconnu'


def test_check_password_strength_length():
    with pytest.raises(Exception) as exception_info:
        model.check_password_strength('aaa')
    assert str(exception_info.value) == 'Mot de passe trop court'