# Library Management System

## Description

Ce projet est une application Flask pour la gestion de bibliothèque en ligne déployée sur **deux VMs séparées** pour une architecture scalable et sécurisée.

### Fonctionnalités
- ✅ Gestion des livres (ajout, recherche, suppression, modification)
- ✅ Gestion des utilisateurs avec authentification
- ✅ Listes de livres personnalisées
- ✅ Interface web moderne et responsive
- ✅ Authentification à deux facteurs (TOTP)
- ✅ Recherche avancée de livres

### Architecture
- **VM BDD** : PostgreSQL (installation native)
- **VM Web** : Flask (conteneurisé avec Docker)

## Prérequis

### VM BDD (PostgreSQL)
- Ubuntu 20.04+ ou CentOS 7+
- 2 CPU, 4 GB RAM, 20 GB stockage
- Accès réseau depuis la VM Web

### VM Web (Flask)
- Ubuntu 20.04+ ou CentOS 7+
- 2 CPU, 2 GB RAM, 10 GB stockage
- Docker et Docker Compose
- Accès réseau vers la VM BDD

## Déploiement

### Étape 1 : VM BDD (PostgreSQL)

1. **Créer la VM BDD** avec Ubuntu/CentOS

2. **Copier les fichiers** sur la VM BDD :
   ```bash
   scp -r infra/db/* user@vm-bdd:/opt/db-setup/
   ```

3. **Se connecter à la VM BDD** :
   ```bash
   ssh user@vm-bdd
   cd /opt/db-setup
   ```

4. **Exécuter le script d'installation** :
   ```bash
   chmod +x setup-db-vm.sh
   ./setup-db-vm.sh
   ```

5. **Noter l'IP de la VM BDD** :
   ```bash
   hostname -I
   ```

### Étape 2 : VM Web (Flask)

1. **Créer la VM Web** avec Ubuntu

2. **Cloner le repository** sur la VM Web :
   ```bash
   git clone <votre-repo> /opt/web-app/
   cd /opt/web-app
   ```

3. **Modifier les variables dans le script** :
   ```bash
   sudo nano infra/web/setup-web-vm.sh
   ```
   
   Modifier les lignes 11-15 :
   ```bash
   DB_HOST="<IP-VM-BDD>"           # Ex: "192.168.1.100"
   DB_USER="<nom-utilisateur>"     # Ex: "mohhhhamed_hebbbbache"
   DB_PASSWORD="<mot-de-passe>"    # Ex: "HolalaHolala"
   DB_NAME="<nom-base>"            # Ex: "app_bibliotheque_db"
   ```

4. **Exécuter le script d'installation** :
   ```bash
   chmod +x infra/web/setup-web-vm.sh
   sudo ./infra/web/setup-web-vm.sh
   ```

## Configuration

### Variables d'Environnement

Le script crée automatiquement un fichier `.env` avec les variables que vous avez configurées :
```bash
DATABASE_URL=postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:5432/<DB_NAME>?sslmode=disable
SECRET_KEY=<clé-générée-automatiquement>
FLASK_ENV=production
```

### Firewall

Le script configure automatiquement le firewall :
- **VM BDD** : Port 5432 (PostgreSQL) ouvert
- **VM Web** : Ports 80, 5000, 22 ouverts

## Utilisation

### Accès à l'application
- **URL principale** : `http://<IP-VM-WEB>`



## Maintenance

### Commandes utiles

#### VM BDD
```bash
# Redémarrer PostgreSQL
sudo systemctl restart postgresql

# Sauvegarder la base
pg_dump "postgresql://<DB_USER>:<DB_PASSWORD>@localhost:5432/<DB_NAME>" > backup.sql

# Vérifier l'état
sudo systemctl status postgresql
```

#### VM Web
```bash
# Voir les logs
sudo docker compose logs -f

# Redémarrer l'application
sudo docker compose restart

# Mettre à jour l'application
git pull
sudo docker compose build
sudo docker compose up -d

# Voir l'état
sudo docker compose ps
```

## Structure du Projet

```
Library-management-prod/
├── flask_app/                 # Code Flask
│   ├── __init__.py           # Application principale
│   ├── model.py              # Modèle de données (PostgreSQL)
│   ├── static/               # Fichiers statiques
│   ├── templates/            # Templates HTML
│   └── tests/                # Tests unitaires
├── infra/                    # Scripts de déploiement
│   ├── db/                   # Fichiers pour VM BDD
│   │   ├── build_postgres.sql
│   │   ├── seed_postgres.py
│   │   ├── data.py
│   │   └── setup-db-vm.sh
│   └── web/                  # Fichiers pour VM Web
│       ├── Dockerfile
│       ├── docker-compose.yml
│       └── setup-web-vm.sh
├── requirements.txt          # Dépendances Flask
└── README.md                # Ce fichier
```

## Sécurité

- ✅ Séparation des services (BDD et Web)
- ✅ Firewall configuré
- ✅ Variables d'environnement sécurisées
- ✅ Authentification robuste
- ✅ Mots de passe forts

## Support

En cas de problème :
1. Vérifier les logs des deux VMs
2. Tester la connectivité réseau
3. Vérifier la configuration des variables d'environnement
4. Consulter la documentation PostgreSQL et Docker

---

