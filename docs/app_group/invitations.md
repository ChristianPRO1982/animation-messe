# Invitation et consentement des Membres AM

## Parcours implémenté

Le Responsable avec accès AM crée une demande avec nom, prénom et email.
`app_group.invitations.invite_am_member()` fige le consentement actif, génère
deux secrets indépendants et programme un envoi après commit via
`app_email.services.send_private_email_now()`, profil `default`.
L'adresse n'est jamais persistée, ni sur la demande, ni sur le profil, ni dans
la trace email. Le fournisseur SMTP et la boîte du destinataire restent hors
de cette garantie de stockage local. Le backend console est interdit pour ce flux.

L'email contient deux liens personnels : consentement et suppression. Les
secrets sont uniquement dans l'email et leurs empreintes en base, jamais
affichés au Responsable ni enregistrés en session. Le fragment du lien est
transmis par POST depuis la page publique ; GET ne prend aucune décision.
JavaScript est nécessaire. Ne pas partager ni journaliser ces liens.

La page de consentement présente l'identité et le texte exact figé à
l'invitation. Une acceptation explicite crée le Membre AM et supprime la
demande ; un refus supprime la demande sans créer de membre. Une double
acceptation concurrente ne crée qu'un profil. Les invitations expirent à 14 jours.

Le lien de suppression permet d'annuler une invitation encore valide, puis de
supprimer le Membre AM après acceptation, sans expiration automatique du secret
de retrait. Une confirmation POST est obligatoire. La suppression retire le
profil, son ancre et les associations locales, sans conserver une identité
historique. Les futures références de planning devront respecter cette règle.
Un Responsable du groupe ou l'Administrateur AM dispose aussi d'une commande
avec confirmation dans l'interface, notamment lorsque l'email est perdu.

Nom et prénom ne sont plus modifiables après validation, même par l'admin.
Une correction nécessite suppression et nouvelle invitation. Le titre et les
fonctions restent modifiables par tout membre du groupe disposant de l'accès AM.
Cela ne donne aucun droit applicatif au Membre AM lui-même.

## Blocages et conservation

Le résultat affiché au Responsable est celui du service email : succès,
message exact du verrou environnement ou administrateur, ou erreur technique.
Il n'y a aucun retry ni reprise après réactivation. Une nouvelle invitation
volontaire exige de saisir à nouveau l'adresse et crée de nouveaux secrets.

À la création, une échéance de purge à 7 jours est réservée ; elle est retirée
après envoi réussi. Blocages, échecs et interruptions avant confirmation de
l'envoi gardent cette échéance. Les autres demandes expirent à 14 jours.
Une panne entre SMTP et PostgreSQL reste ambiguë : ne pas renvoyer aveuglément.

La purge est **manuelle**, sans tâche planifiée :

```bash
python manage.py purge_am_member_requests --dry-run
python manage.py purge_am_member_requests
```

Elle supprime les demandes dont `purge_at` ou `expires_at` est atteint, sans
envoyer d'email. Sans exécution, les lignes restent présentes, mais les liens
arrivés à échéance ne permettent plus de valider la demande.

## Déploiement

Appliquer les migrations `app_email.0003` et `app_group.0006`. Elles retirent
les adresses et empreintes métier existantes, nettoient les destinataires des
traces `group_am_member_invitation`, et initialisent les identifiants publics
et les textes de consentement. Les anciennes invitations sans secret de retrait
doivent être recréées pour le nouveau parcours ; les anciens membres restent
supprimables par un Responsable ou l'Administrateur AM.

Définir `AM_PUBLIC_ORIGIN` explicitement : `http://localhost:8000` en local,
origine HTTPS en production, sans chemin ni identifiants. Ne jamais dériver
cette origine de l'en-tête Host d'une requête. Les pages publiques sont sans
cache, sans référent et sans ressource tierce.

Suivre ensuite [l'essai Brevo](../app_email/brevo.md#6-essai-du-parcours-membre-am)
avec un destinataire explicitement autorisé, puis refermer les verrous.
