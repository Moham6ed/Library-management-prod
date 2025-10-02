#!/usr/bin/env python3
"""
Script d'initialisation des données pour PostgreSQL
À exécuter sur la VM BDD après avoir créé le schéma
"""

import os
import sys
import psycopg
from passlib.hash import scrypt

# Import des données depuis le fichier local
from data import books, book_lists, book_list_relations

def check_password_strength(password):
    """Vérification de la force du mot de passe"""
    if len(password) < 12:
        raise Exception("Mot de passe trop court")
    lower = False
    upper = False
    digit = False
    special = False
    for character in password:
        if 'a' <= character <= 'z':
            lower = True
        elif 'A' <= character <= 'Z':
            upper = True
        elif '0' <= character <= '9':
            digit = True
        elif character in '(~`! @#$%^&*()_-+={[}]|:;"\'<,>.?/)':
            special = True
        else:
            raise Exception("Caractère invalide")
    if not (lower and upper and digit and special):
        raise Exception('''Le mot de passe doit contenir au moins 
                    un chiffre, une minuscule, une majuscule et un caractère spécial''')

def hash_password(password):
    """Hashage du mot de passe avec scrypt"""
    check_password_strength(password)
    return scrypt.using(salt_size=16).hash(password)

def seed_books(cur):
    """Insérer les livres dans la base"""
    print("Insertion des livres...")
    sql = """
        INSERT INTO books (title, author, genre, publication_date, isbn, description, image_url)
        VALUES (%(title)s, %(author)s, %(genre)s, %(publication_date)s, %(isbn)s, %(description)s, %(image_url)s)
        ON CONFLICT (isbn) DO NOTHING;
    """
    for book in books():
        cur.execute(sql, book)
    print(f"✓ {len(books())} livres insérés")

def seed_book_lists(cur):
    """Insérer les listes de livres"""
    print("Insertion des listes de livres...")
    sql = """
        INSERT INTO book_lists (id, list_name, description, image_url)
        VALUES (%(id)s, %(list_name)s, %(description)s, %(image_url)s)
        ON CONFLICT (id) DO NOTHING;
    """
    for book_list in book_lists():
        cur.execute(sql, book_list)
    print(f"✓ {len(book_lists())} listes insérées")

def seed_relations(cur):
    """Insérer les relations entre livres et listes"""
    print("Insertion des relations...")
    sql = """
        INSERT INTO book_list_relations (book_id, list_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING;
    """
    for (book_id, list_id) in book_list_relations():
        cur.execute(sql, (book_id, list_id))
    print(f"✓ {len(book_list_relations())} relations insérées")

def seed_admin_user(cur, name, email, password):
    """Créer l'utilisateur administrateur"""
    print("Création de l'utilisateur administrateur...")
    password_hash = hash_password(password)
    sql = """
        INSERT INTO users (name, email, password_hash)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO NOTHING;
    """
    cur.execute(sql, (name, email, password_hash))
    print("✓ Utilisateur administrateur créé")

def main():
    """Fonction principale"""
    # Récupérer l'URL de la base depuis les variables d'environnement
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ Erreur: Variable d'environnement DATABASE_URL manquante")
        print("Exemple: export DATABASE_URL='postgresql://app_user:password@localhost:5432/app_db'")
        sys.exit(1)
    
    try:
        print("🔌 Connexion à la base de données...")
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                print("✓ Connexion établie")
                
                # Vérifier que les tables existent
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name IN ('books', 'book_lists', 'users', 'book_list_relations')
                """)
                tables = [row[0] for row in cur.fetchall()]
                if len(tables) != 4:
                    print("❌ Erreur: Les tables n'existent pas. Exécutez d'abord build_postgres.sql")
                    sys.exit(1)
                
                # Insérer les données
                seed_books(cur)
                seed_book_lists(cur)
                seed_relations(cur)
                seed_admin_user(cur, "admin", "admin@example.com", 'AAAbbccd@"9klk')
                
                # Commit des changements
                conn.commit()
                print("\n✅ Initialisation terminée avec succès!")
                
                # Vérification finale
                cur.execute("SELECT COUNT(*) FROM books")
                books_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM book_lists")
                lists_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM book_list_relations")
                relations_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM users")
                users_count = cur.fetchone()[0]
                
                print(f"\n📊 Résumé:")
                print(f"   - {books_count} livres")
                print(f"   - {lists_count} listes")
                print(f"   - {relations_count} relations")
                print(f"   - {users_count} utilisateurs")
                
    except psycopg.Error as e:
        print(f"❌ Erreur de base de données: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
