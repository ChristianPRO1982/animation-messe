# Email — Modèle et architecture technique

Ce document décrit le contrat technique cible du module email.

La V1 utilise une app Django dédiée :

```text
app_email
```

Les apps métier appellent un service email central, jamais directement le
backend Django ou le provider.

---

# 1. Frontière

Le module email possède :

- la table de trace des notifications ;
- le service d'envoi ;
- le rendu des templates d'e-mails ;
- l'abstraction du backend/provider ;
- l'administration minimale des notifications ;
- les tests transverses d'envoi.

En V1, aucun déclencheur automatique n'est branché dans les apps métier
existantes.

Le module email ne possède pas :

- les groupes ;
- les membres ;
- les Membres AM ;
- les plannings ;
- les célébrations ;
- les feuilles générées ;
- les comptes externes ;
- les rôles et permissions métier.

Les apps métier restent propriétaires de leurs règles.

Exemples :

- `app_group` décide qu'une invitation Membre AM doit être envoyée ;
- `app_planning` décide qu'un planning personnel doit être envoyé ;
- `app_celebration` décide qu'une feuille est disponible ;
- `app_email` rend, envoie et trace la notification.

---

# 2. Fichiers créés en V1

Structure implémentée en V1 :

```text
app_email/
    __init__.py
    admin.py
    apps.py
    models.py
    services.py
    tests.py
    migrations/
        __init__.py

templates/
    emails/
        test_notification/
            subject.txt
            body.txt
            body.html
```

Les templates métier réels, par exemple `group_am_member_invitation` ou
`planning_personal_schedule`, restent à créer au moment où le flux métier
correspondant est branché. La V1 ne fournit que le template de test nécessaire
aux tests d'infrastructure email.

Des sous-modules peuvent être ajoutés si le service grossit :

```text
app_email/services/rendering.py
app_email/services/delivery.py
app_email/services/notifications.py
```

La V1 peut rester simple avec un seul `services.py` si cela suffit.

---

# 3. Fichiers existants modifiés en V1

Fichiers concernés :

```text
config/settings.py
config/urls.py
templates/
```

Modifications attendues :

- ajouter `app_email` à `INSTALLED_APPS` ;
- ajouter la configuration email par variables d'environnement ;
- ajouter Django Admin ;
- protéger `/admin/` du middleware de session AM ;
- ajouter les templates d'e-mails nécessaires aux tests d'infrastructure ;
- ajouter les tests.

Les branchements métier doivent rester explicites.

Il ne faut pas créer un système qui scanne la base pour deviner seul tous les
e-mails à envoyer.

---

# 4. Configuration

Toutes les valeurs de configuration doivent provenir de variables
d'environnement.

Variables minimales :

```text
EMAIL_BACKEND
DEFAULT_FROM_EMAIL
AM_EMAIL_FROM_NAME
AM_EMAIL_ENABLED
AM_EMAIL_SUBJECT_PREFIX
```

Pour SMTP :

```text
EMAIL_HOST
EMAIL_PORT
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_USE_TLS
EMAIL_USE_SSL
EMAIL_TIMEOUT
```

Avec Django 6, ces variables d'environnement alimentent la configuration
`MAILERS["default"]`. Elles ne doivent pas obliger les services métier à
connaître le backend utilisé.

Pour un futur provider API :

```text
AM_EMAIL_PROVIDER
AM_EMAIL_PROVIDER_API_KEY
AM_EMAIL_PROVIDER_ENDPOINT
```

Ces variables de provider API sont réservées à une évolution future. La V1 ne
code aucun provider Outlook, Microsoft Graph ou OAuth.

Les secrets peuvent aussi être lus via des variables `*_FILE`, comme le reste
du projet lorsque c'est pertinent.

Comportements par environnement :

```text
développement local
    EMAIL_BACKEND = django.core.mail.backends.console.EmailBackend
    AM_EMAIL_ENABLED = false par défaut ou true uniquement volontairement

tests
    EMAIL_BACKEND = django.core.mail.backends.locmem.EmailBackend
    aucun envoi réel

production
    EMAIL_BACKEND = backend SMTP ou provider configuré
    AM_EMAIL_ENABLED = true
```

L'envoi exige `AM_EMAIL_ENABLED = true` et `EmailSettings.enabled = true`.
Le verrou serveur est prioritaire : s'il bloque, une tentative passe de
`pending` à `blocked_env`, sinon une autorisation BDD absente ou désactivée
produit `blocked_admin`. `queue_email()` seul crée toujours `pending`.
Une notification non `pending` n'est jamais renvoyée automatiquement.

Le fournisseur retenu est Brevo via le backend SMTP Django standard, avec
STARTTLS sur le port 587. Voir [brevo.md](brevo.md) pour le raccordement.

---

# 5. Modèle de données

Table recommandée :

