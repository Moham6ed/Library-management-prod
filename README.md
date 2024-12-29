MASTER 1
HEBBACHE Mohamed
BENZAIT Kuider


                                                Library Management
                                                    Description
Ce projet est une application Flask pour la gestion de bibliothèque en ligne. L'application permet de gérer des livres et des utilisateurs, et d'effectuer les actions suivantes :
Ajouter un livre
Rechercher des livres
Supprimer des livres
Mettre à jour les informations des livres

Optionnel : Ce projet utilise Docker pour faciliter le déploiement et l'exécution dans un environnement isolé.

                                                    Utilisation


                                        Méthode 1 : Utilisation avec Docker

Assurez-vous que Docker et Docker Compose sont installés sur votre machine. Vous pouvez vérifier cela en exécutant les commandes suivantes :

docker --version

docker-compose --version

Clonez ce dépôt ou téléchargez l'archive du projet.

git clone https://github.com/Moham6ed/Library-management.git 

cd Library-management

OU

Téléchargez l'archive du projet et extrayez-le. Ensuite, entrez dans le répertoire du projet :

cd Library-management

Lancez les conteneurs avec Docker Compose pour construire l'image et démarrer les services :

docker-compose up --build

Cela va démarrer deux services :

web : Le service qui exécute l'application Flask.

db_init : Un service qui initialise la base de données avec les données par défaut.

Une fois les conteneurs démarrés, l'application sera accessible à l'adresse suivante :

http://localhost:5000

                                    Méthode 2 : Utilisation sans Docker

Clonez ce dépôt ou téléchargez l'archive du projet.

git clone https://github.com/Moham6ed/Library-management.git 

cd Library-management

OU

Téléchargez l'archive du projet et extrayez-le. Ensuite, entrez dans le répertoire du projet :

cd Library-management

Créez et activez un environnement virtuel.

Pour créer un environnement virtuel :


python3 -m venv venv

Pour activer l'environnement virtuel :

Sur Linux/macOS :

source venv/bin/activate

Sur Windows :

.\venv\Scripts\activate

Installez les dépendances nécessaires en utilisant pip :

pip install -r requirements.txt

Initialisez la base de données en exécutant le script init_db.py :

python3 init_db.py

Lancez l'application Flask :

flask run

L'application sera alors accessible à l'adresse suivante :

http://localhost:5000