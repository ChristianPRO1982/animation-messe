# app_group — Functional Requirements

`app_group` porte l'environnement AM des groupes communs, leurs droits internes
propres à AM, les Membres AM, les paramètres durables du groupe et le recueil
de chants utilisé par le groupe.

Sources fonctionnelles principales :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/SFD-02-planning.md`
- `docs/SFD-03-chants.md`
- `docs/SFD-04-celebrations.md`

Contrat BDD cible :

- `docs/app_group/models.md`

---

# 1. Rôle fonctionnel

`app_group` est responsable :

- de l’extension AM des groupes communs à CARThographie, AM et LSS ;
- de l’accès AM à un groupe pour les membres avec compte ;
- du rôle AM Responsable impression ;
- des Membres AM sans compte ;
- des demandes d’accès AM pour les membres déjà présents dans le groupe commun ;
- des consentements liés aux Membres AM ;
- des paramètres de groupe utiles au planning ;
- des lieux habituels du groupe ;
- des fonctions d’animation possibles ;
- des états de planning configurables ;
- des règles régulières de génération de célébrations ;
- des dates particulières ;
- des durées de conservation configurables par groupe ;
- du recueil de chants du groupe ;
- des tags de groupe appliqués aux chants et aux blocs.

`app_group` ne possède pas :

- l’identité externe des utilisateurs ;
- les groupes communs CARThographie ;
- l’appartenance commune des utilisateurs aux groupes ;
- le rôle Responsable porté par le groupe commun ;
- le rôle global Administrateur porté par `app_member` ;
- les célébrations elles-mêmes ;
- les cellules réelles de planning, portées par `app_celebration` ;
- les gabarits de célébration ou d’impression ;
- les textes sources LSS ;
- les caches AELF.

---

# 2. Groupes et accès AM

Les groupes AM et LSS représentent une même entité fonctionnelle de groupe,
portée par CARThographie dans le schéma `common`.

La table commune `common.g_groups` est la source de vérité du groupe.

La table cible `am.g_group` est une extension 1–1 de `common.g_groups` et ne
stocke que les paramètres propres à AM.

Avoir accès à AM pour un groupe implique que le groupe soit disponible dans LSS.

Faire partie du groupe commun ne donne pas automatiquement accès à AM.

Pour un membre avec compte, l’appartenance au groupe commun est portée par
`common.g_group_user`.

L’accès AM est porté par `common.g_group_user.am_access`.

La présence d’une ligne `am.g_group` signifie que le groupe dispose de son environnement AM.

Le mode ouvert ou fermé est porté par `common.g_groups.status`. Toute nouvelle
fonctionnalité est privée par défaut, sauf décision explicite de la rendre
utilisable dans l’espace public d’un groupe ouvert.

---

# 3. Membres et rôles de groupe

Les statuts fonctionnels visibles dans un groupe AM sont :

- Membre ;
- Membre AM ;
- Responsable ;
- Responsable impression.

En BDD, le rôle Responsable est porté par
`common.g_group_user.is_group_admin`.

Les rôles AM assignés qui ajoutent des droits propres à AM sont :

- Responsable impression.

Un Membre avec compte est représenté par son appartenance dans
`common.g_group_user`. Il ne faut pas créer un rôle `Membre` redondant.

Un Membre avec compte utilisable par AM possède aussi une ancre technique
`am.g_group_member` lorsque `common.g_group_user.am_access = TRUE`. Cette ancre
sert aux fonctions, au planning et aux célébrations, mais ne remplace pas la
source de vérité commune.

Un Membre AM est représenté par une appartenance `member_kind = am` et par son profil Membre AM.

Un groupe doit toujours conserver au moins un Responsable commun
`is_group_admin = TRUE`.

Un Responsable peut gérer les membres, les Membres AM, les paramètres du groupe et les validations administratives prévues par les apps métier.

Un Responsable impression peut gérer les feuilles de messe selon les règles de `app_celebration`, sans droit sur le planning, le déroulé, la validation ou l’administration du groupe.

Les rôles de groupe sont distincts du rôle global Administrateur de `app_member`.

Dans l'interface, un Membre avec compte doit être affiché par son prénom et son
nom issus de l'annuaire utilisateur lorsque ces informations sont disponibles.
L'UUID technique `member_id` ne doit pas être affiché dans les listes de
consultation ou de gestion. Il peut rester présent dans les champs techniques
nécessaires aux formulaires POST. L'email n'est pas affiché dans `app_group`.

Les listes de personnes doivent rendre lisibles les statuts utiles :

- accès AM ;
- Responsable ;
- Responsable impression ;
- fonctions affectées.

Un Membre AM est affiché par son prénom, son nom, son titre éventuel, son état
de consentement et ses fonctions. Il ne reçoit jamais de badge donnant des
droits applicatifs.

Une demande de rejoindre le groupe depuis AM utilise le workflow commun
`common.g_group_user_ask_to_join`. Si elle est acceptée depuis AM, elle crée
l’appartenance commune et active aussi `am_access`.

Une personne déjà membre du groupe commun mais sans accès AM peut demander
uniquement l’accès AM. Cette demande relève de `app_group` et sa validation met
à jour `common.g_group_user.am_access`.

Depuis la page de gestion des membres, un Responsable peut retirer un membre de
l'espace AM sans supprimer son appartenance au groupe commun. Ce retrait met
`common.g_group_user.am_access` à `FALSE` et supprime l'ancre technique
`am.g_group_member` du membre avec compte si elle existe.

Depuis la même page, un Responsable peut retirer un membre du groupe global.
Ce retrait supprime l'appartenance `common.g_group_user` et supprime aussi
l'ancre `am.g_group_member` du membre avec compte si elle existe.

Ces deux retraits protègent le dernier Responsable : un groupe doit toujours
conserver au moins une appartenance `is_group_admin = TRUE`.

L'espace de gestion des groupes AM est exposé sous `/groups/manage/`.
Cette route est réservée aux utilisateurs authentifiés pouvant gérer au moins
un groupe :

- Administrateur global AM, qui voit tous les groupes communs ;
- Responsable d'au moins un groupe commun, qui ne voit que ses groupes.

Le lien vers cet espace peut être présenté par `app_main` :

- dans la section Administration du profil pour les Administrateurs globaux ;
- dans l'encadré résumé de la page d'accueil pour les Administrateurs globaux
  et les Responsables d'au moins un groupe.

La page publique `/groups/` reste distincte de l'espace de gestion.

Elle affiche les groupes disposant d'un espace AM actif, triés avec les groupes
de l'utilisateur en premier, puis les groupes ouverts, puis les autres groupes,
chaque bloc étant ordonné alphabétiquement.

Depuis `/groups/`, un utilisateur authentifié peut :

- accéder à un groupe lorsqu'il possède `am_access = TRUE`, lorsqu'il est
  Responsable du groupe ou lorsqu'il est Administrateur global ;
- demander son rattachement lorsqu'il n'est pas encore membre et qu'aucune
  demande n'est en attente ;
- voir l'état `Demande de rattachement en attente` lorsqu'une demande existe.

Les visiteurs anonymes peuvent consulter la liste des groupes AM actifs, mais
ne peuvent ni entrer dans un groupe ni demander un rattachement sans se
connecter.

La page `/groups/<id>/` est la page de pilotage synthétique d'un groupe.
Elle ne doit pas devenir une page fourre-tout contenant tous les formulaires de
gestion. Elle présente l'état du groupe, les listes utiles à la décision et des
accès vers les actions ou pages dédiées.

Cette page est accessible à un Membre ayant l'accès AM, à un Responsable du
groupe et à un Administrateur global. L'interface y est contextuelle :

- un Membre simple voit l'état du groupe et les listes utiles, sans blocs de
  gestion ;
- un Responsable ou un Administrateur global voit aussi les blocs de navigation
  vers les pages de gestion et les liens de demandes en cours ;
- un Responsable impression ne reçoit pas, par ce rôle seul, de droits de
  gestion `app_group`.

L'encadré résumé de `/groups/<id>/` est une zone de lecture seule. Il doit
afficher, avec des éléments séparés et lisibles :

- l'état de l'espace AM, actif ou inactif ;
- le statut public ou privé du groupe commun ;
- le nombre de membres avec compte ;
- le nombre de demandes, avec un lien contextuel `🆕` vers
  `/groups/<id>/members/` lorsque ce nombre est supérieur à zéro ;
- le nombre de Membres AM ;
- le nombre de chants dans le recueil du groupe.

Le lien contextuel des demandes doit aussi être affiché sous le titre du groupe
sur `/groups/<id>/` lorsqu'au moins une demande est en attente. Il pointe vers
la page `Membres`, car cette page centralise les demandes de rattachement au
groupe commun et les demandes d'accès AM des membres avec compte.

Le panneau outils de `/groups/<id>/` doit proposer un accès vers la gestion des
chants ou du recueil du groupe.

Le corps de `/groups/<id>/` doit privilégier des blocs de consultation et de
navigation. Les blocs historiques `Synthèse` et `Responsables communs` ne sont
pas la cible UX. Ils doivent être remplacés par :

- `Liste des membres` ;
- `Liste des responsables` ;
- `Liste des Membres AM` ;
- un bloc d'actions de modification proposant des accès dédiés pour gérer les
  membres, les responsables, les Membres AM, les fonctions et les titres Membre
  AM.

Un bloc général de paramétrage doit regrouper les accès dédiés sans afficher
tous les formulaires directement :

- `Paramètres du calendrier` : états planning, règles régulières, dates
  particulières ;
- `Paramètres du groupe` : paramètres généraux, lieux.

## Pages de gestion dédiées

Les boutons et accès de `/groups/<id>/` doivent pointer vers des pages dédiées
de gestion. Ces routes sont une cible UX à implémenter progressivement : leur
présence dans ce document ne signifie pas qu'elles existent déjà dans le code.

Le découpage cible est volontairement fin afin que chaque écran reste lisible :

- `/groups/<id>/members/` : membres avec compte, demandes de rattachement au
  groupe commun, demandes d'accès AM et actions liées aux membres ;
- `/groups/<id>/responsables/` : Responsables communs portés par
  `common.g_group_user.is_group_admin` ;
- `/groups/<id>/am-members/` : Membres AM, demandes de création, consentements,
  refus et expiration ;
- `/groups/<id>/functions/` : fonctions possibles du groupe et affectations aux
  personnes ;
- `/groups/<id>/am-member-titles/` : titres proposés pour les Membres AM ;
- `/groups/<id>/calendar/states/` : états planning configurables ;
- `/groups/<id>/calendar/regular-rules/` : règles régulières de génération ;
- `/groups/<id>/calendar/special-dates/` : dates particulières ;
- `/groups/<id>/settings/` : paramètres généraux de l'espace AM du groupe ;
- `/groups/<id>/locations/` : lieux habituels ;
- `/groups/<id>/songs/` : recueil, chants LSS, tags et blocs sélectionnés par
  défaut.

Les formulaires longs, les listes éditables et les actions de masse doivent
vivre sur ces pages dédiées. Le tableau de bord `/groups/<id>/` conserve
seulement les indicateurs, les listes principales en lecture ou consultation
rapide, et les boutons de navigation vers ces écrans.

## Workflows utilisateur actuels

### Consultation publique et demande de rattachement

1. Un visiteur ouvre `/groups/` et voit les groupes AM actifs.
2. S'il est connecté et non membre d'un groupe, il peut envoyer une demande de
   rattachement.
3. La demande crée une ligne `common.g_group_user_ask_to_join`.
4. Un Responsable traite la demande depuis `/groups/<id>/members/`.
5. En cas d'acceptation, `common.g_group_user` est créé ou mis à jour avec
   `am_access = TRUE`, et l'ancre technique `am.g_group_member` est créée si
   elle manque.

### Retrait d'un membre

1. Un Responsable ouvre `/groups/<id>/members/`.
2. `Retirer de l'espace AM` enlève seulement l'accès AM et l'ancre technique
   AM du membre.
