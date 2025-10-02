#!/bin/bash
#pour debian ou ubuntu important avec la version "16" de postgrsesql sinon il faut changer le repetoire du nom du fichier de configuration postgresql.conf et pg_hba.conf

# Script de déploiement pour VM BDD (PostgreSQL)
# À exécuter sur la VM BDD après avoir copié les fichiers

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement de la base de données PostgreSQL..."

# Variables de configuration
DB_NAME="app_bibliotheque_db"
DB_USER="mohhhhamed_hebbbbache"
DB_PASSWORD="HolalaHolala"
DB_HOST="localhost"
DB_PORT="5432"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si on est root
if [[ $EUID -eq 0 ]]; then
   log_error "Ce script ne doit pas être exécuté en tant que root"
   exit 1
fi

# Détecter la distribution Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    log_error "Impossible de détecter la distribution Linux"
    exit 1
fi

log_info "Distribution détectée: $OS $VER"

# Installation de PostgreSQL
log_info "Installation de PostgreSQL..."
    sudo apt update
    sudo apt install -y postgresql postgresql-contrib python3 python3-pip python3-venv

# Démarrer PostgreSQL
log_info "Démarrage de PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configuration de PostgreSQL
log_info "Configuration de PostgreSQL..."

# Modifier postgresql.conf pour écouter sur toutes les interfaces
PG_CONFIG="/etc/postgresql/16/main/postgresql.conf"

sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '0.0.0.0'/" "$PG_CONFIG"
sudo sed -i "s/listen_addresses = 'localhost'/listen_addresses = '0.0.0.0'/" "$PG_CONFIG"


# Configuration de pg_hba.conf
log_info "Configuration de l'authentification..."

PG_HBA="/etc/postgresql/16/main/pg_hba.conf"


# Ajouter la ligne d'authentification pour l'utilisateur app
echo "host    $DB_NAME    $DB_USER    0.0.0.0/0    md5" | sudo tee -a "$PG_HBA"

# Redémarrer PostgreSQL
log_info "Redémarrage de PostgreSQL..."
sudo systemctl restart postgresql

# Créer la base de données et l'utilisateur
log_info "Création de la base de données et de l'utilisateur..."
sudo -u postgres psql << EOF
CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';
CREATE DATABASE $DB_NAME OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

# Configuration du firewall
log_info "Configuration du firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 5432/tcp
    sudo ufw --force enable
elif command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=5432/tcp
    sudo firewall-cmd --reload
else
    log_warn "Aucun gestionnaire de firewall détecté. Configurez manuellement le port 5432."
fi

# Installation des dépendances Python
log_info "Installation des dépendances Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_db.txt

# Initialisation de la base de données
log_info "Initialisation de la base de données..."
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

# Créer le schéma
psql "$DATABASE_URL" -f build_postgres.sql

# Insérer les données
python seed_postgres.py

# Vérification finale
log_info "Vérification de l'installation..."
psql "$DATABASE_URL" -c "\dt"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM books;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM book_lists;"
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM users;"

log_info "✅ Installation terminée avec succès!"
log_info "Base de données: $DB_NAME"
log_info "Utilisateur: $DB_USER"
log_info "Port: $DB_PORT"
log_info "URL de connexion: $DATABASE_URL"

echo ""
log_info "📋 Prochaines étapes:"
echo "1. Notez l'IP de cette VM BDD"
echo "2. Configurez le firewall pour autoriser l'IP de la VM Web"
echo "3. Déployez l'application sur la VM Web"