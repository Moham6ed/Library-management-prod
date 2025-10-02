FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY flask_app/ ./flask_app/
COPY init_db.py .

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Variables d'environnement
ENV FLASK_APP=flask_app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Exposer le port
EXPOSE 5000

# Commande de démarrage
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
