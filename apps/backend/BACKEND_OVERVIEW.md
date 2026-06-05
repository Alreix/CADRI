# Vue d'ensemble du backend CADRI

Ce document présente le backend CADRI tel qu’il existe actuellement dans `apps/backend`. L’objectif est de donner une vision claire de la structure générale, du rôle de chaque fichier, des fonctions présentes et de la manière dont tout s’enchaîne. Le texte est volontairement rédigé dans un format simple à copier dans Google Docs.

## 1. Architecture générale

Le backend suit une architecture Flask découpée en couches.

- `app/__init__.py` contient la fabrique d’application et le bootstrap général.
- `app/config.py` centralise les configurations selon l’environnement.
- `app/extensions.py` regroupe les extensions Flask partagées.
- `app/models/` contient les objets métier persistés en base.
- `app/repositories/` contient les accès base de données.
- `app/services/` contient les règles métier.
- `app/facades/` sert de couche de passage entre routes et services.
- `app/routes/` contient la couche HTTP.
- `app/utils/` rassemble les outils transverses.
- `app/seeds/` gère les données de départ.
- `tests/` contient les tests unitaires, d’intégration et API.

Ce qui est déjà en place aujourd’hui:

- l’authentification;
- la gestion des utilisateurs;
- les rôles et services de référence;
- les tokens d’activation, de réinitialisation et de refresh;
- l’envoi d’e-mails;
- les validations et les helpers de sécurité;
- les seeds initiales;
- une vraie suite de tests.

Ce qui n’est pas encore implémenté:

- les missions;
- les assignations de mission;
- les liaisons mission-service;
- les vraies routes métier pour l’API missions;
- les endpoints REST complets, car les routes exposent pour le moment seulement des health checks.

## 2. Comment le backend fonctionne

Le chemin d’une requête ou d’un traitement suit généralement cette logique:

1. `run.py` démarre l’application Flask.
2. `app/__init__.py` crée l’application avec `create_app()`.
3. La configuration est chargée depuis `app/config.py`.
4. Les extensions sont initialisées.
5. Les blueprints sont enregistrés.
6. Une route HTTP reçoit la requête.
7. Cette route devra, à terme, appeler une façade.
8. La façade appelle un service.
9. Le service applique les règles métier et s’appuie sur les repositories et les modèles.
10. Le repository parle à la base de données via SQLAlchemy.

Aujourd’hui, cette chaîne est vraiment complète pour l’auth et les users côté logique interne, mais pas encore pour les futures routes métier finales.

## 3. Point d’entrée de l’application

### `app/__init__.py`

Rôle: création et initialisation de l’application Flask.

Fichiers liés:

- `app/config.py`
- `app/extensions.py`
- tous les fichiers de `app/routes/`

Fonctions:

- `create_app()`
  - Rôle: créer l’instance Flask prête à l’emploi.
  - Ce que ça fait: instancie Flask, charge la bonne configuration, initialise les extensions, puis enregistre les routes.
  - Prend: rien.
  - Renvoie: une application Flask configurée.
  - Pourquoi: cela permet d’avoir une seule façon de démarrer l’app selon l’environnement.

- `configure_extensions(app)`
  - Rôle: brancher les extensions Flask à l’application.
  - Ce que ça fait: initialise SQLAlchemy, Migrate, CORS, JWT et Bcrypt.
  - Prend: l’objet Flask.
  - Renvoie: rien.
  - Pourquoi: garder tout le bootstrap technique au même endroit.

- `configure_routes(app)`
  - Rôle: enregistrer les blueprints.
  - Ce que ça fait: monte les routes sous `/auth`, `/me`, `/users`, `/missions` et `/metadata`.
  - Prend: l’objet Flask.
  - Renvoie: rien.
  - Pourquoi: organiser la couche HTTP par domaine fonctionnel.

### `run.py`

Rôle: point de lancement du serveur.

Ce fichier crée l’application avec `create_app()` puis lance le serveur sur `0.0.0.0:5000` lorsqu’il est exécuté directement.

## 4. Configuration et extensions

### `app/config.py`

Rôle: gérer les paramètres de l’application selon l’environnement.

Fichiers liés:

- `app/__init__.py`
- `docker-compose.yml`
- `.env.example`

Classes:

