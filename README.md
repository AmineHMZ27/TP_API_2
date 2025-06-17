🗄️ Transaction Data Lake – API REST

Cette application Django met à disposition une API REST protégée qui dialogue avec un data lake local stockant les journaux de transactions. Elle offre des outils pour consulter, filtrer, auditer et republier les données dans Kafka.

⚡ Points forts

🔑 JWT pour l’authentification
🛂 Gestion fine des permissions (utilisateur ↔ ressource)
🔎 Filtrage, projection et pagination des résultats
📈 Indicateurs analytics (montants globaux, produits les plus achetés, etc.)
📝 Traçabilité complète des accès (audit log)
🔄 Republier une ou l’ensemble des transactions sur Kafka
🤖 Lancement d’un entraînement de modèle ML
📚 Interface Swagger intégrée pour la doc et les tests
🧑‍💻 Lancement en environnement local

Installer les dépendances
pip install -r requirements.txt
Exécuter les migrations
python manage.py migrate
Démarrer le serveur de développement
python manage.py runserver
Créer un compte administrateur
python manage.py createsuperuser
🔐 Obtenir un jeton JWT

Faites un POST sur /api/token/ avec vos username et password.
Le jeton access retourné s’utilise :

Authorization: Bearer <access_token>
(pensez à cliquer sur “Authorize” dans Swagger pour le tester).

🛣️ Routes essentielles

Endpoint	Rôle
/api/token/	Générer un token JWT
/api/access/grant/	Donner un droit d’accès
/api/access/revoke/	Retirer un droit
/api/data/	Lister les transactions (filtre, projection, pagination)
/api/metrics/last5min/	Dépenses cumulées sur les 5 dernières minutes
/api/metrics/total_by_user/	Totaux par utilisateur et par type
/api/metrics/top_products/	Produits les plus achetés
/api/search/	Recherche plein-texte
/api/repush/transaction/	Republier une transaction
/api/repush/all/	Republier tout l’historique
/api/audit/	Journal des accès
/api/train/	Entraîner le modèle ML
/api/repush/check/	Vérifier qu’une transaction republiée est bien stockée
📖 Swagger

La documentation interactive est disponible à : http://localhost:8000/swagger/

👤 Auteur·rice

Projet développé pour le TP API 2 du Master Data Engineering.