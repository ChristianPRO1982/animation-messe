# Brevo : configuration et essai contrôlé

Le fournisseur retenu est Brevo via le backend SMTP standard de Django. Le
compte et le domaine `animation-messe.fr` ont été préparés côté Brevo/DNS.
La clé SMTP reste dans un fichier secret extérieur au dépôt.

## 1. Identités d'expédition

Déclarer et vérifier ces deux expéditeurs dans Brevo avant un essai réel :

| Profil du service | Adresse | Nom affiché |
| --- | --- | --- |
| `default` | `no-reply@animation-messe.fr` | Animation Messe |
| `planning` | `planning-noreply@animation-messe.fr` | Animation Messe - Planning |

La connexion SMTP est `be2ae2001@smtp-brevo.com`, distincte de ces adresses.
Le serveur est `smtp-relay.brevo.com`, port `587`, avec STARTTLS (`use_tls=true`,
`use_ssl=false`). La clé SMTP sert de mot de passe, pas une clé API Brevo.
Les adresses d'expédition ne constituent pas des boîtes de réception ; les
besoins éventuels de réception ou de réponse sont à configurer séparément.

## 2. Préparer Docker local

La surcharge `compose.email.yaml` est optionnelle. Sans elle, le démarrage
DEV habituel conserve sa configuration et ne nécessite aucun secret Brevo.

1. Placer la clé SMTP dans un fichier extérieur au dépôt, avec un accès limité
   au propriétaire. Ne jamais la placer dans un `.env`, un script, une commande
   versionnée, un ticket ou le chat. Le fichier doit être lisible par le
   processus du conteneur.
2. Créer `.env.email.local` à partir de `.env.email.local.example` et remplacer
   uniquement le chemin du secret par son chemin absolu sur l'hôte. Conserver
   `AM_EMAIL_ENABLED=false` pendant la préparation. Le fichier local est exclu
   de Git et du contexte de construction Docker.
3. Démarrer les services avec les surcharges DEV et email :

```bash
docker compose --env-file .env.dev --env-file .env.email.local -f compose.yaml -f compose.dev.yaml -f compose.email.yaml up -d --build
```

4. Appliquer les migrations :

```bash
docker compose --env-file .env.dev --env-file .env.email.local -f compose.yaml -f compose.dev.yaml -f compose.email.yaml exec web python manage.py migrate
```

Docker monte le secret en lecture seule sur `/run/secrets/brevo_smtp_key`.
Django le lit via `EMAIL_HOST_PASSWORD_FILE`. Aucun mot de passe SMTP n'est
injecté en clair dans la configuration Compose ou affiché par la procédure.
Le domaine d'envoi et les identités sont fournis par la surcharge ; aucune
adaptation spécifique du provider n'est nécessaire dans les apps métier.

## 3. Les deux autorisations

La migration crée une autorisation BDD globale désactivée. Le rôle
Administrateur AM la modifie dans « Paramètres du site », section
« Envoi des e-mails ».

| Environnement | Administration | Résultat d'une tentative `pending` |
| --- | --- | --- |
| Désactivé | Désactivée ou activée | `blocked_env` : Impossible d'envoyer des emails |
| Activé | Désactivée ou absente | `blocked_admin` : Impossible d'envoyer des emails - blocage administratif |
| Activé | Activée | Tentative SMTP |

Le verrou environnement est le verrou de stabilité : l'administrateur ne peut
pas le contourner. Le verrou BDD sert au quotidien et reste modifiable lorsque
le serveur bloque les envois. Le réglage est global par base de données : deux
environnements utilisant la même base partagent donc ce réglage, mais chacun
conserve son autorisation serveur propre.

Une nouvelle désactivation administrative archive les anciens `blocked_admin`
encore courants en `blocked_admin_history`. Une levée du verrou ou un nouvel
enregistrement d'une autorisation déjà désactivée n'archive rien. Les
`blocked_env` ne sont pas historisés. Aucun de ces statuts ne déclenche de
reprise automatique.

## 4. Essai réel explicite

Les tests automatisés utilisent le backend mémoire ou un transport SMTP simulé.
Ils n'envoient aucun e-mail réel et n'ont pas besoin de la clé Brevo.

Pour un essai réel, choisir explicitement une adresse destinataire autorisée,
puis :

1. Mettre `AM_EMAIL_ENABLED=true` dans le fichier local et recréer le service
   `web` avec la même commande Compose `up -d`. Un simple `restart` ne recharge
   pas les variables d'environnement.
2. Activer l'autorisation administrateur dans les paramètres du site.
3. Appeler `send_email_now()` avec `test_notification` et le destinataire choisi,
   selon le [guide d'utilisation](usage.md). Tester séparément les profils
   `default` et `planning`, avec des clés métier de test distinctes.
4. Vérifier le statut en BDD/admin, l'identité d'expédition, le sujet, les
   parties texte et HTML, puis la réception effective et les éventuels spams.
   `sent` prouve l'acceptation du backend, pas la réception en boîte principale.
5. Désactiver l'autorisation BDD après l'essai et remettre l'autorisation
   serveur à `false` tant que le raccordement n'est pas validé.

Une notification de test bloquée ne sera pas envoyée après réactivation :
utiliser une nouvelle clé de test pour un nouvel essai volontaire. Ne pas
modifier son statut manuellement pour contourner les verrous.

Ne pas copier les logs contenant un message complet ou une configuration
résolue avec des secrets. Les diagnostics du service sont volontairement fixes.
Une panne de persistance après acceptation SMTP reste un cas ambigu : pas de
retry aveugle, même si la trace est restée `pending`.

## 5. Transposer en production

Conserver les mêmes paramètres SMTP et les deux identités, mais déployer le
secret séparément sur l'hôte de production et le monter en lecture seule au
chemin configuré par `EMAIL_HOST_PASSWORD_FILE`. Ne pas réutiliser un chemin
local qui n'existe pas sur cet hôte.

La surcharge email peut être combinée avec la surcharge de production du
déploiement, ou ses paramètres reportés dans cette dernière. Ne pas remplacer
la configuration complète de production par le seul exemple email. Garder
`AM_EMAIL_ENABLED=false` pendant les migrations et la vérification du montage,
puis procéder à un essai réel explicitement autorisé avant activation durable.

Le réglage BDD est initialisé à `False` lors de la migration sur chaque base.
L'activation durable reste distincte du branchement des premiers flux métier :
les templates de consentement et de planning ne sont pas encore fournis.
