# Connexion Keycloak - Animation Messe

## Objet

Ce document est le contrat de reference pour l'authentification dans Animation Messe.

Il est destine aux conversations Codex et aux documents techniques. Il doit etre lu comme un ensemble de contraintes et de decisions, pas comme une note exploratoire.

## Objectif courant

Fournir un flux d'authentification avec :

- `DEV` : service local `auth_mock` ;
- `PROD` : service externe `Keycloak` ;
- `AM` : session Django locale apres controle en lecture seule de `users.users`.

Le perimetre couvre la couche connexion. Les roles metier, groupes, affectations, celebrations et plannings sont traites par les SFD et les apps Django concernees.

## Regles non negociables

- `AM` n'est pas la source de verite des comptes utilisateur.
- `AM` ne modifie jamais les donnees de reference des comptes.
- `AM` ne lit jamais la base PostgreSQL interne de `Keycloak`.
- `AM` lit la table `users.users` de la base PostgreSQL `carthographie`, schema `users`, en lecture seule.
- La cle primaire fonctionnelle de `users.users` est l'UUID `Keycloak`.
- Le rapprochement utilisateur se fait uniquement par UUID `Keycloak`.
- `email` et `username` sont informatifs et ne doivent pas porter l'autorisation principale.
- Une authentification externe valide ne suffit pas pour entrer dans `AM`.
- Un utilisateur doit aussi exister dans `users.users` et etre actif.
- Un utilisateur absent de `users.users` ne recoit pas de session Django locale.
- Un utilisateur present avec `enabled = false` est refuse.

## Modele de securite

Le modele est :

1. `Keycloak` prouve l'identite ;
2. `AM` recoit cette identite ;
3. `AM` controle `users.users` ;
4. `AM` ouvre une session Django locale, refuse l'acces ou redirige vers le provisioning.

Regle centrale :

- authentification != autorisation.

Consequences :

- une connexion Google valide dans `Keycloak` ne donne pas automatiquement acces a `AM` ;
- seuls les utilisateurs explicitement acceptes dans `users.users` peuvent entrer dans `AM`.

## Flux cible

### PROD

1. L'utilisateur arrive sur `AM`.
2. `AM` redirige vers le service d'authentification externe / `Keycloak`.
3. L'utilisateur s'authentifie.
4. L'utilisateur revient sur `AM`.
5. `AM` valide le callback.
6. `AM` lit `users.users` par UUID `Keycloak`.
7. Si l'utilisateur existe et est actif, `AM` ouvre une session Django.
8. Si l'utilisateur est inconnu, `AM` affiche une page intermediaire de provisioning avec lien et redirection automatique vers `home`.
9. Si l'utilisateur est refuse pour une autre raison, `AM` garde une session anonyme et affiche une erreur claire.

### DEV

1. L'utilisateur arrive sur `AM`.
2. `AM` redirige vers `auth_mock`.
3. `auth_mock` retourne un payload signe.
4. `AM` valide le callback.
5. `AM` lit `users.users` par UUID `Keycloak`.
6. Si l'utilisateur existe et est actif, `AM` ouvre une session Django.
7. Sinon, `AM` garde une session anonyme et affiche une erreur claire.

## Choix techniques actuels

- framework : `Django` ;
- gestionnaire Python : `uv` ;
- base cible : `PostgreSQL` ;
- runtime local : `Docker` ;
- app d'entree auth : `app_main` ;
- strategie de session : session Django locale ;
- reference utilisateur : lecture seule SQL dans `users.users` ;
- auth DEV : `auth_mock` ;
- auth PROD : `Keycloak` externe.

L'implementation evite volontairement de recreer une source de verite locale des comptes.

## Contrat minimal d'identite

Identite attendue apres authentification :

- `external_id` : UUID `Keycloak` ;
- `username` ;
- `email` ;
- `first_name` ;
- `last_name`.

Seul `external_id` est autoritatif pour le rapprochement.

## Session AM

Les noms de session sont propres a Animation Messe :

