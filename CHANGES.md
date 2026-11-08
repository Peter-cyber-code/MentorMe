# MentorMe backend : correctifs

## Appliquer
1. Dézipper **par-dessus** votre projet (les chemins sont ceux du projet) ; supprimer ensuite `db.sqlite3`, `__pycache__` du dépôt (`.gitignore` fourni).
2. `pip install -r requirements.txt`
3. Copier `.env.example` en `.env` et l'adapter. **Générer une nouvelle `DJANGO_SECRET_KEY`** : l'ancienne était dans le code et doit être considérée comme compromise.
4. (Recommandé) `docker compose up -d`, puis `DATABASE_URL` / `REDIS_URL` du `.env.example`.
5. `python manage.py migrate` : seed des rôles, reprise de `user_type`/`hourly_price` vers le profil, table de blacklist JWT. Testé sur une copie de votre base actuelle.
6. Tests : `DJANGO_DEBUG=1 python manage.py test` (24 tests).

## Corrigé
**Rôles et réservation**
- Un seul système de rôles : `Profile.roles` (`profiles/roles.py`). `CustomUser.user_type` n'est plus utilisé (champ conservé, migré).
- Rôles sensibles (mentor, investisseur, experts) : refusés tant que le profil n'est pas vérifié. Inscription : `project_owner` ou `collaborator` seulement.
- Prix de réservation = `Profile.session_price` (ne valait toujours 0 avant).
- Nouveaux endpoints `complete` et `reject`. Annulation limitée à `PENDING`/`CONFIRMED`. Créneaux : pas de passé, pas de chevauchement. Un tiers reçoit 404.
- Avis : plus de `AttributeError`, statut `COMPLETED` corrigé, note moyenne recalculée automatiquement, modification d'avis possible.

**Sécurité / production**
- Configuration par variables d'environnement ; démarrage refusé sans `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL` (hors `DJANGO_DEBUG=1`).
- PostgreSQL + Redis ; CORS ; HTTPS, HSTS, cookies sécurisés hors DEBUG ; JSON seul hors DEBUG.
- JWT : access 15 min (7 jours avant), refresh avec rotation + blacklist, endpoint `logout`.
- Limites de débit : login/inscription 10/min, audit IA 5/heure, global 60/min anonyme et 300/min connecté.
- Mots de passe : validation Django (10 caractères minimum) à l'inscription.
- Audit : plus de message d'erreur interne renvoyé au client ; contenu du projet encadré dans le prompt (anti-injection).

**Temps réel et notifications**
- WebSocket authentifié par JWT : `?token=<access>` (la session cookie ne fonctionnait pas avec Flutter).
- Messages REST diffusés sur le WebSocket.
- Notifications créées automatiquement (message, réservation créée/confirmée/refusée/terminée/annulée, avis).

**IA**
- `AUDIT_PROVIDER=mock|openai` ; client OpenAI créé à la demande, résultat converti en dict, schémas dédupliqués.
- **Nouveau** `GET /api/audits/<id>/recommendations/` : l'audit déclenche les recommandations (mentors, experts, investisseurs, collaborateurs) à partir de profils réels, avec score et explication.

## Pas encore fait (à prévoir)
- **Paiements** (Stripe / Mobile Money) : aucun modèle ni endpoint. Les prix sont calculés mais pas encaissés.
- **Celery** : l'audit reste synchrone dans la requête (acceptable avec le mock, à passer en tâche asynchrone avec OpenAI).
- **Programmes de financement** : pas de modèle (`funding_programs` renvoie `[]`).
- **Workflow de vérification** des experts : pour l'instant, un admin coche `is_verified` et attribue les rôles dans l'admin Django.
- **Pièces jointes de messages** : toujours servies publiquement via `/media/` ; prévoir un téléchargement authentifié ou des URL signées avant la production.
- Le mode `openai` n'a pas pu être testé avec une vraie clé (seulement le mode mock) ; PostgreSQL non testé en conditions réelles (config vérifiée, tests sur SQLite).
- Une réservation n'est pas liée à un paiement, ni à un lien de visioconférence.