```text
am.e_email_notification
```

Alias :

```text
een
```

Champs :

```text
een_id
notification_type
sender_key
recipient_email
recipient_member_id
gg_id
content_object_type
content_object_id
business_key
status
provider_message_id
error_message
created_at
sent_at
failed_at
updated_at
```

## 5.1. Champs

`notification_type`

Identifiant stable du type de notification.

Exemples :

```text
group_am_member_invitation
planning_personal_schedule
celebration_sheet_available
account_inactivity_warning
```

`recipient_email`

Adresse utilisée pour l'envoi.

Elle doit être conservée seulement si nécessaire à la traçabilité.

`recipient_member_id`

UUID du compte CARThographie lorsque le destinataire est un membre avec compte.

Peut être vide pour un Membre AM ou une invitation externe.

`gg_id`

Groupe concerné si applicable.

FK vers `am.g_group.gg_id` si le groupe est propriétaire AM de l'événement.

`content_object_type` et `content_object_id`

Référence souple vers l'objet métier concerné.

Exemples :

```text
app_group.AmMemberRequest + gamr_id
app_celebration.Celebration + cel_id
planning_personal_period + 2026-W40:2026-W45
```

Ne pas utiliser cette référence pour porter une permission.

`business_key`

Clé d'idempotence métier.

Exemples :

```text
group_am_member_invitation:7:42:alice@example.test
planning_personal_schedule:7:2026-10:11111111-1111-1111-1111-111111111111
celebration_sheet_available:88:11111111-1111-1111-1111-111111111111
```

`status`

Statut courant de la notification.

`provider_message_id`

Identifiant retourné par le provider si disponible.

`error_message`

Diagnostic technique court issu d'une liste de messages fixes. Le texte libre
des exceptions du backend n'est ni stocké ni loggé, car il peut contenir des
secrets ou des données personnelles sous des formats imprévisibles.

Le corps complet de l'e-mail ne doit pas être stocké par défaut.

---

# 6. Statuts

Statuts minimaux :

```text
pending
sent
failed
```

Statuts recommandés :

```text
pending
sent
failed
skipped
blocked_env
blocked_admin
blocked_admin_history
```

`pending`

Notification créée et envoyable.

`sent`

Envoi accepté par le backend/provider.

`failed`

Tentative d'envoi en erreur.

`skipped`

Statut historique d'une notification ignorée ; sa cause n'est pas reclassifiée.

`blocked_env` : blocage par l'environnement, message
« Impossible d'envoyer des emails ».

`blocked_admin` : blocage administratif courant, message
« Impossible d'envoyer des emails - blocage administratif ».

`blocked_admin_history` : blocage administratif archivé, avec le même message.
Ces trois statuts sont terminaux pour l'envoi automatique. `status` accepte
32 caractères et l'admin permet de filtrer les nouvelles valeurs.

## Réglage global et périodes administratives

`EmailSettings`, dans `am.e_email_settings`, possède une unique ligne `id=1`
(contrainte BDD), avec `enabled=False` à l'initialisation. La migration crée
cette ligne. Ce réglage est indépendant de `SiteParams.language` et accessible
au rôle Administrateur AM dans les paramètres du site.

`set_email_enabled()` verrouille cette ligne et, uniquement lors du passage de
`enabled=True` à `False`, passe les notifications encore `blocked_admin` en
`blocked_admin_history` dans la même transaction. Les statuts modifiés, les
blocages environnement et les autres états restent intacts. Un enregistrement
répété du verrou et sa levée n'archivent rien.

L'ordre de verrouillage commun aux envois et aux bascules est : réglage global,
puis notification. Les envois autorisés sont sérialisés pendant l'appel SMTP.
La lecture du réglage est évitée lorsque l'environnement bloque. Une ligne
absente est une interdiction ; une erreur de lecture est propagée avant SMTP.

---

# 7. Contraintes

Contraintes recommandées :

```text
business_key unique lorsque non null
status dans la liste des statuts connus
notification_type non vide
recipient_email non vide pour une notification envoyable par email
```

La contrainte d'unicité sur `business_key` doit rester compatible avec les
renvois volontaires.

Deux options sont acceptables :

- nouvelle notification avec suffixe de renvoi dans la clé ;
- table séparée d'essais d'envoi si le besoin devient plus fin.

La V1 peut rester sur une seule table.

---

# 8. Service d'envoi

API V1 :

```python
queue_email(
    notification_type: str,
    recipient_email: str,
    context: dict | None = None,
    *,
    recipient_member_id: str | None = None,
    group=None,
    content_object=None,
    business_key: str | None = None,
    sender_key: str = "default",
) -> EmailNotification
```

```python
send_notification(
    notification: EmailNotification,
    context: dict | None = None,
) -> EmailNotification
```

