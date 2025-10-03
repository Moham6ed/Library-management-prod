import os
import psycopg
from passlib.hash import scrypt
from PIL import Image

def dictionary_factory(cursor, row):
  """Factory pour créer des dictionnaires à partir des résultats PostgreSQL"""
  dictionary = {}
  for index in range(len(cursor.description)):
    column_name = cursor.description[index][0]
    dictionary[column_name] = row[index]
  return dictionary


def connect(database_url=None):
  """Connexion à la base PostgreSQL"""
  if database_url is None:
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
      raise Exception("Variable d'environnement DATABASE_URL manquante")
  
  connection = psycopg.connect(database_url)
  # PostgreSQL n'a pas besoin de PRAGMA foreign_keys, c'est activé par défaut
  return connection


# Fonction read_build_script supprimée - utilisée seulement pour l'initialisation de la BDD
# Le script est maintenant dans infra/db/build_postgres.sql


# Fonction create_database supprimée - utilisée seulement pour l'initialisation de la BDD
# Le schéma est maintenant créé par infra/db/build_postgres.sql


def insert_book(connection, book):
    """Insérer un livre dans la base PostgreSQL"""
    sql = '''
    INSERT INTO books 
    (title, author, genre, publication_date, isbn, description, image_url) 
    VALUES 
    (%(title)s, %(author)s, %(genre)s, %(publication_date)s, %(isbn)s, %(description)s, %(image_url)s)
    RETURNING id
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql, {
            'title': book['title'],
            'author': book['author'],
            'genre': book['genre'],
            'publication_date': book['publication_date'],
            'isbn': book['isbn'],
            'description': book['description'],
            'image_url': book['image_url']
        })
        result = cursor.fetchone()
        connection.commit()
        return result[0] if result else None


def insert_book_list(connection, book_list):
    """Insérer une liste de livres dans la base PostgreSQL"""
    sql = '''INSERT INTO book_lists 
             (id, list_name, description, image_url) 
             VALUES 
             (%(id)s, %(list_name)s, %(description)s, %(image_url)s)'''
    with connection.cursor() as cursor:
        cursor.execute(sql, book_list)
        connection.commit()

def insert_book_list_relation(connection, book_list_relation):
    """Insérer une relation livre-liste dans la base PostgreSQL"""
    sql = '''INSERT INTO book_list_relations 
             (book_id, list_id) 
             VALUES 
             (%s, %s)'''
    with connection.cursor() as cursor:
        cursor.execute(sql, book_list_relation)
        connection.commit()


def get_book(connection, id):
  """Récupérer un livre par son ID depuis PostgreSQL"""
  sql = '''
          SELECT * FROM books
    WHERE id = %s; 
'''
  with connection.cursor() as cursor:
    cursor.execute(sql, (id,))
    book = cursor.fetchone()
    if not book:
      raise Exception('Livre inconnu')
    return {
      'id': book[0], 'title': book[1], 'author': book[2], 'genre': book[3], 
      'publication_date': book[4], 'isbn': book[5], 'description': book[6],
      'image_url': book[7]
    }

def get_lists(connection):
    """Récupérer toutes les listes de livres depuis PostgreSQL"""
    sql = '''
        SELECT * FROM book_lists;
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql)
        lists = cursor.fetchall()
        
        if not lists:
            raise Exception('Aucune liste trouvée')
        
        return [
            {
                'id': row[0], 
                'list_name': row[1], 
                'description': row[2], 
                'image_url': row[3]
            } 
            for row in lists
        ]

