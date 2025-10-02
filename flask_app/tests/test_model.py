import pytest
import sys
import os
import psycopg
from unittest.mock import patch, MagicMock

# Ajouter le chemin du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from flask_app import model

# Configuration de test
TEST_DATABASE_URL = "postgresql://test_user:test_pass@localhost:5432/test_db"

class TestModel:
    """Tests pour le module model avec PostgreSQL"""
    
    @pytest.fixture
    def mock_connection(self):
        """Mock de la connexion PostgreSQL"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        return mock_conn, mock_cursor
    
    def test_connect_with_env_var(self, mock_connection):
        """Test de la fonction connect avec variable d'environnement"""
        with patch.dict(os.environ, {'DATABASE_URL': TEST_DATABASE_URL}):
            with patch('psycopg.connect') as mock_connect:
                mock_connect.return_value = mock_connection[0]
                conn = model.connect()
                mock_connect.assert_called_once_with(TEST_DATABASE_URL)
    
    def test_connect_with_parameter(self, mock_connection):
        """Test de la fonction connect avec paramètre"""
        with patch('psycopg.connect') as mock_connect:
            mock_connect.return_value = mock_connection[0]
            conn = model.connect(TEST_DATABASE_URL)
            mock_connect.assert_called_once_with(TEST_DATABASE_URL)
    
    def test_connect_missing_env_var(self):
        """Test de la fonction connect sans variable d'environnement"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception, match="Variable d'environnement DATABASE_URL manquante"):
                model.connect()
    
    def test_add_user(self, mock_connection):
        """Test de l'ajout d'un utilisateur"""
        mock_conn, mock_cursor = mock_connection
        
        # Mock du hashage du mot de passe
        with patch('model.hash_password', return_value='hashed_password'):
            model.add_user(mock_conn, 'test_user', 'test@example.com', 'password123')
            
            # Vérifier que la requête SQL a été exécutée
            mock_cursor.execute.assert_called_once()
            call_args = mock_cursor.execute.call_args[0]
            assert 'INSERT INTO users' in call_args[0]
            assert call_args[1] == ('test_user', 'test@example.com', 'hashed_password')
    
    def test_get_user_success(self, mock_connection):
        """Test de récupération d'un utilisateur (succès)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = (1, 'test_user', 'test@example.com', 'hashed_password')
        
        # Mock de la vérification du mot de passe
        with patch('model.scrypt.verify', return_value=True):
            result = model.get_user(mock_conn, 'test@example.com', 'password123')
            
            assert result == {'id': 1, 'email': 'test@example.com', 'name': 'test_user'}
            mock_cursor.execute.assert_called_once()
    
    def test_get_user_not_found(self, mock_connection):
        """Test de récupération d'un utilisateur (non trouvé)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None
        
        with pytest.raises(Exception, match="Utilisateur inconnu"):
            model.get_user(mock_conn, 'test@example.com', 'password123')
    
    def test_get_user_wrong_password(self, mock_connection):
        """Test de récupération d'un utilisateur (mauvais mot de passe)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = (1, 'test_user', 'test@example.com', 'hashed_password')
        
        # Mock de la vérification du mot de passe (échec)
        with patch('model.scrypt.verify', return_value=False):
            with pytest.raises(Exception, match="Utilisateur inconnu"):
                model.get_user(mock_conn, 'test@example.com', 'wrong_password')
    
    def test_get_book_success(self, mock_connection):
        """Test de récupération d'un livre (succès)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = (1, 'Le Petit Prince', 'Antoine de Saint-Exupéry', 
                                           'Conte philosophique', '1943-04-06', '9782070612758', 
                                           'Description', '/static/Livre.jpeg')
        
        result = model.get_book(mock_conn, 1)
        
        expected = {
            'id': 1, 'title': 'Le Petit Prince', 'author': 'Antoine de Saint-Exupéry',
            'genre': 'Conte philosophique', 'publication_date': '1943-04-06',
            'isbn': '9782070612758', 'description': 'Description', 'image_url': '/static/Livre.jpeg'
        }
        assert result == expected
        mock_cursor.execute.assert_called_once()
    
    def test_get_book_not_found(self, mock_connection):
        """Test de récupération d'un livre (non trouvé)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None
        
        with pytest.raises(Exception, match="Livre inconnu"):
            model.get_book(mock_conn, 999)
    
    def test_get_lists_success(self, mock_connection):
        """Test de récupération des listes (succès)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = [
            (1, 'Classiques Français', 'Description', '/static/francais.jpeg'),
            (2, 'Philosophie', 'Description', '/static/philosophie.jpeg')
        ]
        
        result = model.get_lists(mock_conn)
        
        expected = [
            {'id': 1, 'list_name': 'Classiques Français', 'description': 'Description', 'image_url': '/static/francais.jpeg'},
            {'id': 2, 'list_name': 'Philosophie', 'description': 'Description', 'image_url': '/static/philosophie.jpeg'}
        ]
        assert result == expected
        mock_cursor.execute.assert_called_once()
    
    def test_get_lists_empty(self, mock_connection):
        """Test de récupération des listes (vide)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = []
        
        with pytest.raises(Exception, match="Aucune liste trouvée"):
            model.get_lists(mock_conn)
    
    def test_search_book_success(self, mock_connection):
        """Test de recherche de livre (succès)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = [
            (1, 'Le Petit Prince', 'Antoine de Saint-Exupéry', 'Conte philosophique', 
             '1943-04-06', '9782070612758', 'Description', '/static/Livre.jpeg')
        ]
        
        result = model.searchBook(mock_conn, 'Prince')
        
        expected = [{
            'id': 1, 'title': 'Le Petit Prince', 'author': 'Antoine de Saint-Exupéry',
            'genre': 'Conte philosophique', 'publication_date': '1943-04-06',
            'isbn': '9782070612758', 'description': 'Description', 'image_url': '/static/Livre.jpeg'
        }]
        assert result == expected
        mock_cursor.execute.assert_called_once()
    
    def test_search_book_no_results(self, mock_connection):
        """Test de recherche de livre (aucun résultat)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = []
        
        with pytest.raises(Exception, match="Aucun résultat"):
            model.searchBook(mock_conn, 'Inexistant')
    
    def test_password_strength_valid(self):
        """Test de validation de mot de passe (valide)"""
        valid_passwords = [
            'Password123!',
            'MyStr0ng#Pass',
            'Test@2024$'
        ]
        
        for password in valid_passwords:
            # Ne doit pas lever d'exception
            model.check_password_strength(password)
    
    def test_password_strength_invalid(self):
        """Test de validation de mot de passe (invalide)"""
        invalid_passwords = [
            'short',           # Trop court
            'nouppercase123!', # Pas de majuscule
            'NOLOWERCASE123!', # Pas de minuscule
            'NoNumbers!',      # Pas de chiffre
            'NoSpecial123',    # Pas de caractère spécial
            'Invalid@char'     # Caractère invalide
        ]
        
        for password in invalid_passwords:
            with pytest.raises(Exception):
                model.check_password_strength(password)
    
    def test_hash_password(self):
        """Test de hashage du mot de passe"""
        password = 'TestPassword123!'
        
        with patch('model.check_password_strength'):
            with patch('model.scrypt.using') as mock_scrypt:
                mock_scrypt.return_value.hash.return_value = 'hashed_password'
                
                result = model.hash_password(password)
                
                assert result == 'hashed_password'
                mock_scrypt.assert_called_once_with(salt_size=16)
    
    def test_delete_book_success(self, mock_connection):
        """Test de suppression d'un livre (succès)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.rowcount = 1
        
        result = model.delete_book(mock_conn, 1)
        
        assert result == "Le livre a été supprimé."
        assert mock_cursor.execute.call_count == 2  # Suppression des relations + du livre
        mock_conn.commit.assert_called_once()
    
    def test_delete_book_not_found(self, mock_connection):
        """Test de suppression d'un livre (non trouvé)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.rowcount = 0
        
        result = model.delete_book(mock_conn, 999)
        
        assert result == "Le livre n'a pas été supprimé!"
    
    def test_delete_book_error(self, mock_connection):
        """Test de suppression d'un livre (erreur)"""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.execute.side_effect = Exception("Database error")
        
        result = model.delete_book(mock_conn, 1)
        
        assert result == "Le livre n'a pas été supprimé!"
        mock_conn.rollback.assert_called_once()

if __name__ == '__main__':
    pytest.main([__file__])
