# Utiliser app_email depuis une autre app

Ce guide est le point d'entrée pratique pour Codex et les développeurs qui
doivent ajouter un envoi d'e-mail dans Animation Messe. Il décrit le socle V1
disponible et ses précautions d'intégration.

Les règles métier sont décrites dans [functional_requirements.md](functional_requirements.md)
et le contrat technique détaillé dans [models.md](models.md).

## 1. Choisir le bon point d'entrée

Toutes les apps Django du site peuvent importer `app_email.services`.

| Fonction | Utilisation |
| --- | --- |
| `send_email_now()` | Créer ou retrouver une notification, rendre les templates et tenter l'envoi immédiatement. Point d'entrée habituel. |
| `queue_email()` | Créer ou retrouver la trace sans rendre ni envoyer de message. |
| `send_notification()` | Envoyer une notification déjà enregistrée, avec son contexte de rendu. |
| `render_email()` | Rendre le sujet, le texte et le HTML sans créer de notification ni envoyer de message. |

Les apps métier déterminent l'événement, les destinataires autorisés et le
contexte minimal. Elles passent par ce service central ; elles n'appellent pas
directement `send_mail()`, `EmailMultiAlternatives`, SMTP ou un provider externe.

La V1 ne branche encore aucun événement métier automatiquement. Seul le type
`test_notification` dispose de templates fournis. Les noms comme
`planning_personal_schedule` sont des exemples de futurs flux, pas des types
déjà utilisables.

## 2. Appel direct et résultat

Exemple utilisable avec les templates existants, hors transaction métier :

```python
from app_email.models import EmailNotification
from app_email.services import send_email_now

notification = send_email_now(
    notification_type="test_notification",
    recipient_email="alice@example.test",
    context={
        "subject": "Information de test",
        "name": "Alice",
        "message": "Votre action a bien ete prise en compte.",
    },
    business_key="test_notification:guide:destinataire-42:v1",
)

if notification.status == EmailNotification.STATUS_FAILED:
    diagnostic = notification.error_message
```

Cet appel reste soumis à la configuration email. Il ne constitue pas un
nouveau flux métier à brancher tel quel en production.

| Statut retourné | Signification |
| --- | --- |
| `sent` | Le backend a accepté l'envoi ; cela ne prouve pas la réception dans la boîte du destinataire. |
| `failed` | Le rendu ou le backend a échoué, ou le backend a indiqué zéro envoi. Le diagnostic est dans `error_message`. |
| `skipped` | L'envoi était désactivé par `AM_EMAIL_ENABLED=False` lorsque la notification `pending` a été traitée. |

Un échec de rendu ou du backend est normalement converti en `failed`, sans
relancer l'exception brute. Les erreurs de validation, de création ou de
persistance peuvent en revanche lever une exception : ne pas supposer que
chaque appel retourne une notification.

L'admin Django permet de consulter, filtrer et rechercher les traces. Il
n'autorise ni création, ni modification, ni suppression, ni retry.

## 3. Envoyer après la transaction métier

Ne pas effectuer l'envoi à l'intérieur d'un `transaction.atomic()` métier.
Programmer l'appel avec `transaction.on_commit()` après la modification métier,
dans la transaction qui porte cette modification.

Exemple de fonction à placer dans le service de l'app appelante. Elle utilise
le type de test existant ; un vrai flux devra utiliser ses propres templates.

```python
from functools import partial

from django.db import transaction

from app_email.services import send_email_now


def programmer_notification(*, evenement_id, destinataire_id, email, prenom):
    contexte = {
        "subject": "Information de test",
        "name": prenom,
        "message": "Votre action a bien ete prise en compte.",
    }
    cle = f"test_notification:{evenement_id}:{destinataire_id}"

    transaction.on_commit(
        partial(
            send_email_now,
            notification_type="test_notification",
            recipient_email=email,
            context=contexte,
            business_key=cle,
        ),
        robust=True,
    )
```

- Appeler cette fonction après la sauvegarde métier, avant de sortir de la
  transaction ; le callback sera exécuté après le commit final.
- En cas de rollback, Django n'exécute pas le callback.
- Sans transaction active, le callback s'exécute immédiatement.
- Capturer les valeurs nécessaires au moment de l'inscription du callback et
  ne plus modifier le dictionnaire de contexte ensuite. `partial()` évite les
  captures tardives d'une variable de boucle par une `lambda`.
- `robust=True` permet à Django de journaliser une exception du callback et de
  poursuivre les callbacks suivants. Cela ne crée pas de retry et ne garantit
  pas qu'une trace ait pu être enregistrée en cas de panne de base.
- `on_commit()` ne retourne pas la notification produite par le callback. Si
  un traitement du résultat est nécessaire, le faire dans une fonction de
  callback dédiée.

L'envoi reste synchrone : il peut allonger la requête après le commit. La V1 ne
fournit ni worker, ni file durable, ni garantie d'exécution si le processus
s'arrête avant le callback.

## 4. Construire la clé d'idempotence

`business_key` identifie un événement à notifier à un destinataire. Elle est
unique dans toute la table, toutes apps et tous types confondus.

Construire une clé stable comprenant le type, les identifiants métier utiles,
le destinataire et, si nécessaire, la version de l'événement. Par exemple :

```text
planning_personal_schedule:groupe-7:periode-2026-10:validation-3:membre-42
```

Cette clé illustre un futur flux. Son type n'est pas fourni en V1.

- Deux appels avec la même clé retrouvent la même notification. Les nouveaux
  arguments ne remplacent pas son type, son destinataire ou ses autres données.