- `BaseConfig`
  - Rôle: définir les paramètres communs à tous les environnements.
  - Ce que ça contient: clés secrètes, CORS frontend, e-mail, durées des JWT et des tokens, paramètres du cookie de refresh.
  - Pourquoi: éviter de dupliquer les mêmes valeurs partout.

- `DevelopmentConfig`
  - Rôle: config de développement local.
  - Ce que ça fait: active le debug et pointe SQLAlchemy vers PostgreSQL via `DATABASE_URL` ou la valeur Docker par défaut.
  - Pourquoi: le développement doit se rapprocher du comportement réel de l’application.

- `TestingConfig`
  - Rôle: config de test.
  - Ce que ça fait: active `TESTING = True` et utilise `TEST_DATABASE_URL`.
  - Pourquoi: isoler les tests de l’environnement de développement.

- `ProductionConfig`
  - Rôle: config de production.
  - Ce que ça fait: désactive le debug et utilise `DATABASE_URL`.
  - Pourquoi: la production doit rester stricte et explicite.

- `get_config()`
  - Rôle: choisir la bonne configuration.
  - Ce que ça fait: lit `FLASK_ENV` et renvoie la classe de config correspondante.
  - Prend: rien.
  - Renvoie: une classe de configuration.
  - Pourquoi: simplifier le démarrage de l’application dans plusieurs contextes.

### `app/extensions.py`

Rôle: déclarer les extensions Flask partagées.

Ce fichier regroupe les objets non initialisés suivants: base de données, migrations, CORS, JWT et Bcrypt.

Il ne contient pas de fonction métier, mais il est central car il relie la couche Flask à la couche persistence et sécurité.

## 5. Modèles métier

### `app/models/base_model.py`

Rôle: modèle de base commun à toutes les entités.

Fichiers liés:

- tous les modèles dans `app/models/`
- les repositories et services qui réutilisent les identifiants et les timestamps

Classe: `BaseModel`

- `save(self) -> None`
  - Rôle: enregistrer l’objet en base.
  - Ce que ça fait: ajoute l’objet à la session SQLAlchemy puis commit.
  - Prend: l’instance elle-même.
  - Renvoie: rien.
  - Pourquoi: standardiser la création d’un enregistrement.

- `update_timestamp(self) -> None`
  - Rôle: mettre à jour la date de modification.
  - Ce que ça fait: remplace `updated_at` par l’heure courante.
  - Prend: l’instance elle-même.
  - Renvoie: rien.
  - Pourquoi: garder une trace fiable des modifications.

- `to_dict(self) -> dict`
  - Rôle: sérialiser l’objet dans un format exploitable par l’API.
  - Ce que ça fait: transforme UUID et dates en valeurs JSON-friendly.
  - Prend: l’instance elle-même.
  - Renvoie: un dictionnaire.
  - Pourquoi: préparer facilement les réponses HTTP ou les logs.

### `app/models/role.py`

Rôle: représenter un rôle applicatif.

Fichiers liés:

- `app/repositories/role_repository.py`
- `app/seeds/seed_initial_data.py`
- `app/models/user.py`

Classe: `Role`

- Représente les profils métiers comme `admin`, `responsable` ou `agent`.
- Sert à contrôler les droits et les permissions.
- `__repr__(self) -> str` renvoie une représentation lisible pour le débogage.

### `app/models/service.py`

Rôle: représenter un service ou un pôle métier.

Fichiers liés:

- `app/repositories/service_repository.py`
- `app/seeds/seed_initial_data.py`
- `app/models/user.py`

Classe: `Service`

- Sert à rattacher un utilisateur à une structure métier.
- `__repr__(self) -> str` renvoie une représentation lisible pour le débogage.

### `app/models/user.py`

Rôle: représenter un compte utilisateur CADRI.

Fichiers liés:

- `app/utils/security.py`
- `app/services/auth_service.py`
- `app/services/user_service.py`
- `app/repositories/user_repository.py`

Classe: `User`

Ce modèle contient notamment: prénom, nom, e-mail, mot de passe hashé, rôle, service, statut actif et date d’activation.

Méthodes:

- `set_password(self, password: str) -> None`
  - Hache un mot de passe en clair et stocke le hash.
  - Prend: un mot de passe brut.
  - Renvoie: rien.
  - Pourquoi: un mot de passe ne doit jamais être stocké en clair.