3. `Retirer du groupe` enlève l'appartenance commune et l'ancre technique AM.
4. Si le membre ciblé est le dernier Responsable du groupe, l'action est
   refusée.

### Entrée dans un groupe

1. Un utilisateur connecté voit le bouton d'accès au groupe sur `/groups/` s'il
   possède `am_access = TRUE`, s'il est Responsable du groupe ou s'il est
   Administrateur global.
2. Le bouton ouvre `/groups/<id>/`.
3. Un utilisateur sans accès AM, non Responsable et non Administrateur global
   reçoit un refus d'accès.

### Pilotage par rôle

1. Un Membre avec accès AM consulte le tableau de bord synthétique du groupe.
2. Un Responsable ou Administrateur global consulte le même tableau de bord,
   avec les blocs supplémentaires de gestion.
3. Les pages dédiées sous `/groups/<id>/.../` restent réservées aux
   Responsables et Administrateurs globaux.
4. Les demandes en cours sont signalées par un lien contextuel `🆕` uniquement
   aux Responsables et Administrateurs globaux, car elles mènent vers une page
   de gestion.

---

# 4. Membres AM et consentement

La création d’un Membre AM est initiée par un Responsable.

Elle nécessite :

- une demande ;
- un email d’information ;
- un consentement explicite ;
- un secret personnel permettant un retrait ultérieur.