def get_books_in_list(connection, list_id):
    """Récupérer les livres d'une liste depuis PostgreSQL"""
    sql = '''
        SELECT books.* FROM books
        INNER JOIN book_list_relations ON books.id = book_list_relations.book_id
        WHERE book_list_relations.list_id = %s;
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql, (list_id,))
        books = cursor.fetchall()
        
        if not books:
            raise Exception('Aucun livre trouvé pour cette liste.')
        
        return [
            {
                'id': book[0], 
                'title': book[1], 
                'author': book[2], 
                'genre': book[3],
                'publication_date': book[4], 
                'isbn': book[5], 
                'description': book[6], 
                'image_url': book[7]
            } for book in books
        ]

def get_lists_of_book(connection, book_id):
    """Récupérer les listes contenant un livre depuis PostgreSQL"""
    sql = '''
        SELECT book_lists.* FROM book_lists
        INNER JOIN book_list_relations ON book_lists.id = book_list_relations.list_id
        WHERE book_list_relations.book_id = %s;
    '''
    with connection.cursor() as cursor:
        cursor.execute(sql, (book_id,))
        lists = cursor.fetchall()
        
        if not lists:
            raise Exception('Aucune liste trouvée pour ce livre.')
        
        return [
            {
                'id': book_list[0], 
                'list_name': book_list[1], 
                'description': book_list[2]
            } for book_list in lists
        ]

def check_password_strength(password):
  if len(password) < 12:
    raise Exception("Mot de passe trop court")
  lower = False
  upper = False
  digit = False
  special = False
  for character in password:
    if 'a' <= character <= 'z' :
      lower = True
    elif 'A' <= character <= 'Z' :
      upper = True
    elif '0' <= character <= '9' :
      digit = True
    elif character in '(~`! @#$%^&*()_-+={[}]|:;"\'<,>.?/)':
      special = True
    else:
      raise Exception("Caractère invalide")
  if not(lower and upper and digit and special):
    raise Exception('''Le mot de passe doit contenir au moins 
                    un chiffre, une minuscule, une majuscule et un caractère spécial''')


def hash_password(password):
  check_password_strength(password)
  return scrypt.using(salt_size=16).hash(password)

def compare_password(password, confirm_password) :
  return password == confirm_password


def add_user(connection, name, email, password):
  """Ajouter un utilisateur dans PostgreSQL"""
  password_hash = hash_password(password)
  sql = '''
    INSERT INTO users(name, email, password_hash)
    VALUES (%s, %s, %s);
  '''
  with connection.cursor() as cursor:
    cursor.execute(sql, (name, email, password_hash))
    connection.commit()


def get_user(connection, email, password):
  """Récupérer un utilisateur depuis PostgreSQL"""
  sql = '''
    SELECT * FROM users
    WHERE email = %s;
  '''
  with connection.cursor() as cursor:
    cursor.execute(sql, (email,))
    user = cursor.fetchone()
    if not user:
      raise Exception('Utilisateur inconnu')
    password_hash = user[3]  # password_hash est à l'index 3
    if not scrypt.verify(password, password_hash):
      raise Exception('Utilisateur inconnu')
    return {'id': user[0], 'email': user[2], 'name': user[1]}


def change_password(connection, email, old_password, new_password):
  """Changer le mot de passe d'un utilisateur dans PostgreSQL"""
  user = get_user(connection, email, old_password)
  password_hash = hash_password(new_password)
  sql = '''
    UPDATE users
    SET password_hash = %s
    WHERE id = %s 
  '''
  with connection.cursor() as cursor:
    cursor.execute(sql, (password_hash, user['id']))
    connection.commit()


def update_totp_secret(connection, user_id, totp_secret):
  """Mettre à jour le secret TOTP d'un utilisateur dans PostgreSQL"""
  sql = '''
    UPDATE users
    SET totp = %s
    WHERE id = %s
  '''
  with connection.cursor() as cursor:
    cursor.execute(sql, (totp_secret, user_id))
    connection.commit()


def totp_enabled(connection, user):
  """Vérifier si TOTP est activé pour un utilisateur dans PostgreSQL"""
  sql = '''
    SELECT * FROM users
    WHERE id = %s AND totp IS NULL
  '''
  with connection.cursor() as cursor:
    cursor.execute(sql, (user['id'],))
    rows = cursor.fetchall()
    return len(rows) == 0


def totp_secret(connection, user):
  """Récupérer le secret TOTP d'un utilisateur depuis PostgreSQL"""
  sql = '''
    SELECT totp FROM users
    WHERE id = %s AND totp IS NOT NULL
  '''
  with connection.cursor() as cursor:
    cursor.execute(sql, (user['id'],))
    rows = cursor.fetchall()
    if len(rows) == 0:
      raise Exception("Échec de la double authentification")
    return rows[0][0]

def searchBook(connection, nameBook):
  """Rechercher des livres par titre dans PostgreSQL"""
  sql = '''
          SELECT * FROM books
    WHERE title ILIKE %s
  '''
  with connection.cursor() as cursor:
    cursor.execute(sql, (f'%{nameBook}%',))
    books = cursor.fetchall()
    if len(books)==0:
      raise Exception('Aucun résultat')
    return [
        {
            'id': book[0], 
            'title': book[1], 
            'author': book[2], 
            'genre': book[3],
            'publication_date': book[4], 
            'isbn': book[5], 
            'description': book[6], 
            'image_url': book[7]
        } for book in books
    ]
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_image(file):
    try:
        img = Image.open(file)
        img.verify()  
        file.seek(0)  
        return True
    except (IOError, SyntaxError) as e:
        return False

def delete_book(connection, id_book):
  """Supprimer un livre et ses relations dans PostgreSQL"""
  try:
      with connection.cursor() as cursor:
          sql_relation = '''
              DELETE FROM book_list_relations
              WHERE book_id = %s;
          '''
          cursor.execute(sql_relation, (id_book,))
          
          sql = '''
              DELETE FROM books
              WHERE id = %s;
          '''
          cursor.execute(sql, (id_book,))
          
          if cursor.rowcount > 0:
              connection.commit()
              return "Le livre a été supprimé."
          else:
              return "Le livre n'a pas été supprimé!"
  except Exception as e:
      connection.rollback()
      return "Le livre n'a pas été supprimé!"
  
 