- `check_password(self, password: str) -> bool`
  - Vérifie qu’un mot de passe correspond au hash stocké.
  - Prend: un mot de passe brut.
  - Renvoie: un booléen.
  - Pourquoi: utile pour l’authentification et les changements de mot de passe.

- `activate_account(self) -> None`
  - Active le compte et enregistre la date d’activation.
  - Prend: l’instance elle-même.
  - Renvoie: rien.
  - Pourquoi: l’activation est un acte métier à part entière.

- `update_profile(self, first_name: str | None = None, last_name: str | None = None, email: str | None = None) -> None`
  - Met à jour les informations modifiables du profil.
  - Prend: des champs optionnels.
  - Renvoie: rien.
  - Pourquoi: permettre une modification partielle du profil.

- `__repr__(self) -> str`
  - Retourne une chaîne utile pour les logs et le débogage.

### `app/models/account_activation_token.py`

Rôle: gérer les jetons d’activation de compte.

Fichiers liés:

- `app/repositories/account_activation_token_repository.py`
- `app/services/auth_service.py`
- `app/utils/tokens.py`

Classe: `AccountActivationToken`

- `create_for_user(cls, user_id: int, expires_in_hours: int = 24)`
  - Crée un jeton stocké en base et renvoie aussi le jeton brut à envoyer par e-mail.
  - Prend: un identifiant utilisateur et une durée d’expiration.
  - Renvoie: le modèle de jeton et la version brute.
  - Pourquoi: on stocke le hash, mais l’utilisateur reçoit le token brut dans le lien.

- `is_expired(self) -> bool`
  - Vérifie si le jeton est expiré.
  - Pourquoi: un lien d’activation ne doit pas rester valide indéfiniment.

- `is_used(self) -> bool`
  - Vérifie si le jeton a déjà servi.
  - Pourquoi: le lien doit être à usage unique.

- `verify_token(self, raw_token: str) -> bool`
  - Compare le jeton brut fourni avec le hash stocké.
  - Prend: un jeton brut.
  - Renvoie: un booléen.
  - Pourquoi: valider que le lien reçu correspond bien au jeton attendu.

- `mark_as_used(self) -> None`
  - Marque le jeton comme consommé.
  - Pourquoi: empêcher sa réutilisation.

- `__repr__(self) -> str`
  - Retourne une représentation lisible pour le débogage.

### `app/models/password_reset_token.py`

Rôle: gérer les jetons de réinitialisation de mot de passe.

Fichiers liés:

- `app/repositories/password_reset_token_repository.py`
- `app/services/auth_service.py`
- `app/utils/tokens.py`

Classe: `PasswordResetToken`

- `create_for_user(cls, user_id: int, expires_in_hours: int = 2) -> tuple["PasswordResetToken", str]`
  - Crée le jeton en base et renvoie le jeton brut.
  - Prend: un identifiant utilisateur et une durée d’expiration.
  - Renvoie: le modèle et le token brut.
  - Pourquoi: le lien envoyé par e-mail doit correspondre au jeton stocké.

- `is_expired(self) -> bool`
  - Vérifie si le jeton est encore valable.

- `is_used(self) -> bool`
  - Vérifie si le jeton a déjà été consommé.

- `verify_token(self, raw_token: str) -> bool`
  - Compare le jeton brut à son hash.

- `mark_as_used(self) -> None`
  - Passe le jeton en état utilisé.

- `__repr__(self) -> str`
  - Retourne une chaîne lisible pour le débogage.

### `app/models/refresh_token.py`

Rôle: gérer les jetons de session longue durée.

Fichiers liés:

- `app/repositories/refresh_token_repository.py`
- `app/services/auth_service.py`
- `app/utils/tokens.py`

Classe: `RefreshToken`

- `create_for_user(cls, user_id: int, expires_in_days: int = 7) -> tuple["RefreshToken", str]`
  - Crée un token persistant et renvoie aussi la valeur brute pour le client.
  - Prend: un identifiant utilisateur et une durée de validité.
  - Renvoie: le modèle et le token brut.
  - Pourquoi: permettre le renouvellement de session sans retaper le mot de passe.

- `is_expired(self) -> bool`
  - Vérifie si le token a expiré.

