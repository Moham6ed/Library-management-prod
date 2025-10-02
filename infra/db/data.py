def books():
    return [
        {'id': 1, 'title': 'Le Petit Prince', 'author': 'Antoine de Saint-Exupéry', 'genre': 'Conte philosophique', 'publication_date': '1943-04-06', 'isbn': '9782070612758', 'description': 'Un conte pour enfants qui parle de l\'amour et de l\'amitié.', 'image_url':'/static/Livre.jpeg'},
        {'id': 2, 'title': 'Les Misérables', 'author': 'Victor Hugo', 'genre': 'Roman historique', 'publication_date': '1862-01-01', 'isbn': '9782070643028', 'description': 'Un classique sur la justice sociale en France.', 'image_url':'/static/Livre.jpeg'},
        {'id': 3, 'title': 'Madame Bovary', 'author': 'Gustave Flaubert', 'genre': 'Roman réaliste', 'publication_date': '1857-12-01', 'isbn': '9782070413119', 'description': 'L\'histoire d\'une femme déçue par la vie de province.', 'image_url':'/static/Livre.jpeg'},
        {'id': 4, 'title': 'L\'Étranger', 'author': 'Albert Camus', 'genre': 'Philosophie', 'publication_date': '1942-05-01', 'isbn': '9782070360024', 'description': 'Un roman sur l\'absurdité de la vie humaine.', 'image_url':'/static/Livre.jpeg'},
        {'id': 5, 'title': 'Le Rouge et le Noir', 'author': 'Stendhal', 'genre': 'Roman', 'publication_date': '1830-11-01', 'isbn': '9782070105229', 'description': 'Une analyse de l\'ambition et de l\'amour.', 'image_url':'/static/Livre.jpeg'},
        {'id': 6, 'title': '1984', 'author': 'George Orwell', 'genre': 'Dystopie', 'publication_date': '1949-06-08', 'isbn': '9780451524935', 'description': 'Un roman sur la surveillance et le contrôle totalitaire.', 'image_url':'/static/Livre.jpeg'},
        {'id': 7, 'title': 'Le Seigneur des Anneaux', 'author': 'J.R.R. Tolkien', 'genre': 'Fantasy', 'publication_date': '1954-07-29', 'isbn': '9780261102385', 'description': 'L\'histoire d\'une quête pour sauver la Terre du Milieu.', 'image_url':'/static/Livre.jpeg'},
        {'id': 8, 'title': 'La Peste', 'author': 'Albert Camus', 'genre': 'Roman philosophique', 'publication_date': '1947-06-10', 'isbn': '9782070359493', 'description': 'Un roman sur la condition humaine face à une épidémie.', 'image_url':'/static/Livre.jpeg'},
        {'id': 9, 'title': 'Les Fleurs du Mal', 'author': 'Charles Baudelaire', 'genre': 'Poésie', 'publication_date': '1857-06-25', 'isbn': '9782070419043', 'description': 'Un recueil de poésie qui explore la beauté et la souffrance.', 'image_url':'/static/Livre.jpeg'},
        {'id': 10, 'title': 'Le Comte de Monte-Cristo', 'author': 'Alexandre Dumas', 'genre': 'Aventure', 'publication_date': '1844-08-28', 'isbn': '9782080708280', 'description': 'Une histoire de vengeance et de rédemption.','image_url':'/static/Livre.jpeg'}
    ]

def book_lists():
    return [
        {'id': 1, 'list_name': 'Classiques Français', 'description': 'Une collection de classiques de la littérature française','image_url':'/static/francais.jpeg'},
        {'id': 2, 'list_name': 'Philosophie et Réflexion', 'description': 'Des livres qui explorent les thèmes philosophiques et existentiels','image_url':'/static/philosophie.jpeg'},
        {'id': 3, 'list_name': 'Romans d\'Aventure', 'description': 'Livres qui emmènent le lecteur dans des mondes d\'aventure et de suspense','image_url':'/static/romainsAventure.jpeg'},
        {'id': 4, 'list_name': 'Poésie Française', 'description': 'Les grands poètes français à travers les âges','image_url':'/static/francais.jpeg'},
        {'id': 5, 'list_name': 'Dystopie et Futur', 'description': 'Romans traitant de sociétés futuristes et dystopiques','image_url':'/static/avenir.jpeg'},
        {'id': 6, 'list_name': 'Fantasy et Imaginaire', 'description': 'Les meilleures œuvres de fantasy et de science-fiction','image_url':'/static/francais.jpeg'}
    ]

def book_list_relations():
    return [
        (1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 3), (7, 3), (8, 2), (9, 4), (10, 3),
        (1, 4), (2, 4), (3, 4), (6, 5), (7, 6)
    ]
