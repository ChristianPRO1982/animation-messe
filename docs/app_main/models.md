# app_main — Modèle BDD

Ce document décrit le contrat BDD de `app_main`, c'est-à-dire le socle partagé
qui ne relève pas d'un module métier.

Les règles fonctionnelles sources restent :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/app_main/functional_requirements.md`
- `docs/keycloak_connexion.md`

---

# 1. Frontière

`app_main` porte uniquement :

- les paramètres globaux du site ;
- les pages communes ;
- l'intégration d'authentification ;
- la résolution de l'utilisateur courant depuis la session ;
- la lecture du répertoire externe `users.users`.

Il ne possède pas :

- les comptes CARThographie ;
- les profils globaux AM persistés ;
- les rôles de groupe ;
- les Membres AM sans compte ;
- les consentements ;
- les célébrations ;
- le planning ;
- les chants, recueils ou tags.

`users.users` reste la source de vérité des comptes. `app_main` la lit en
lecture seule et ne doit jamais la modifier.

---

# 2. Table `am.site_params`

## Rôle

Cette table stocke les paramètres globaux administrables du site Animation
Messe.

Elle ne doit pas devenir un lieu de configuration métier propre aux groupes,
aux célébrations, au planning ou aux chants.

## Structure actuelle cible

```text
table : am.site_params
PK    : language
```

Champs fonctionnels actuels :

```text
language
title
title_h1
signup_url
home_text
bloc1_text
bloc2_text
admin_message
admin_message_cooldown_minutes
```

Les contenus d'accueil peuvent contenir une structure applicative légère, par
exemple les cartes de page d'accueil sérialisées dans `home_text`.

## Résolution par langue

La résolution d'une ligne `SiteParams` doit suivre cet ordre :

1. langue de la requête ;
2. langue par défaut Django ;
3. première ligne disponible ;
4. `None` si aucune ligne n'existe.

Le code consommateur doit donc accepter l'absence totale de paramètres.

## Héritage technique à corriger

Le dépôt contient encore des champs issus d'un ancien besoin de modération LSS :

```text
moderator_message
moderator_message_cooldown_minutes
```

Ces champs ne constituent pas une cible fonctionnelle AM, car Animation Messe
n'a pas de rôle global Modérateur. Ils peuvent rester temporairement présents
pour compatibilité technique, mais toute évolution cible doit privilégier les
messages administrateur globaux ou des messages métier portés par les apps
concernées.

---

# 3. Table externe `users.users`

## Rôle

`users.users` est une table externe à AM. Elle représente le répertoire des
comptes CARThographie synchronisés avec Keycloak.

`app_main` peut l'exposer techniquement via `DirectoryUserRecord`, mais ce
modèle est non géré par Django AM.

## Contrat lu par AM

Champs lus par `app_main` :

```text
id
username
first_name
last_name
email
enabled
email_verified
synced_at
last_login_at
```

Seul `id`, UUID Keycloak, est autoritatif pour rapprocher une session externe
et un utilisateur AM.

`username`, `email`, `first_name` et `last_name` sont des attributs
d'affichage. Ils ne doivent pas porter l'autorisation principale.

## Règles

- `app_main` ne crée pas de ligne dans `users.users`.
- `app_main` ne modifie pas de ligne dans `users.users`.
- un utilisateur absent ou désactivé ne reçoit pas de session AM locale ;
- si un utilisateur disparaît ou devient désactivé pendant une session, la
  session AM doit être vidée.

---

# 4. Contrat vers `app_member`

`app_main` délègue à `app_member` la lecture des données globales persistées
propres à Animation Messe.

Le contrat attendu est :

- `app_main` fournit l'identité externe active ;
- `app_member` indique si cette identité possède le rôle Administrateur AM ;
- `request.user.is_admin` expose ce rôle au runtime ;
- aucun autre rôle global AM ne doit être ajouté au contrat `request.user` sans
  arbitrage fonctionnel.

Les rôles de groupe, Membres AM et consentements restent hors périmètre de
`app_main`.