- `is_revoked(self) -> bool`
  - Vérifie si le token a été révoqué.

- `is_replaced(self) -> bool`
  - Vérifie si le token a été remplacé lors d’une rotation.

- `is_valid(self) -> bool`
  - Vérifie si le token est encore utilisable.

- `verify_token(self, raw_token: str) -> bool`
  - Compare le token reçu avec le hash stocké.

- `revoke(self) -> None`
  - Révoque le token.
  - Pourquoi: indispensable pour le logout.

- `rotate(self, new_raw_token: str) -> None`
  - Remplace l’ancien token par un nouveau hash et marque l’ancien comme remplacé.
  - Pourquoi: réduire le risque de réutilisation d’un token intercepté.

- `__repr__(self) -> str`
  - Retourne une forme lisible pour le débogage.

### Fichiers de mission encore vides

- `app/models/mission.py`
- `app/models/mission_assignment.py`
- `app/models/mission_service_link.py`

Ces fichiers sont réservés pour le futur domaine mission. Ils ne contiennent pas encore de logique métier exploitable.

## 6. Accès base de données

Les repositories sont la couche qui parle directement à SQLAlchemy. Ils évitent de disperser les requêtes dans les services.

### `app/repositories/user_repository.py`

Rôle: accès aux utilisateurs.

Classe: `UserRepository`

- `get_all()`
  - Retourne tous les utilisateurs, triés du plus récent au plus ancien.
  - Utilisation: listes d’administration.

- `get_by_id(user_id)`
  - Retourne un utilisateur par identifiant, ou `None`.
  - Utilisation: détails, authentification, modifications.

- `get_by_email(email)`
  - Retourne un utilisateur par e-mail, ou `None`.
  - Utilisation: connexion et contrôle d’unicité.

- `create(user)`
  - Enregistre un nouvel utilisateur.
  - Utilisation: création de compte.

- `update()`
  - Valide les modifications en attente.
  - Utilisation: après modification d’un utilisateur.

- `delete(user)`
  - Supprime un utilisateur.
  - Utilisation: suppression de compte.

### `app/repositories/role_repository.py`

Rôle: accès aux rôles.

Méthodes:

- `get_all()` : liste tous les rôles.
- `get_by_id(role_id)` : récupère un rôle par identifiant.
- `get_by_name(name)` : récupère un rôle par nom technique.

### `app/repositories/service_repository.py`

Rôle: accès aux services.

Méthodes:

- `get_all()` : liste tous les services.
- `get_by_id(service_id)` : récupère un service par identifiant.
- `get_by_name(name)` : récupère un service par nom technique.

### `app/repositories/refresh_token_repository.py`

Rôle: accès aux refresh tokens.

Méthodes:

- `get_by_id(token_id)`
- `get_by_token_hash(token_hash)`
- `get_latest_for_user(user_id)`
- `revoke_all_for_user(user_id)`
- `create(token)`
- `update()`

Ces méthodes servent aux flows de login, logout et renouvellement de session.

### `app/repositories/password_reset_token_repository.py`

Rôle: accès aux tokens de réinitialisation.

Méthodes:

- `get_by_id(token_id)`
- `get_by_token_hash(token_hash)`
- `get_latest_for_user(user_id)`
- `invalidate_unused_tokens_for_user(user_id)`
- `create(token)`
- `update()`

### `app/repositories/account_activation_token_repository.py`

Rôle: accès aux tokens d’activation.

Méthodes:

- `get_by_id(token_id)`
- `get_by_token_hash(token_hash)`
- `get_latest_for_user(user_id)`
- `invalidate_unused_tokens_for_user(user_id)`
- `create(token)`
- `update()`

### Fichiers repository de mission encore vides

- `app/repositories/mission_repository.py`
- `app/repositories/mission_assignment_repository.py`
- `app/repositories/mission_service_link_repository.py`

Ils sont prévus pour la future persistance des missions.

## 7. Couche métier

### `app/services/auth_service.py`

Rôle: concentrer toute la logique d’authentification et de gestion des tokens.

Fichiers liés:

- modèles token et utilisateur
- repositories associés
- `app/services/email_service.py`
- `app/utils/exceptions.py`
- `app/utils/validators.py`

Classe: `AuthService`