```python
send_email_now(
    notification_type: str,
    recipient_email: str,
    context: dict | None = None,
    *,
    recipient_member_id: str | None = None,
    group=None,
    content_object=None,
    business_key: str | None = None,
    sender_key: str = "default",
) -> EmailNotification
```

`queue_email()` crée ou retrouve la trace ; son paramètre `context` n'est pas
stocké. Pour un envoi séparé, fournir le contexte à `send_notification()`.
`send_email_now()` le transmet directement au rendu. Aucun corps de message
n'est persisté par ces fonctions.

`sender_key` est persisté sur la notification et vaut `default` pour les
notifications préexistantes. Seuls `default` et `planning` sont acceptés.
`default` utilise `DEFAULT_FROM_EMAIL` / `AM_EMAIL_FROM_NAME` ; `planning`
utilise `AM_EMAIL_PLANNING_FROM_EMAIL` / `AM_EMAIL_PLANNING_FROM_NAME`.
La réutilisation d'une clé métier ne modifie pas son profil d'expédition.

Les services métier doivent utiliser une fonction de haut niveau adaptée au cas
métier.

Exemples :

```python
send_am_member_invitation(...)
send_personal_planning(...)
send_celebration_sheet_available(...)
```

Ces fonctions peuvent vivre dans `app_email.services` ou dans des modules
spécialisés, mais elles doivent toutes passer par le même moteur d'envoi.

---

# 9. Templates

Les e-mails utilisent des templates Django.

Structure :

```text
templates/emails/<notification_type>/subject.txt
templates/emails/<notification_type>/body.txt
templates/emails/<notification_type>/body.html
```

Règles :

- le sujet est dans `subject.txt` ;
- le texte brut est obligatoire ;
- le HTML est optionnel mais recommandé pour les e-mails riches ;
- le sujet et le corps texte préservent les caractères du contexte sans
  échappement HTML ; le corps HTML conserve l'échappement automatique Django ;
- le Python ne construit pas de longs corps HTML ;
- chaque template reçoit un contexte métier minimal ;
- les secrets ne doivent pas être injectés dans des logs de rendu.

Le sujet rendu doit être normalisé sur une seule ligne, préfixe de configuration
inclus. Un HTML absent permet un envoi texte seul ; un HTML présent mais cassé
(par exemple une inclusion introuvable) fait échouer le rendu et l'envoi.

En V1, seuls les templates `test_notification` existent dans le dépôt. Les
types métier cités ci-dessous sont des exemples de flux futurs et ne doivent
pas être appelés tant que leurs templates et services métier dédiés ne sont pas
ajoutés.

---

# 10. Flux d'envoi

Flux synchrone V1 :

```text
service métier
-> construit le contexte minimal
-> appelle app_email.services
-> crée EmailNotification(pending)
-> rend subject/body
-> appelle django.core.mail.EmailMultiAlternatives
-> marque sent ou failed
-> retourne la notification
```

Les erreurs de rendu et du backend sont capturées dans le service email. Leur
diagnostic fixe est loggé avant la sauvegarde du statut `failed`, sans traceback
du backend. Les erreurs de persistance restent propagées à l'appelant, sans
chaîner l'exception sensible du backend. Un échec de sauvegarde de `sent` n'est
pas requalifié en échec du backend.

`send_notification()` exige une notification déjà enregistrée en base ; sinon,
il lève `ValueError` avant le rendu et avant tout envoi.

Pour une notification persistée, le service verrouille la ligne en base et
relit son statut avant tout envoi. Le verrou est conservé jusqu'à la mise à
jour du statut. Seules les notifications `pending` sont envoyées : deux
instances chargées avant l'envoi ne peuvent donc pas provoquer un double envoi
concurrent. Une notification non `pending`, y compris bloquée ou historique,
n'est pas réessayée automatiquement, même après réactivation des envois.

Le verrou ne rend pas l'envoi SMTP transactionnel : les futurs appels métier
doivent intervenir après la validation de leur transaction, afin qu'un rollback
métier ne remette pas à `pending` une notification déjà envoyée.

Une panne de persistance après acceptation SMTP peut également laisser une
notification `pending` malgré l'envoi effectif. Dans ce cas, aucun retry aveugle
ne doit être déclenché : la V1 ne garantit pas l'envoi exactement une fois face
aux pannes entre SMTP et PostgreSQL.

Le service métier peut choisir :

- de continuer si l'e-mail échoue ;
- ou de remonter une erreur uniquement pour un cas explicitement critique.

La règle par défaut est de ne pas annuler l'opération métier principale pour un
échec d'e-mail.

## 10.1. Limites connues de la V1

Ces deux limites restent présentes dans l'implémentation. Elles ne bloquent
pas un essai local contrôlé, mais doivent être prises en compte avant de
brancher les flux métier ou d'augmenter les volumes.

### Absence d'atomicité entre SMTP et PostgreSQL

