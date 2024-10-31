import sqlite3
import os
from passlib.hash import scrypt


def dictionary_factory(cursor, row):
  dictionary = {}
  for index in range(len(cursor.description)):
    column_name = cursor.description[index][0]
    dictionary[column_name] = row[index]
  return dictionary


def connect(database = "database.sqlite"):
  connection = sqlite3.connect(database)
  connection.set_trace_callback(print)
  connection.execute('PRAGMA foreign_keys = 1')
  connection.row_factory = dictionary_factory
  return connection


def read_build_script():
  path = os.path.join(os.path.dirname(__file__), 'build.sql')
  file = open(path)
  script = file.read()
  file.close()
  return script


def create_database(connection):
  script = read_build_script()
  connection.executescript(script)
  connection.commit()


def fill_database(connection):
  pass


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
  #check_password_strength(password)
  return scrypt.using(salt_size=16).hash(password)

def compare_password(password, confirm_password) :
  return password == confirm_password


def add_user(connection, name ,email, password):
  password_hash = hash_password(password)
  sql = '''
    INSERT INTO users(name,email, password_hash)
    VALUES (:name ,:email, :password_hash);
  '''
  connection.execute(sql, {
    'name' : name,
    'email' : email,
    'password_hash': password_hash
  })
  connection.commit()


def get_user(connection, email, password):
  sql = '''
    SELECT * FROM users
    WHERE email = :email;
  '''
  cursor = connection.execute(sql, {'email': email})
  users = cursor.fetchall()
  if len(users)==0:
    raise Exception('Utilisateur inconnu')
  user = users[0]
  password_hash = user['password_hash']
  if not scrypt.verify(password, password_hash):
    raise Exception('Utilisateur inconnu')
  return {'name' : user['name'],'id': user['id'], 'email': user['email']}


def change_password(connection, email, old_password, new_password):
  user = get_user(connection, email, old_password)
  password_hash = hash_password(new_password)
  sql = '''
    UPDATE users
    SET password_hash = :password_hash
    WHERE id = :id 
  '''
  connection.execute(sql, {
    'password_hash' : password_hash,
    'id': user['id']
  });
  connection.commit()


def update_totp_secret(connection, user_id, totp_secret):
  sql = '''
    UPDATE users
    SET totp = :totp_secret
    WHERE id = :user_id
  '''
  connection.execute(sql, {'user_id' : user_id, 'totp_secret': totp_secret})
  connection.commit()


def totp_enabled(connection, user):
  sql = '''
    SELECT * FROM users
    WHERE id = :id AND totp IS NULL
  '''
  rows = connection.execute(sql, {'id' : user['id']}).fetchall()
  return len(rows) == 0


def totp_secret(connection, user):
  sql = '''
    SELECT totp FROM users
    WHERE id = :id AND totp IS NOT NULL
  '''
  rows = connection.execute(sql, {'id' : user['id']}).fetchall()
  if len(rows) == 0:
    raise Exception("Échec de la double authentification")
  return rows[0]['totp']