- `login(email, password)`
  - Vérifie les identifiants, contrôle le compte, crée les tokens et renvoie une session.
  - Pourquoi: c’est le cœur de la connexion utilisateur.

- `logout(raw_refresh_token)`
  - Révoque le refresh token fourni.
  - Pourquoi: déconnecter proprement le client.

- `refresh_session(raw_refresh_token)`
  - Vérifie le refresh token, le fait tourner si nécessaire et renvoie une nouvelle session.
  - Pourquoi: prolonger l’accès sans demander à l’utilisateur de se reconnecter.

- `activate_account(raw_token, password)`
  - Valide le jeton, active le compte, pose le mot de passe et consomme le jeton.
  - Pourquoi: finaliser l’inscription d’un compte inactif.

- `request_password_reset(email)`
  - Crée un jeton de reset et déclenche l’e-mail correspondant.
  - Pourquoi: lancer le flux de récupération de mot de passe.

- `reset_password(raw_token, password)`
  - Vérifie le jeton, met à jour le mot de passe et marque le jeton comme utilisé.
  - Pourquoi: terminer le reset de manière sécurisée.

- `change_password(user_id, current_password, new_password)`
  - Vérifie le mot de passe actuel, applique le nouveau mot de passe.
  - Pourquoi: permettre à l’utilisateur de gérer son mot de passe lui-même.

- `send_activation_email_for_user(user)`
  - Génère un jeton d’activation et envoie l’e-mail.
  - Pourquoi: garder ensemble la génération du jeton et son envoi.

### `app/services/user_service.py`

Rôle: gérer la création, la modification et la consultation des utilisateurs avec les règles métier.

Fichiers liés:

- `app/models/user.py`
- `app/repositories/user_repository.py`
- `app/repositories/role_repository.py`
- `app/repositories/service_repository.py`
- `app/utils/exceptions.py`
- `app/utils/validators.py`
- `app/services/auth_service.py`

Classe: `UserService`

- `_validate_name(value, field_name)`
  - Valide un prénom ou un nom.
  - Pourquoi: éviter les champs vides ou incohérents.

- `_get_role_or_fail(role_name)`
  - Cherche un rôle ou lève une erreur si absent.
  - Pourquoi: une création utilisateur doit s’appuyer sur un rôle valide.

- `_get_service_or_fail(service_id)`
  - Cherche un service ou lève une erreur si absent.
  - Pourquoi: un utilisateur doit être rattaché à un service existant.

- `_check_user_creation_permissions(current_user, target_role_name)`
  - Vérifie si le créateur a le droit de créer ce type de compte.
  - Pourquoi: sécuriser la création d’utilisateurs.

- `_check_user_update_permissions(current_user)`
  - Vérifie si l’utilisateur courant peut modifier d’autres comptes.
  - Pourquoi: protéger les opérations sensibles.

- `_check_user_delete_permissions(current_user)`
  - Vérifie si l’utilisateur courant peut supprimer un compte.
  - Pourquoi: empêcher les suppressions non autorisées.

- `create_user(current_user, first_name, last_name, email, role_name, service_id)`
  - Crée un nouvel utilisateur en appliquant les validations et permissions.
  - Pourquoi: centraliser le flux de création de compte.

- `list_users()`
  - Renvoie la liste des utilisateurs.
  - Pourquoi: alimenter les vues d’administration.

- `get_user_details(user_id)`
  - Renvoie le détail d’un utilisateur.
  - Pourquoi: afficher une fiche utilisateur.

- `update_user(current_user, user_id, first_name, last_name, email, role_name, service_id)`
  - Met à jour un utilisateur avec contrôle d’accès.
  - Pourquoi: permettre l’administration des comptes.

- `delete_user(current_user, user_id)`
  - Supprime un utilisateur après contrôle d’accès.
  - Pourquoi: gérer les suppressions administratives.

- `list_assignable_users()`
  - Retourne les utilisateurs assignables à des missions.
  - Pourquoi: c’est une base utile pour le futur module mission.

- `update_own_profile(current_user, first_name, last_name, email)`
  - Permet à l’utilisateur de modifier son propre profil.
  - Pourquoi: fonctionnalité self-service.

### `app/services/email_service.py`

Rôle: construire et envoyer les e-mails métier.

Fichiers liés:

- `app/utils/constants.py`
- `app/utils/tokens.py`
- `app/models/account_activation_token.py`
- `app/models/password_reset_token.py`

Classe: `EmailService`

- `build_activation_link(raw_token: str) -> str`
  - Construit le lien d’activation côté frontend.
  - Pourquoi: le mail doit contenir une URL cliquable.

- `build_reset_link(raw_token: str) -> str`
  - Construit le lien de réinitialisation de mot de passe.
  - Pourquoi: orienter l’utilisateur vers la bonne page.

- `send_email(to_email: str, subject: str, body: str) -> None`
  - Envoie un e-mail simple via le serveur configuré.
  - Pourquoi: méthode de base pour tous les mails sortants.

- `send_activation_email(cls, user_email: str, raw_token: str) -> None`
  - Prépare et envoie l’e-mail d’activation.
  - Pourquoi: encapsuler le modèle de message d’activation.

- `send_password_reset_email(cls, user_email: str, raw_token: str) -> None`
  - Prépare et envoie l’e-mail de réinitialisation.
  - Pourquoi: encapsuler le modèle de message de reset.

### `app/services/metadata_service.py`

Rôle: couche réservée aux futures métadonnées métier.

### `app/services/mission_service.py`

Rôle: couche réservée aux futures règles métier liées aux missions.

## 8. Façades

Les façades sont aujourd’hui très fines. Elles ne portent pas encore de logique complexe; elles servent surtout de couche d’interface entre HTTP et services.

### `app/facades/auth_facade.py`

Rôle: relayer les appels vers `AuthService`.

Méthodes:

- `login(email, password)`
- `logout(raw_refresh_token)`
- `refresh_session(raw_refresh_token)`
- `activate_account(raw_token, password)`
- `request_password_reset(email)`
- `reset_password(raw_token, password)`
- `change_password(user_id, current_password, new_password)`
- `send_activation_email_for_user(user)`

Chaque méthode appelle directement la méthode correspondante du service.

### `app/facades/user_facade.py`

Rôle: relayer les appels vers `UserService`.

Méthodes:

- `create_user(current_user, first_name, last_name, email, role_name, service_id)`
- `list_users()`
- `get_user_details(user_id)`
- `update_user(current_user, user_id, first_name, last_name, email, role_name, service_id)`
- `delete_user(current_user, user_id)`
- `list_assignable_users()`
- `update_own_profile(current_user, first_name, last_name, email)`

### `app/facades/metadata_facade.py`

Rôle: emplacement réservé pour le futur module metadata.

### `app/facades/mission_facade.py`

Rôle: emplacement réservé pour le futur module missions.

## 9. Routes HTTP

Les routes existent déjà, mais elles ne contiennent pour l’instant que des health checks. Cela montre que les blueprints sont correctement branchés sans exposer encore l’API métier finale.

### `app/routes/auth_routes.py`

- `auth_bp = Blueprint("auth", __name__)`
  - Blueprint de l’authentification.
  - Il sera le point d’entrée de toutes les routes `/auth`.

- `auth_health()`
  - Renvoie un simple message JSON de vérification.
  - Sert à confirmer que le blueprint est bien chargé.

### `app/routes/user_routes.py`

- `users_bp = Blueprint("users", __name__)`
  - Blueprint des routes utilisateurs.

- `users_health()`
  - Health check simple.

### `app/routes/me_routes.py`

- `me_bp = Blueprint("me", __name__)`
  - Blueprint du profil courant.

- `me_health()`
  - Health check simple.

### `app/routes/metadata_routes.py`

- `metadata_bp = Blueprint("metadata", __name__)`
  - Blueprint des métadonnées.

- `metadata_health()`
  - Health check simple.

### `app/routes/mission_routes.py`

- `missions_bp = Blueprint("missions", __name__)`
  - Blueprint des missions.

- `missions_health()`
  - Health check simple.

### Ce qui existera plus tard côté API

Les routes finales devraient exposer des endpoints métier sous ces préfixes:

- `/auth` pour login, logout, refresh, activation et reset de mot de passe;
- `/users` pour la gestion des comptes;
- `/me` pour le profil de l’utilisateur connecté;
- `/metadata` pour les données de référence comme rôles et services;
- `/missions` pour les opérations liées aux missions.

