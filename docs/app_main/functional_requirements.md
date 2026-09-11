# app_main — Functional Requirements

`app_main` porte le socle partagé d’Animation Messe.

Il fournit les pages communes, l’intégration d’authentification, la résolution de l’utilisateur courant, les paramètres globaux du site et les préférences navigateur qui ne relèvent pas d’un module métier.

Sources fonctionnelles principales :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/general_overview.md`

---

# 1. Rôle fonctionnel

`app_main` est responsable :

- de la page d’accueil publique ;
- des pages communes d’information, dont la politique de confidentialité ;
- des flux login, callback, provisioning et logout ;
- du chargement de `request.user` à partir de la session ;
- de la lecture du répertoire externe `users.users` ;
- des paramètres globaux stockés dans `am.site_params` ;
- de la page compte partagée ;
- des préférences de langue et de thème au niveau navigateur ;
- des messages globaux administrateur.

`app_main` ne possède pas :

- les rôles de groupe ;
- les Membres AM ;
- les consentements ;
- les célébrations ;
- le planning ;
- les chants ou recueils ;
- les règles métier de validation des modules.

---

# 2. Authentification et identité

L’identité vient d’un fournisseur externe.

Les modes supportés sont :

- `mock` en développement ;
- `keycloak` en environnement intégré.

`app_main` ne crée pas de compte local Django.

Il résout l’utilisateur authentifié en lecture seule dans `users.users`, via `DirectoryUserRecord` ou une requête SQL validée lorsque `USER_SCHEMA` / `USER_TABLE` changent.

Un utilisateur inconnu après callback Keycloak doit être dirigé vers le flux de provisioning Home configuré pour l’application `am`.

Le flux de provisioning :

- conserve l’utilisateur anonyme tant que `users.users` ne contient pas l’identité ;
- stocke uniquement un état temporaire de reprise en session ;
- expire après un délai court ;
- n’authentifie jamais l’utilisateur par la seule présence de cet état.

---

# 3. Contrat `request.user`

Le middleware de `app_main` expose un utilisateur runtime compatible avec les besoins AM.

Le contrat minimal contient :

- `is_authenticated` ;
- `is_anonymous` ;
- `external_id` ;
- `username` ;
- `email` ;
- `first_name` ;
- `last_name` ;
- `is_admin`.

L’indicateur `is_admin` est fourni par `app_member`.

Le code peut encore exposer temporairement des champs hérités de l’ancien miroir LSS. Ils ne doivent pas devenir un nouveau contrat fonctionnel AM.

Si l’utilisateur externe disparaît ou devient désactivé, la session locale doit être vidée.

---

# 4. Paramètres globaux

`app_main` possède le modèle `SiteParams` mappé vers `am.site_params`.

Ces paramètres couvrent :

- titre du site ;
- contenus de page d’accueil ;
- URL d’inscription ou de provisioning ;
- messages administrateur ;
- délais de réaffichage des messages.

La recherche d’un `SiteParams` doit :

1. essayer la langue de la requête ;
2. essayer la langue par défaut Django ;
3. utiliser la première ligne disponible ;
4. retourner `None` si aucune ligne n’existe.

---

# 5. Pages et routes

`app_main` expose les routes communes :

- `/` ;
- `/login/` ;
- `/login/diagnostic/` ;
- `/auth/callback/` ;
- `/provision/redirect/` ;
- `/provision/complete/` ;
- `/logout/` ;
- `/account/` ;
- `/themes/` ;
- `/language/` ;
- `/privacy-policy/` ;
- `/site-params/`.

Les routes de debug éventuelles doivent retourner `404` lorsque `DEBUG=False`.

La page compte est le point d’entrée partagé pour :

- consulter son identité runtime ;
- comprendre ses rôles globaux ;
- gérer les actions administrateur globales ;
- gérer les messages globaux ;
- rechercher un membre du répertoire externe pour lui attribuer un rôle global AM.

---

# 6. Règles fonctionnelles

**MAIN-AUTH-01** — `app_main` ne crée ni ne modifie les utilisateurs dans `users.users`.

**MAIN-AUTH-02** — Une session AM authentifiée repose toujours sur une identité externe active.

**MAIN-AUTH-03** — Un utilisateur Keycloak inconnu localement passe par le provisioning Home et reste anonyme jusqu’à résolution dans `users.users`.

**MAIN-AUTH-04** — Un callback invalide ou un utilisateur désactivé vide l’état local d’authentification.

**MAIN-USER-01** — `request.user` expose les informations d’identité externe et les rôles globaux AM.

**MAIN-USER-02** — Les rôles globaux AM sont lus depuis `app_member`, pas depuis Keycloak.

**MAIN-PARAM-01** — Les paramètres globaux sont stockés dans `am.site_params`.

**MAIN-PARAM-02** — Les contenus administrables doivent être résolus par langue avec fallback.

**MAIN-PAGE-01** — La page d’accueil reste accessible sans compte.

**MAIN-PAGE-02** — Les préférences de thème et de langue sont des préférences navigateur tant qu’aucune synchronisation serveur n’est spécifiée.

**MAIN-ADMIN-01** — La gestion complète des paramètres globaux est réservée aux administrateurs globaux AM.

---

# 7. Points encore à spécifier

1. contenu final de la page d’accueil AM ;
2. éventuels nouveaux champs `SiteParams` réellement utiles à AM hors besoins propres à LSS ;
3. présence ou non d’une page d’administration globale séparée de `/account/` ;
4. comportement exact des messages globaux sur les futures pages `app_group`, `app_planning` et `app_celebration`.