Un Membre AM :

- ne peut pas se connecter ;
- ne peut pas être Responsable ;
- ne peut pas être Responsable impression ;
- ne possède aucun droit applicatif ;
- peut recevoir des fonctions ;
- peut être affecté à une célébration ou à une cellule de planning.

Le secret personnel ne doit jamais être stocké en clair.

Le retrait de consentement ne doit jamais être déclenché par une simple ouverture de lien : il doit passer par une confirmation explicite.

La fusion future d’un Membre AM vers un compte CARThographie doit conserver l’ancre `g_group_member.ggm_id`.

---

# 5. Paramètres durables pour le planning

`app_group` possède les paramètres durables utilisés par `app_planning` :

- états de planning ;
- fonctions d’animation ;
- fonctions possibles par personne ;
- lieux habituels ;
- règles régulières de célébrations ;
- dates particulières.

`app_planning` lit ces paramètres, génère des célébrations via `app_celebration` et affiche le tableau ou le calendrier.

Il ne doit pas créer de stockage parallèle ni de tables `p_*` en V1.

Les cellules réelles du planning appartiennent à la célébration, pas à `app_group`.

---

# 6. Recueil et tags de groupe

`app_group` porte la partie AM de l’usage des chants par un groupe.

Le recueil du groupe est le sous-ensemble de chants LSS que le groupe utilise couramment.