Aujourd’hui, ces endpoints métier ne sont pas encore écrits.

## 10. Utilitaires

### `app/utils/exceptions.py`

Rôle: définir les erreurs métier de l’application.

Classe `AppError`

- classe de base pour les erreurs applicatives;
- contient un message et un code HTTP;
- `__init__(message, status_code=None)` initialise le message et éventuellement le code;
- `to_dict()` renvoie une structure JSON simple.

Classes filles:

- `ValidationError`: erreur 400 pour les données invalides;
- `AuthenticationError`: erreur 401 pour les problèmes d’authentification;
- `AuthorizationError`: erreur 403 pour les droits insuffisants;
- `NotFoundError`: erreur 404 pour les ressources absentes;
- `ConflictError`: erreur 409 pour les conflits de données;
- `GoneError`: erreur 410 pour les ressources consommées ou invalidées.

### `app/utils/security.py`

Rôle: fonctions de sécurité autour des mots de passe.

- `hash_password(password: str) -> str`
  - Hache un mot de passe avec bcrypt.
  - Pourquoi: protéger les identifiants utilisateurs.

- `check_password(password: str, password_hash: str) -> bool`
  - Vérifie un mot de passe brut contre un hash bcrypt.
  - Pourquoi: valider une tentative de connexion ou un changement de mot de passe.

### `app/utils/tokens.py`

Rôle: génération et hachage des jetons.

- `generate_raw_token(length: int = 32) -> str`
  - Génère une chaîne aléatoire sûre pour les liens sensibles.
  - Pourquoi: activation, reset et refresh utilisent des jetons opaques.

- `hash_token(raw_token: str) -> str`
  - Hache un jeton avant stockage.
  - Pourquoi: la base ne doit pas conserver les jetons bruts.

### `app/utils/validators.py`

Rôle: validation des entrées utilisateur.

- `validate_email(email)`
  - Normalise et valide une adresse e-mail.
  - Pourquoi: garder un format cohérent pour la connexion et les comptes.

- `validate_password(password)`
  - Vérifie la politique de mot de passe.
  - Pourquoi: imposer une base de sécurité minimale.

### `app/utils/constants.py`

Rôle: emplacement prévu pour les constantes partagées.

### `app/utils/decorators.py`

Rôle: emplacement prévu pour les décorateurs communs.

## 11. Seeds

### `app/seeds/seed_initial_data.py`

Rôle: créer les données de référence de départ.

Fichiers liés:

- `app/models/role.py`
- `app/models/service.py`
- `app/repositories/role_repository.py`
- `app/repositories/service_repository.py`

Fonctions:

- `seed_roles()`
  - Crée les rôles par défaut s’ils n’existent pas.
  - Pourquoi: le backend a besoin d’une base d’autorisations connue.

- `seed_services()`
  - Crée les services par défaut s’ils n’existent pas.
  - Pourquoi: les utilisateurs doivent être rattachés à des services existants.

- `run_seed()`
  - Lance l’ensemble du seed.
  - Pourquoi: fournir un seul point d’entrée pour l’initialisation.

## 12. Tests

Les tests sont divisés en trois couches: unitaires, intégration et API.

### `tests/conftest.py`

Rôle: fournir les fixtures communes.

Fixtures:

- `app`: crée une application Flask propre pour chaque test et pointe vers PostgreSQL local exposé par Docker sur `127.0.0.1:5432`.
- `client`: fournit un client de test Flask.
- `reference_data`: crée les rôles et services de base.
- `user_factory`: fabrique des utilisateurs de test cohérents.
- `admin_user`: crée un utilisateur admin réutilisable.
- `responsable_user`: crée un responsable réutilisable.
- `agent_user`: crée un agent réutilisable.
- `access_token_factory`: fabrique des JWT réels.
- `auth_headers_factory`: construit les headers `Authorization`.

### Tests unitaires

#### `tests/unit/test_security.py`

- `test_hash_password_generates_verifiable_hash(app)`
  - Vérifie que le hachage produit une chaîne différente du mot de passe brut et que la vérification fonctionne.

#### `tests/unit/test_tokens_utils.py`

- `test_generate_raw_token_returns_url_safe_strings()`
- `test_generate_raw_token_respects_length_argument()`
- `test_hash_token_is_deterministic_and_hex_encoded()`

