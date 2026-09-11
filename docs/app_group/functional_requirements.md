# app_group — Functional Requirements

`app_group` porte les groupes AM, leurs rôles internes, leurs membres, les Membres AM, les paramètres durables du groupe et le recueil de chants utilisé par le groupe.

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

- de l’extension AM des groupes communs à AM et LSS ;
- de l’accès AM à un groupe ;
- des rôles de groupe Responsable et Responsable impression ;
- de l’appartenance de base des Membres avec compte ;
- des Membres AM sans compte ;
- des demandes d’accès ;
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
- le rôle global Administrateur porté par `app_member` ;
- les célébrations elles-mêmes ;
- les cellules réelles de planning, portées par `app_celebration` ;
- les gabarits de célébration ou d’impression ;
- les textes sources LSS ;
- les caches AELF.

---

# 2. Groupes et accès AM

Les groupes AM et LSS représentent une même entité fonctionnelle de groupe.

La table cible `am.g_group` est une extension 1–1 de `lss.g_groups`.

Avoir accès à AM pour un groupe implique que le groupe soit disponible dans LSS.

Faire partie d’un groupe dans LSS ne donne pas automatiquement accès à AM.

La présence d’une ligne `am.g_group` signifie que le groupe dispose de son environnement AM.

Le mode ouvert ou fermé est un paramètre du groupe. Toute nouvelle fonctionnalité est privée par défaut, sauf décision explicite de la rendre utilisable dans l’espace public d’un groupe ouvert.

---

# 3. Membres et rôles de groupe

Les statuts fonctionnels visibles dans un groupe AM sont :

- Membre ;
- Membre AM ;
- Responsable ;
- Responsable impression.

En BDD, les rôles de groupe assignés qui ajoutent des droits sont :

- Responsable ;
- Responsable impression.

Un Membre avec compte est représenté par son appartenance au groupe. Il ne faut pas créer un rôle `Membre` redondant.

Un Membre AM est représenté par une appartenance `member_kind = am` et par son profil Membre AM.

Un groupe doit toujours conserver au moins un Responsable.

Un Responsable peut gérer les membres, les Membres AM, les paramètres du groupe et les validations administratives prévues par les apps métier.

Un Responsable impression peut gérer les feuilles de messe selon les règles de `app_celebration`, sans droit sur le planning, le déroulé, la validation ou l’administration du groupe.

Les rôles de groupe sont distincts du rôle global Administrateur de `app_member`.

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

**GROUP-ROLE-02** — Seuls Responsable et Responsable impression sont des rôles assignés ajoutant des droits.

**GROUP-ROLE-03** — Un Membre avec compte est représenté par son appartenance au groupe, sans rôle `Membre` redondant.

**GROUP-ROLE-04** — Un groupe doit toujours avoir au moins un Responsable.

**GROUP-ROLE-05** — Les rôles de groupe sont distincts du rôle global Administrateur de `app_member`.

**GROUP-ACCESS-01** — L’accès LSS à un groupe ne donne pas automatiquement accès AM.

**GROUP-ACCESS-02** — L’accès AM implique l’accès au même groupe côté LSS.

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