- utilisateur local : `am_user` ;
- etat OIDC : `am_keycloak_state` ;
- cible de provisioning : `am_home_provision_target` ;
- provisioning en attente : `am_pending_provision` ;
- diagnostic Keycloak : `am_keycloak_diagnostic`.

Ces noms evitent les collisions avec les autres applications CARThographie.

## Test local DEV

Configuration locale validee :

- `AM` tourne dans Docker ;
- `auth_mock` tourne dans Docker ;
- `AM` rejoint le reseau Docker backend partage ;
- `AM` lit l'instance PostgreSQL partagee du projet CARThographie.

Pre-requis :

- le reseau backend externe existe ;
- PostgreSQL partage est demarre ;
- `users.users` existe dans la base `carthographie` ;
- l'utilisateur SQL configure pour `AM` peut lire `users.users` ;
- `AUTH_MOCK_USERS_JSON` contient les comptes de test attendus ;
- les UUID de connexion reussie existent dans `users.users` ;
- l'UUID desactive existe avec `enabled = false` ;
- l'UUID inconnu reste volontairement absent de `users.users` ;
- les roles locaux dans `am.m_member_roles` sont coherents avec les profils de test.

Variables locales utiles :

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `AUTH_MOCK_SHARED_SECRET`
- `AUTH_MOCK_USERS_JSON`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

Notes pour PostgreSQL partage :

- utiliser le reseau backend partage attendu par `compose.dev.yaml` ;
- utiliser `DB_HOST=postgres` si cet alias existe ;
- sinon utiliser l'alias expose par le projet PostgreSQL partage.

Demarrage local de base :

```bash
cp .env.dev.example .env.dev
docker compose -f compose.yaml -f compose.dev.yaml up --build
docker compose exec web python manage.py sync_auth_mock_accounts
```

## Preparation Docker PROD

La preparation production est separee en :

- `compose.yaml` : socle partage ;
- `compose.prod.yaml` : surcharge production ;
- `.env.prod` : variables de production non versionnees ;
- `.env.prod.example` : gabarit versionne.

Attentes reseau :

- `AM` rejoint le reseau backend partage pour atteindre PostgreSQL ;
- `AM` rejoint le reseau proxy partage pour etre expose par `Traefik` ;
- le service de production est route par nom d'hote, par exemple `am.carthographie.fr`.

Demarrage production :

```bash
cp .env.prod.example .env.prod
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml pull
docker compose --env-file .env.prod -f compose.yaml -f compose.prod.yaml up -d
```

Notes :

- `--env-file .env.prod` est requis pour l'interpolation Compose (`COMPOSE_PROJECT_NAME`, reseaux, ports, etc.) ;
- `env_file: .env.prod` injecte seulement les variables dans le conteneur ;
- le projet Compose de production doit etre nomme `am`, typiquement avec `COMPOSE_PROJECT_NAME=am`.

Limite actuelle :

- l'override production retire `auth_mock` et durcit Django/conteneur ;
- le vrai flux interactif `Keycloak` depend de la configuration du client, du secret et des URLs de production.

## Verification manuelle DEV

1. Ouvrir `http://localhost:8000`.
2. Verifier l'etat anonyme.
3. Cliquer l'entree de simulation.
4. Choisir un utilisateur admin et verifier l'interface `Admin`.
5. Se deconnecter et verifier le retour anonyme.
6. Choisir un moderateur et verifier les droits `Moderator` sans `Admin`.
7. Se deconnecter et verifier le retour anonyme.
8. Choisir un membre simple et verifier l'interface membre.
9. Se deconnecter et verifier le retour anonyme.
10. Choisir un utilisateur desactive et verifier le refus clair.
11. Choisir un utilisateur inconnu et verifier le parcours de refus ou provisioning.

## Provisioning production

Variables attendues :

- `HOME_PROVISION_START_URL=https://carthographie.fr/provision/start`
- `HOME_PROVISION_APP_ID=am`
- `HOME_PROVISION_SHARED_SECRET_FILE=/opt/stacks/_shared/secrets/home-provisioning/redirect_am_secret.txt`
- `HOME_PROVISION_RETURN_URL=https://am.carthographie.fr/provision/complete/`