Ces tests valident la génération et le hachage des jetons.

#### `tests/unit/test_validators.py`

- `test_validate_email_normalizes_and_returns_lowercase()`
- `test_validate_email_rejects_invalid_values(invalid_email)`
- `test_validate_password_rejects_policy_violations(password, expected_message)`
- `test_validate_password_returns_original_password_when_valid()`

Ces tests vérifient les règles de validation des données.

#### `tests/unit/test_models_unit.py`

- `test_user_password_and_profile_helpers(app)`
- `test_base_model_to_dict_serializes_uuid_and_datetimes()`
- `test_account_activation_token_lifecycle_in_memory()`
- `test_password_reset_token_lifecycle_in_memory()`
- `test_refresh_token_rotation_marks_token_invalid()`

Ces tests vérifient les helpers des modèles et les cycles de vie des jetons.

### Tests d’intégration

#### `tests/integration/test_repositories.py`

- `test_role_repository_lists_reference_roles(reference_data)`
- `test_service_repository_lists_reference_services(reference_data)`
- `test_user_repository_crud(reference_data)`
- `test_account_activation_token_repository_workflow(user_factory)`
- `test_password_reset_token_repository_workflow(user_factory)`
- `test_refresh_token_repository_workflow(user_factory)`

Ces tests vérifient le comportement réel des repositories avec la base de données.

#### `tests/integration/test_seed_initial_data.py`

- `test_run_seed_creates_default_roles_and_services(app)`
- `test_run_seed_is_idempotent(app)`

Ces tests vérifient que les seeds créent bien les données de base sans doublons.

#### `tests/integration/test_auth_service.py`

- `test_login_returns_session_payload_and_creates_refresh_token(admin_user)`
- `test_login_rejects_invalid_password(admin_user)`
- `test_logout_revokes_refresh_token(admin_user)`
- `test_change_password_updates_user_password(agent_user)`
- `test_request_password_reset_creates_token_and_sends_email(agent_user)`
- `test_refresh_session_rotates_refresh_token(admin_user)`
- `test_activate_account_marks_user_active_and_consumes_token(user_factory)`
- `test_reset_password_marks_token_used_and_updates_password(user_factory)`

Ces tests couvrent les principaux scénarios d’authentification de bout en bout.

### Tests API

#### `tests/api/test_auth_routes.py`

- `test_auth_health_route(client)`

#### `tests/api/test_users_routes.py`

- `test_users_health_route(client)`

#### `tests/api/test_metadata_routes.py`

- `test_metadata_health_route(client)`

Ces tests vérifient que les blueprints sont bien enregistrés et que la couche HTTP répond.

### Fichiers de tests encore vides ou legacy

- `tests/test_auth.py`
- `tests/test_metadata.py`
- `tests/test_missions.py`
- `tests/test_missions.py`

## 13. Ce qui existe déjà et ce qui reste à faire

### Déjà présent

- le socle Flask;
- l’authentification;
- les utilisateurs;
- les rôles et services de référence;
- les jetons de session et d’activation;
- l’e-mail;
- les validations;
- les seeds;
- les tests.

### Réservé pour plus tard

- les modèles de mission;
- les repositories mission;
- les services mission;
- les façades mission;
- les vraies routes HTTP de mission.

### API future attendue

Les préfixes déjà en place annoncent la structure finale de l’API:

- `/auth` pour l’authentification et la gestion de session;
- `/users` pour l’administration des comptes;
- `/me` pour le profil de l’utilisateur connecté;
- `/metadata` pour les données de référence;
- `/missions` pour tout le cycle de vie des missions.

Pour l’instant, ces routes ne font encore que répondre à des health checks.

## 14. Ordre de lecture conseillé

Si tu veux comprendre le backend rapidement, l’ordre le plus utile est:

1. `app/__init__.py`
2. `app/config.py`
3. `app/models/base_model.py`
4. `app/models/user.py`
5. `app/services/auth_service.py`
6. `app/services/user_service.py`
7. `app/repositories/user_repository.py`
8. `app/routes/auth_routes.py`
9. `app/routes/user_routes.py`
10. `tests/conftest.py`

Cette lecture permet de suivre le chemin complet: démarrage, configuration, modèle, logique métier, persistence, puis tests.