L'acceptation du message par SMTP et la sauvegarde du statut `sent` sont deux
opérations distinctes. Si SMTP accepte le message mais que la sauvegarde ou le
commit échoue, la trace peut rester `pending` alors que le message est déjà
parti. Un nouvel appel sur cette notification peut alors produire un doublon.
Le verrou et la clé d'idempotence protègent les appels concurrents ordinaires,
mais ne garantissent donc pas un envoi exactement une fois face à cette panne.

En cas de résultat ambigu, ne pas réessayer automatiquement et ne pas déduire
de `pending` que le message n'a pas été envoyé. Vérifier les événements du
fournisseur et la trace locale avant de décider d'un éventuel renvoi volontaire.
Conserver les appels après le commit métier, selon le guide d'utilisation.
Une future stratégie de reprise devra traiter explicitement ce cas ; ajouter
un worker ou une file d'attente ne suffit pas, à lui seul, à le résoudre.

### Sérialisation des envois autorisés

Le verrou de la ligne globale `EmailSettings` est conservé pendant le rendu,
l'appel SMTP et la mise à jour de la notification. Les envois autorisés
partageant cette base sont donc traités un par un, même pour des notifications
différentes. Une désactivation administrative attend aussi la fin de l'envoi
déjà engagé ; elle ne l'annule pas rétroactivement.

Ce choix garantit un ordre cohérent entre les bascules administratives et le
classement des blocages. En contrepartie, un SMTP lent peut faire attendre les
autres envois et l'administration. Le délai SMTP configuré ne constitue pas
une borne globale sur l'attente des verrous ou sur la durée totale du traitement.
Ce compromis est retenu pour la V1 à faible volume. Avant des envois en masse,
mesurer les délais et revoir la stratégie de concurrence en conservant les
garanties d'historisation ; ne pas simplement retirer le verrou global.

---

# 11. Exemples de notifications métier

## 11.1. Invitation Membre AM

Type :

```text
group_am_member_invitation
```

Déclencheur :

```text
app_group.services.create_am_member_request
```

Destinataire :

```text
AmMemberRequest.email
```

Objet métier :

```text
AmMemberRequest
```

Idempotence :

```text
type + gamr_id + recipient_email
```

## 11.2. Planning personnel

Type :

```text
planning_personal_schedule
```

Déclencheur :

```text
action explicite d'un Responsable ou action future planifiée
```

Destinataire :

```text
membre avec compte ou Membre AM selon les données disponibles
```

Contenu :

```text
liste des célébrations et fonctions du destinataire sur une période
```

Idempotence :

```text
type + groupe + période + destinataire
```

Ce type d'e-mail doit être conçu comme une notification métier normale, pas
comme une fonctionnalité d'administration.

## 11.3. Feuille disponible

Type :

```text
celebration_sheet_available
```

Déclencheur :

```text
validation ou génération d'une feuille de célébration
```

Destinataire :

```text
Responsables impression ou personnes autorisées selon app_celebration
```

Idempotence :

```text
type + célébration + feuille + destinataire
```

---

# 12. Tests attendus

Tests minimum V1 (infrastructure email) :

- création d'une notification `pending` ;
- rendu du bon sujet ;
- rendu du bon template texte ;
- rendu du template HTML lorsqu'il existe ;
- envoi vers la bonne adresse ;
- passage de `pending` à `sent` ;
- passage à `failed` si le backend échoue ;
- aucun envoi réel en tests ;
- respect de l'idempotence ;
- absence de secret dans les logs ou erreurs stockées.

Lors de l'ajout du futur flux métier de planning personnel, ajouter un test
vérifiant que l'e-mail ne contient aucune donnée inutile d'autres membres.

Les tests doivent utiliser le backend mémoire Django :

```text
django.core.mail.backends.locmem.EmailBackend
```

---

# 13. Administration Django

L'admin Django affiche au minimum :

- type ;
- destinataire ;
- groupe ;
- statut ;
- date de création ;
- date d'envoi ;
- date d'échec ;
- erreur.

Actions admin possibles en V1 :

- consulter ;
- filtrer ;
- rechercher ;
- éventuellement relancer une notification `failed` si la fonction est
  explicitement codée et testée.

Pas d'éditeur de contenu ou de workflow en V1.

L'admin est consultatif : création, modification et suppression des
notifications sont interdites, y compris pour les superutilisateurs. L'action
de suppression groupée n'est pas disponible, afin de préserver les traces et
les clés d'idempotence.

---

# 14. Préparation future

Le service doit pouvoir évoluer vers :

- une commande Django envoyant les `pending` ;
- une tâche asynchrone ;
- un scheduler ;
- un provider API ;
- une API interne appelée par n8n.

Ces mécanismes ne sont pas à implémenter en V1 tant qu'ils ne sont pas
nécessaires.

