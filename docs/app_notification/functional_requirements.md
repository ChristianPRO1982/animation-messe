# Notifications email

## Objectif

Animation Messe envoie les emails transactionnels simples directement depuis
Django, sans dépendre de n8n. Les services métier n'appellent pas `send_mail()`
directement : ils passent par la couche `app_notification.services.email`.

## Configuration

Les paramètres email viennent de l'environnement :

- `EMAIL_BACKEND` ;
- `EMAIL_ENABLED` ;
- `DEFAULT_FROM_EMAIL` ;
- `EMAIL_FROM_NAME` ;
- `EMAIL_HOST` ;
- `EMAIL_PORT` ;
- `EMAIL_HOST_USER` ;
- `EMAIL_HOST_PASSWORD` ou `EMAIL_HOST_PASSWORD_FILE` ;
- `EMAIL_USE_TLS` ;
- `EMAIL_USE_SSL`.

En développement local, `EMAIL_ENABLED=false` évite tout vrai envoi. En tests,
les cas d'envoi utilisent le backend mémoire Django via `override_settings`.

## Traçabilité

Chaque email fonctionnel peut créer une ligne `EmailNotification` avec :

- type de notification ;
- destinataire ;
- groupe concerné si applicable ;
- référence métier éventuelle ;
- statut `pending`, `sent` ou `failed` ;
- dates de création et d'envoi ;
- erreur éventuelle ;
- identifiant provider éventuel.

La trace ne stocke pas le contenu complet du mail ni les tokens/secrets bruts.

## Templates

Chaque notification utilise des templates Django séparés :

- `subject.txt` ;
- `body.txt` ;
- `body.html`.

## Première notification branchée

La création d'une invitation Membre AM envoie un email
`am_member_invitation`. Le lien prépare le workflow public de validation qui sera
implémenté dans une étape suivante.