Separation des responsabilites :

- `KEYCLOAK_LOGOUT_REDIRECT_URI` sert uniquement au logout ;
- `HOME_PROVISION_RETURN_URL` sert uniquement au retour signe post-provisioning ;
- `AM` ne doit jamais reutiliser l'URL de logout comme retour de provisioning.

Si `HOME_PROVISION_SHARED_SECRET_FILE` n'est pas defini, `AM` essaie aussi le chemin contractuel par defaut :

```text
/opt/stacks/_shared/secrets/home-provisioning/redirect_am_secret.txt
```

Si l'URL de provisioning signee ne peut pas etre construite, `AM` ne doit pas renvoyer vers la home generique, car elle ne declenche pas le provisioning. Il doit garder l'utilisateur anonyme et afficher une erreur de configuration.

## Retour post-provisioning

- Apres un callback Keycloak valide pour un utilisateur local inconnu, `AM` stocke un etat temporaire `am_pending_provision` avec l'`external_id` valide.
- `cARThographie` doit renvoyer le navigateur vers l'URL signee exacte `HOME_PROVISION_RETURN_URL`.
- Pour `AM`, cette URL doit cibler `/provision/complete/`.
- `AM` refuse toute `HOME_PROVISION_RETURN_URL` pointant vers `/`, `/auth/callback/`, `/login/` ou un endpoint non dedie.
- `/provision/complete/` n'est pas un callback OIDC : c'est une reprise locale ou `AM` retente la lecture `users.users` avec l'`external_id` stocke dans la meme session navigateur.
- Si l'utilisateur existe alors et est actif, `AM` ouvre la session locale sans second aller-retour Keycloak.

## Diagnostic Keycloak

- Apres un echec de callback Keycloak, `AM` stocke un diagnostic de session consultable sur `/login/diagnostic/`.
- La page affiche l'etape en echec, le statut HTTP, les erreurs Keycloak publiques, les reglages client publics et les indicateurs de presence des secrets.
- Un `token_exchange` en `401 invalid_client` ou `401 unauthorized_client` pointe souvent vers le secret client, l'ID client ou le mode confidential client.
- Un `token_exchange` en `400 invalid_grant` pointe souvent vers la redirect URI, un code expire/consomme ou une derive d'horloge.
- `AM` ne doit jamais exposer le secret client, le code OAuth, l'access token, les cookies ou les payloads sensibles complets dans cette page.

## Cas de refus attendus

- UUID utilisateur absent de `users.users`.
- Utilisateur present avec `enabled = false`.
- Signature de callback invalide.
- PostgreSQL indisponible.
- `auth_mock` indisponible.

## Priorites de durcissement

- Validation stricte des callbacks.
- Rapprochement utilisateur strict par UUID.
- Separation explicite entre identite externe et autorisation locale.
- Aucun secret versionne.
- Reglages Django production stricts.
- Journaux utiles pour succes/echec de connexion.
- Aucun fallback discret qui donnerait acces sur donnees incompletes.

En production, le minimum attendu inclut :

- `DEBUG=False` ;
- `ALLOWED_HOSTS` strict ;
- `CSRF_TRUSTED_ORIGINS` strict ;
- cookies securises ;
- reglages de deploiement compatibles HTTPS.

## Ce que les agents ne doivent pas faire

- Ne pas basculer l'autorisation de l'UUID vers l'email.
- Ne pas auto-accepter un utilisateur authentifie par `Keycloak`.
- Ne pas ecrire dans `users.users`.
- Ne pas supposer que les groupes Keycloak sont la source de verite metier sans arbitrage explicite.
- Ne pas disperser la logique auth dans les apps metier quand `app_main` suffit.
- Ne pas introduire de secrets de production dans des fichiers suivis.

## Hors perimetre

- Gestion detaillee des roles de groupe.
- Affectations planning et celebrations.
- Permissions metier fines.
- Rafraichissement avance des tokens.
- Politique multi-provider.
- Guide complet reverse proxy / VPS.

## Regle de travail

Toute modification Django touchant l'authentification doit rester alignee avec ce document.