Les tables physiques du recueil utilisent le préfixe `s_*` dans le schéma `am`, mais restent définies dans `app_group`.

Il n’existe pas d’application Django `app_song` ou `app_chant`.

Les tags de groupe :

- appartiennent à un seul groupe ;
- sont stockés dans `common.group_tags` pour rester partagés avec LSS ;
- peuvent avoir le même nom dans plusieurs groupes sans représenter le même objet ;
- servent à qualifier les chants et leurs blocs ;
- sont utilisés par les gabarits et les blocs chants de célébration.

`app_group` ne copie jamais les textes, titres, descriptions, types ou ordre des blocs LSS comme contenu métier officiel.

La suppression d’un chant dans LSS retire le chant des usages courants et sélections futures, mais ne supprime pas silencieusement les blocs déjà présents dans des célébrations.

---

# 7. Contrats vers les autres apps

`app_member` fournit les profils globaux AM et le rôle Administrateur.

`app_planning` consomme les paramètres durables du groupe, mais ne possède pas de tables de planning en V1.

`app_celebration` consomme les groupes, membres, fonctions, lieux et tags de groupe pour créer les célébrations, leurs participants effectifs, leur déroulé, leurs validations, leurs gabarits et leurs feuilles.

Les gabarits de célébration et les gabarits d’impression appartiennent à `app_celebration`, même lorsqu’ils sont propres à un groupe.

---

# 8. Règles fonctionnelles

**GROUP-ROLE-01** — Un groupe AM distingue les statuts Membre, Membre AM, Responsable et Responsable impression.

