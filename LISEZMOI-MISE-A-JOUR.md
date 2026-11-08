# Backend MentorMe : mise à jour complète (cumulative)

Ce zip contient TOUS les fichiers modifiés ou ajoutés depuis votre envoi initial
(correctifs 1 à 4 + nouveautés). Copiez-les dans votre dossier Mentorme en conservant
les sous-dossiers, puis :

    python manage.py migrate
    python manage.py seed_demo        (facultatif : données de démonstration)
    python manage.py runserver

## Nouveautés
- Demande de rôle (mentor, expert, investisseur) : POST /api/profiles/role-requests/
  Validation par l admin : Django admin > Profiles > "Role requests" > action "Valider".
  Le profil devient vérifié, reçoit le rôle, et apparaît dans la liste des mentors.
- Profil : titre (headline) et pourcentage de complétion
- Appels à projets publiés par l administration : Django admin > Calls > "Appels à projets"
  API : GET /api/calls/, POST /api/calls/<id>/save/, POST /api/calls/<id>/apply/
- Publications : titre, projet lié (bouton "Découvrir le projet"), photo et titre de l auteur
- Projets : besoins ouverts (POST /api/projects/<id>/needs/) et photo du porteur
- Créneaux : modifier / supprimer ses créneaux (non réservés)
- Commande seed_demo : 3 mentors, 2 projets, 2 publications, 3 appels, créneaux (mot de passe Demo#2026pass)