- Seules les notifications `pending` sont envoyées. Une clé déjà `sent`,
  `failed` ou `skipped` ne provoque aucun renvoi automatique.
- Ne pas réutiliser une même clé pour un autre destinataire ou un autre type,
  même en fournissant un nouveau contexte : celui-ci ne change pas l'identité
  de la notification existante.
- Un renvoi volontaire nécessite une nouvelle notification avec une nouvelle
  clé explicite. Ne pas ajouter un timestamp différent à chaque appel normal :
  cela supprimerait l'idempotence.
- Sans clé, chaque appel crée une nouvelle notification ; deux appels peuvent
  donc produire deux e-mails.
- Ne pas mettre de token, secret ou contenu personnel dans la clé. Préférer
  les identifiants techniques du destinataire à son adresse email.

Le verrou en base protège contre deux traitements concurrents de la même
notification. Il ne rend pas SMTP transactionnel : une panne après acceptation
SMTP mais avant sauvegarde de `sent` peut laisser une trace `pending` malgré
l'envoi effectif. Ne pas déclencher de retry aveugle dans cette situation.

## 5. Ajouter un vrai type d'e-mail

Pour chaque nouveau flux métier :

1. Définir son événement, ses destinataires autorisés, son contexte minimal et
   sa clé d'idempotence dans l'app métier.
2. Créer les templates Django correspondants :

```text
templates/emails/<notification_type>/subject.txt
templates/emails/<notification_type>/body.txt
templates/emails/<notification_type>/body.html
```

3. Fournir un sujet et un corps texte. Le HTML est optionnel : son absence
   autorise un envoi texte seul, mais une inclusion HTML cassée fait échouer
   le rendu.
4. Ajouter une fonction métier explicite qui appelle le service central après
   le commit, puis les tests du flux.

Le sujet est normalisé sur une ligne, préfixe de configuration inclus. Le sujet
et le corps texte conservent les caractères du contexte sans échappement HTML ;
le HTML conserve l'échappement automatique Django. Ne pas marquer des données
non fiables avec `safe`.

Ne pas mettre de donnée sensible dans le sujet. Ne pas journaliser le contexte,
le corps du message, un secret ou un lien contenant un token. Les diagnostics
du service sont des messages fixes, pas les erreurs brutes du backend.

## 6. Séparer création de la trace et envoi

`queue_email()` n'est pas une file d'attente exécutée en arrière-plan. Aucun
processus V1 ne parcourt automatiquement les notifications `pending`.

Exemple hors transaction métier, avec les templates existants :

```python
from app_email.services import queue_email, send_notification

contexte = {
    "subject": "Information de test",
    "name": "Alice",
    "message": "Message de test.",
}

notification = queue_email(
    "test_notification",
    "alice@example.test",
    business_key="test_notification:guide:envoi-separe:destinataire-42:v1",
)
notification = send_notification(notification, context=contexte)
```

Le paramètre `context` de `queue_email()` n'est pas stocké. Il faut fournir le
contexte à `send_notification()` ; le corps complet n'est pas conservé en base.
`send_notification()` refuse une instance non enregistrée avant tout rendu ou
envoi. Dans une transaction métier, différer son appel avec `on_commit()` comme
pour `send_email_now()`.

À la création, `queue_email()` et `send_email_now()` acceptent aussi
`recipient_member_id` (UUID optionnel), `group` (instance de
`app_group.models.Group` ou identifiant `gg_id`) et `content_object` (objet métier
dont le type et la clé primaire seront tracés). `send_notification()` utilise
les métadonnées de la notification déjà enregistrée, sans les recevoir à nouveau.

## 7. Configuration et vérifications

Les paramètres sont lus par `config/settings.py` depuis l'environnement :

| Paramètre | Rôle |
| --- | --- |
| `AM_EMAIL_ENABLED` | Activation des envois ; `false` par défaut. |
| `EMAIL_BACKEND` | Backend alimentant `MAILERS["default"]` de Django 6. |
| `DEFAULT_FROM_EMAIL` | Adresse de l'expéditeur. |
| `AM_EMAIL_FROM_NAME` | Nom affiché de l'expéditeur. |
| `AM_EMAIL_SUBJECT_PREFIX` | Préfixe optionnel du sujet. |

Pour SMTP, utiliser `django.core.mail.backends.smtp.EmailBackend` et configurer
`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` ou
`EMAIL_HOST_PASSWORD_FILE`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL` et `EMAIL_TIMEOUT`.
TLS et SSL ne doivent pas être activés simultanément.

Le backend console par défaut écrit le message complet sur la sortie standard :
ne pas l'utiliser avec de vraies données sensibles. En tests, forcer le backend
mémoire dans `MAILERS["default"]` et activer explicitement `AM_EMAIL_ENABLED`
pour les scénarios d'envoi. Aucun test ne doit contacter un serveur SMTP réel.

Tester le bon destinataire, le contenu minimal, le callback après commit et son
absence après rollback, l'idempotence, les statuts `failed` et `skipped`, ainsi
que l'absence de fuite de secrets. Avec `django.test.TestCase`, utiliser
`captureOnCommitCallbacks(execute=True)` pour exécuter les callbacks dans le test.

Les tests du socle nécessitent une base PostgreSQL de test compatible avec les
schémas du projet. Commandes de vérification :

```bash
uv run python manage.py check
uv run pytest -q app_email app_main/tests.py::ProjectSettingsTests
uv run ruff check app_email config/settings.py app_main/middleware.py app_main/tests.py
```