**GROUP-ROLE-02** — Responsable est porté par `common.g_group_user.is_group_admin`; Responsable impression est un rôle AM propre à `app_group`.

**GROUP-ROLE-03** — Un Membre avec compte est représenté par son appartenance commune au groupe, sans rôle `Membre` redondant.

**GROUP-ROLE-04** — Un groupe doit toujours avoir au moins un Responsable.

**GROUP-ROLE-05** — Les rôles de groupe sont distincts du rôle global Administrateur de `app_member`.

**GROUP-ACCESS-01** — L’appartenance au groupe commun ne donne pas automatiquement accès AM.

**GROUP-ACCESS-02** — L’accès AM implique l’appartenance au groupe commun.

**GROUP-ACCESS-03** — L'espace `/groups/manage/` est accessible aux Administrateurs globaux et aux Responsables d'au moins un groupe, avec une liste filtrée selon leurs droits.

**GROUP-ACCESS-04** — La page `/groups/<id>/` est une page de pilotage synthétique : elle expose l'état du groupe, les listes principales et des accès vers les actions dédiées, sans concentrer tous les formulaires de gestion.

**GROUP-ACCESS-05** — Un Membre avec `am_access = TRUE`, un Responsable du groupe ou un Administrateur global peut entrer dans `/groups/<id>/`; les pages dédiées de gestion restent réservées aux Responsables et Administrateurs globaux.

**GROUP-ACCESS-06** — Retirer un membre de l'espace AM désactive `am_access` et supprime son ancre `am.g_group_member`, sans supprimer son appartenance commune.

**GROUP-ACCESS-07** — Retirer un membre du groupe supprime son appartenance `common.g_group_user` et son ancre `am.g_group_member` éventuelle.

**GROUP-UI-01** — Les formulaires longs et les listes éditables de gestion d'un groupe doivent vivre dans des pages dédiées sous `/groups/<id>/.../`, afin que le tableau de bord groupe reste synthétique.

**GROUP-UI-02** — Les listes visibles de personnes affichent prénom et nom lorsque l'annuaire les fournit, jamais l'UUID technique ni l'email.

**GROUP-UI-03** — Les listes de personnes affichent les badges de statut utiles : accès AM, Responsable, Responsable impression et fonctions affectées.

**GROUP-AM-01** — Un Membre AM est une personne réelle sans compte CARThographie.

**GROUP-AM-02** — Un Membre AM ne possède aucun droit applicatif.

**GROUP-AM-03** — La création d’un Membre AM nécessite un consentement explicite.

**GROUP-AM-04** — Le Membre AM doit pouvoir retirer son consentement via un secret personnel vérifiable.

**GROUP-AM-05** — Une fusion Membre AM vers compte CARThographie conserve l’ancre `g_group_member.ggm_id`.

**GROUP-PLAN-01** — Les états, fonctions, lieux, règles régulières et dates particulières sont des paramètres durables du groupe.

**GROUP-PLAN-02** — `app_group` ne possède pas les cellules réelles du planning.

**GROUP-SONG-01** — Le recueil du groupe contient les chants LSS utilisés couramment par le groupe.

**GROUP-SONG-02** — Les tags de groupe appartiennent exclusivement à leur groupe.

**GROUP-SONG-03** — Les tags de groupe peuvent piloter la sélection par défaut des blocs.

**GROUP-SONG-04** — Retirer un chant du recueil ne modifie pas les célébrations existantes.

**GROUP-PARAM-01** — Les lieux habituels sont des suggestions et ne bloquent pas la saisie libre.

**GROUP-PARAM-02** — La durée de conservation des célébrations est paramétrée au niveau du groupe, dans la limite fonctionnelle définie par `SFD-04`.

---

# 9. Points encore à spécifier

1. stratégie exacte de migration depuis les tables historiques de `app_member` ;
2. workflow UI complet de demande d’accès AM pour un membre déjà présent dans LSS ;
3. effet exact du retrait de consentement d’un Membre AM sur les affectations historiques ;
4. forme finale des services de synchronisation du recueil avec LSS ;
5. règles de trace des interventions sensibles d’un Administrateur.
