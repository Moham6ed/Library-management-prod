# Base pour les projets de Programmation Web (Master 1 RT)

## Configuration

Pour installer les dépendances requises :

```
pip3 install -r requirements.txt
```

Pour créer un fichier `.env` à partir de l'exemple :

```
cp example.env .env
```

## Exécution du projet

Pour exécuter le projet :

```
flask run
```

## Initialisation de la base de données

Dans un interpréteur Python :

```
from flask_app import model
connection = model.connect()
model.create_database(connection)
model.fill_database(connection)
model.update_ranking(connection)
```