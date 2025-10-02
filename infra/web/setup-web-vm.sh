#!/bin/bash

# Script de déploiement pour VM Web (Flask + Docker)
# À exécuter sur la VM Web après avoir configuré la VM BDD

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement de l'application Flask avec Docker..."

# Variables de configuration
APP_DIR="/opt/web-app"
DOCKER_COMPOSE_FILE="docker-compose.yml"

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

# Vérifier que c'est bien Ubuntu
if [[ "$OS" != *"Ubuntu"* ]]; then
    log_warn "Ce script est optimisé pour Ubuntu. Distribution détectée: $OS"
    read -p "Voulez-vous continuer quand même ? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation annulée"
        exit 0
    fi
fi

# Demander l'IP de la VM BDD
echo ""
read -p "Entrez l'IP de la VM BDD (PostgreSQL): " DB_HOST
if [ -z "$DB_HOST" ]; then
    log_error "L'IP de la VM BDD est requise"
    exit 1
fi

# Tester la connectivité vers la VM BDD
log_info "Test de connectivité vers la VM BDD..."
if ping -c 1 $DB_HOST > /dev/null 2>&1; then
    log_info "✅ VM BDD accessible"
else
    log_warn "⚠️  VM BDD non accessible via ping (peut être normal si firewall actif)"
fi

# Demander la clé secrète
echo ""
read -p "Entrez une clé secrète forte pour Flask (ou laissez vide pour générer): " SECRET_KEY
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -base64 32)
    log_info "Clé secrète générée: $SECRET_KEY"
fi

# Installation de Docker (Ubuntu)
log_info "Installation de Docker pour Ubuntu..."
# Supprimer les anciennes versions
sudo apt remove -y docker docker-engine docker.io containerd runc || true

# Installer les prérequis
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Ajouter la clé GPG de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Ajouter le repository Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installer Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Ajouter l'utilisateur au groupe docker
log_info "Configuration des permissions Docker..."
sudo usermod -aG docker $USER
sudo systemctl start docker
sudo systemctl enable docker

# Créer le répertoire de l'application
log_info "Création du répertoire de l'application..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copier les fichiers de l'application
log_info "Copie des fichiers de l'application..."
cp -r . $APP_DIR/
cd $APP_DIR

# Demander les identifiants de la base de données
echo ""
read -p "Entrez le nom d'utilisateur de la base de données: " DB_USER
if [ -z "$DB_USER" ]; then
    DB_USER="app_user"
    log_info "Utilisation de l'utilisateur par défaut: $DB_USER"
fi

read -p "Entrez le mot de passe de la base de données: " -s DB_PASSWORD
echo ""
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD="motdepasse-solide"
    log_info "Utilisation du mot de passe par défaut"
fi

read -p "Entrez le nom de la base de données: " DB_NAME
if [ -z "$DB_NAME" ]; then
    DB_NAME="app_bibliotheque_db"
    log_info "Utilisation de la base par défaut: $DB_NAME"
fi

# Créer le fichier .env
log_info "Création du fichier de configuration..."
cat > .env << EOF
# Configuration générée automatiquement - NE PAS COMMITER
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:5432/$DB_NAME?sslmode=disable
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
EOF

# S'assurer que le fichier .env n'est pas dans le git
if [ -f .gitignore ]; then
    if ! grep -q "\.env" .gitignore; then
        echo ".env" >> .gitignore
        log_info "Ajout de .env au .gitignore"
    fi
else
    echo ".env" > .gitignore
    log_info "Création du .gitignore avec .env"
fi

# Construire et démarrer l'application
log_info "Construction de l'image Docker..."
docker compose build

log_info "Démarrage de l'application..."
docker compose up -d

# Attendre que l'application soit prête
log_info "Attente du démarrage de l'application..."
sleep 10

# Vérification de l'état
log_info "Vérification de l'état de l'application..."
docker compose ps

# Test de connectivité
log_info "Test de connectivité..."
if curl -f http://localhost:5000/ > /dev/null 2>&1; then
    log_info "✅ Application accessible sur http://localhost:5000"
else
    log_warn "⚠️  Application non accessible sur le port 5000"
fi

if curl -f http://localhost/ > /dev/null 2>&1; then
    log_info "✅ Application accessible sur http://localhost"
else
    log_warn "⚠️  Application non accessible sur le port 80"
fi

# Configuration du firewall (Ubuntu UFW)
log_info "Configuration du firewall UFW..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 5000/tcp  # Flask (pour debug)
# Port 443 (HTTPS) commenté car pas de SSL pour le moment
# sudo ufw allow 443/tcp
sudo ufw --force enable
log_info "✅ Firewall UFW configuré (SSH, HTTP, Flask debug)"

# Afficher les logs
log_info "Affichage des logs de l'application..."
echo ""
log_info "📋 Commandes utiles:"
echo "  - Voir les logs: docker compose logs -f"
echo "  - Redémarrer: docker compose restart"
echo "  - Arrêter: docker compose down"
echo "  - Voir l'état: docker compose ps"

echo ""
log_info "✅ Déploiement terminé avec succès!"
log_info "Application accessible sur: http://$(hostname -I | awk '{print $1}')"
log_info "Application accessible sur: http://$(hostname -I | awk '{print $1}'):5000 (debug)"
log_info "Répertoire de l'application: $APP_DIR"

echo ""
log_info "📋 Configuration:"
echo "  - Base de données: $DB_HOST:5432 (sans SSL)"
echo "  - Clé secrète: $SECRET_KEY"
echo "  - Environnement: production"
echo "  - Firewall: SSH (22), HTTP (80), Flask debug (5000)"
