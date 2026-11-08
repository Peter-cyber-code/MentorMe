# MentorMe : guide API pour Flutter

Base : `https://<hote>/api/` · JSON · listes paginées `{count, next, previous, results}`.
Header : `Authorization: Bearer <access>`.

## Authentification
| Action | Requête |
|---|---|
| Inscription | `POST /accounts/register/` `{username, email, first_name, last_name, password, password_confirm, role}` ; `role` = `project_owner` (défaut) ou `collaborator` |
| Connexion | `POST /accounts/login/` `{email, password}` → `{access, refresh}` (**par e-mail**, pas par username) |
| Refresh | `POST /accounts/token/refresh/` `{refresh}` → `{access, refresh}` : **stocker le nouveau refresh** (rotation, l'ancien est révoqué) |
| Déconnexion | `POST /accounts/logout/` `{refresh}` |
| Moi | `GET /accounts/me/` → `{id, username, roles: [...], rating, ...}` |

`access` vit 15 min : à rafraîchir sur 401 (un seul refresh à la fois côté Dio). Login et inscription : 10 requêtes/min max (429 au-delà).

## Rôles
- `GET /profiles/roles/` liste les rôles (id + code) ; `PATCH /profiles/me/` `{role_ids: [...]}`.
- `project_owner` et `collaborator` : libres.
- `mentor`, `investor`, `financial_expert`, `marketing_expert`, `legal_expert` : réservés aux profils **vérifiés** (`is_verified`, attribué par un admin). Sinon 400.
- Les objets profil exposent `user_id` : à utiliser pour réserver, écrire, suivre, noter.

## Réservation
1. Prestataire : `POST /booking/availability/` `{date, start_time, end_time}` (pas de passé, pas de chevauchement).
2. Client : `GET /booking/providers/<user_id>/availability/` (créneaux libres futurs) puis `POST /booking/book/<availability_id>/` `{message}` → réservation `PENDING`, prix = tarif du profil. 409 si créneau pris.
3. Prestataire : `POST /booking/<id>/confirm/` ou `/reject/` (depuis `PENDING`).
4. Prestataire : `POST /booking/<id>/complete/` (depuis `CONFIRMED`, après le début du créneau).
5. Client ou prestataire : `POST /booking/<id>/cancel/` (depuis `PENDING` ou `CONFIRMED`).
6. Listes : `GET /booking/mine/` (client), `GET /booking/received/` (prestataire).

Statuts : `PENDING → CONFIRMED → COMPLETED` ; `CANCELLED` ; `REJECTED`. **Paiement : pas encore implémenté.**

## Avis
- `POST /reviews/` `{booking, rating (1-5), comment}` : uniquement le client, réservation `COMPLETED`, un avis par réservation.
- `GET /reviews/professionals/<user_id>/` · `.../rating/` · `GET /reviews/mine/` · `PATCH|DELETE /reviews/<id>/`.
- La note moyenne est mise à jour automatiquement (`rating` dans `/accounts/me/`).

## Audit IA et recommandations
- `POST /audits/` `{project, problem, solution, target_customers, business_model, competitors?, team?, funding_need?}` → audit avec `report` (réponse synchrone, quelques secondes en mode `openai`). 429 au-delà de 5/heure.
- `GET /audits/<id>/` · `GET /audits/mine/` · `GET /audits/projects/<project_id>/`.
- `GET /audits/<id>/recommendations/` → `{priority_actions, recommendations: {mentor: [{score, score_breakdown, reason, profile}], financial_expert: [...], ...}, funding_programs: []}`. 409 si l'audit n'est pas terminé.

## Messagerie
- `GET /messaging/conversations/` · `POST /messaging/conversations/private/` `{user_id}`
- `GET /messaging/conversations/<id>/messages/` · `POST .../messages/send/` (JSON ou multipart `attachments`)
- `POST /messaging/conversations/<id>/read/`
- **Temps réel** : `wss://<hote>/ws/messaging/<conversation_id>/?token=<access>`
  - envoyer `{"content": "texte"}` ; recevoir `{id, content, sender, created_at}`
  - connexion refusée si token invalide/expiré ou non-participant : se reconnecter avec un access frais.
  - les messages envoyés en REST sont aussi diffusés sur ce canal.

## Notifications
`GET /notifications/` · `GET /notifications/unread-count/` · `POST /notifications/<id>/read/` · `POST /notifications/read-all/`
Types : `message`, `booking_created`, `booking_confirmed`, `booking_rejected`, `booking_completed`, `booking_cancelled`, `review`. Elles sont créées automatiquement par les actions ci-dessus. (Pas encore de push FCM : prévoir un polling ou le WebSocket.)

## Autres
Projets `/projects/`, posts `/posts/…`, follows `/follows/…`, matching `/matching/…` : inchangés.
Erreurs : `{"detail": "..."}` ou `{champ: ["message"]}` en 400 ; messages en français.
