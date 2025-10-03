#!/bin/bash
# Script de déploiement pour VM Web (Flask + Docker) sur ubuntu

set -e  # Arrêter en cas d'erreur

echo "Début du script de déploiement de l'application Flask avec Docker..."

# Variables de configuration
APP_DIR="/opt/web-app"
DOCKER_COMPOSE_FILE="docker-compose.yml"
DB_HOST="--------------------------------"
SECRET_KEY=$(openssl rand -base64 32)
DB_USER="--------------------------------"
DB_PASSWORD="--------------------------------"
DB_NAME="--------------------------------"
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


# Tester la connectivité vers la VM BDD
log_info "Test de connectivité vers la VM BDD..."
if ping -c 1 $DB_HOST > /dev/null 2>&1; then
    log_info "VM BDD accessible"
else
    log_warn "VM BDD non accessible via ping (peut être normal si firewall actif)"
fi


if ! command -v docker &> /dev/null; then
    log_info "Docker non trouvé, installation en cours..."

    # Installer les prérequis
    apt update -y
    apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

    # Ajouter la clé GPG de Docker (si non présente déjà)
    if [ ! -f /usr/share/keyrings/docker-archive-keyring.gpg ]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    fi

    # Ajouter le repository Docker (si absent)
    if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list
    fi

    # Installer Docker
    apt update -y
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    log_info "Docker installé avec succès"
else
    log_info "Docker déjà installé, passage à l'étape suivante"
fi

# Ajouter l'utilisateur au groupe docker
log_info "Configuration des permissions Docker..."
# sudo usermod -aG docker $USER pour rien car on utilise sudo ! 
sudo systemctl start docker
sudo systemctl enable docker

sudo chown -R $USER:$USER $APP_DIR

# Copier uniquement les fichiers Docker et docker-compose dans $APP_DIR
log_info "Copie des Dockerfiles et docker-compose.yml vers $APP_DIR..."

# Liste des fichiers à copier
FILES_TO_COPY=("Dockerfile" "docker-compose.yml")

for file in "${FILES_TO_COPY[@]}"; do
    if [ -f "$file" ]; then
        cp -f "$file" "$APP_DIR/"
        log_info "Copié $file"
    else
        log_warn " $file n'existe pas dans le répertoire courant, ignoré"
    fi
done

cd $APP_DIR


# Créer le fichier .env
log_info "Création du fichier de configuration..."
cat > .env << EOF
# Configuration générée automatiquement - NE PAS COMMITER
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:5432/$DB_NAME?sslmode=disable
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
EOF

# Construire et démarrer l'application
log_info "Construction de l'image Docker..."
sudo docker compose build

log_info "Démarrage de l'application..."
sudo docker compose up -d

# Attendre que l'application soit prête
log_info "Attente du démarrage de l'application..."
sleep 10

# Vérification de l'état
log_info "Vérification de l'état de l'application..."
sudo docker compose ps

# Test de connectivité
log_info "Test de connectivité..."
if curl -f http://localhost:5000/ > /dev/null 2>&1; then
    log_info "Application accessible sur http://localhost:5000"
else
    log_warn " Application non accessible sur le port 5000"
fi

if curl -f http://localhost/ > /dev/null 2>&1; then
    log_info "Application accessible sur http://localhost"
else
    log_warn "Application non accessible sur le port 80"
fi

# Configuration du firewall (Ubuntu UFW)
log_info "Configuration du firewall UFW..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 5000/tcp  # Flask (pour debug)
# Port 443 (HTTPS) commenté car pas de SSL pour le moment
# sudo ufw allow 443/tcp
sudo ufw --force enable
log_info "Firewall UFW configuré (SSH, HTTP, Flask debug)"

# Afficher les logs
log_info "Affichage des logs de l'application..."
echo ""
log_info "📋 Commandes utiles:"
echo "  - Voir les logs: sudo docker compose logs -f"
echo "  - Redémarrer: sudo docker compose restart"
echo "  - Arrêter: sudo docker compose down"
echo "  - Voir l'état: sudo docker compose ps"

echo ""
log_info "Déploiement terminé avec succès!"
log_info "Application accessible sur: http://$(hostname -I | awk '{print $1}')"
log_info "Application accessible sur: http://$(hostname -I | awk '{print $1}'):5000 (debug)"
log_info "Répertoire de l'application: $APP_DIR"


