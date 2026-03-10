# API
API for my apps
Ceci est une API REST FLASK pour une application permettant l'évaluation et l'aide aux prises de décisions
(avec authentification)

Démarrage (WINDOWS):
-Aller dans le dossier de l'API
-ouvrir cmd
-créer l’environnement virtuel : 
	python -m venv venv
-activer l'environnement virtuel : 
	venv\Scripts\activate
-Installer les dépendances Python : 
	pip install -r requirements.txt
-Configurer la base de données (changer port, mot de passe, nom database) dans le fichier .env du backend
-L'ADMIN GLOBAL: déjà configuré dans le back : email = "admin@processflow.com" et password = "Admin12345"
-Lancer le serveur Flask : 
	python app.py
