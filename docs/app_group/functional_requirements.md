# app_group — Functional Requirements

`app_group` porte les groupes AM, leurs rôles internes, leurs membres, les Membres AM, les paramètres de groupe et le recueil de chants utilisé par le groupe.

Sources fonctionnelles principales :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/SFD-03-chants.md`
- `docs/SFD-04-celebrations.md`

---

# 1. Rôle fonctionnel

`app_group` est responsable :

- des groupes communs à AM et LSS ;
- de l’accès AM à un groupe ;
- des rôles de groupe Responsable et Membre ;
- des Membres AM sans compte ;
- des demandes d’accès ;
- des consentements liés aux Membres AM ;
- des paramètres de groupe utiles au planning et aux célébrations ;
- du recueil de chants du groupe ;
- des tags de groupe appliqués aux chants ;
- des lieux habituels du groupe ;
- des durées de conservation configurables par groupe.

`app_group` ne possède pas :

- l’identité externe des utilisateurs ;
- les rôles globaux `admin` et `moderator` ;
- les célébrations elles-mêmes ;
- les lignes et cellules de planning ;
- les textes sources LSS ;
- les caches AELF.

---

# 2. Groupes et rôles

Les groupes AM et LSS représentent une même entité fonctionnelle de groupe.

Avoir accès à AM pour un groupe implique que le groupe soit disponible dans LSS.

Faire partie d’un groupe dans LSS ne donne pas automatiquement accès à AM.

Les rôles de groupe AM sont :

- Responsable ;
- Membre ;
- Membre AM.

Un groupe doit toujours conserver au moins un Responsable.

Un Responsable peut gérer les membres, les Membres AM, les paramètres du groupe et les validations administratives prévues par les apps métier.

Un Membre participe à la vie courante du groupe sans disposer des pouvoirs administratifs.

Un Membre AM représente une personne réelle sans compte CARThographie.

---

# 3. Membres AM et consentement

La création d’un Membre AM est initiée par un Responsable.

Elle nécessite :

- une demande ;
- un email d’information ;
- un consentement explicite ;
- un secret personnel permettant un retrait ultérieur.

Un Membre AM :

- ne peut pas se connecter ;
- ne peut pas être Responsable ;
- ne possède aucun droit applicatif ;
- peut être affecté à une célébration ou à une ligne de planning.

Le secret personnel ne doit jamais être stocké en clair.

Le retrait de consentement ne doit jamais être déclenché par une simple ouverture de lien : il doit passer par une confirmation explicite.

---

# 4. Recueil et tags de groupe

`app_group` porte la partie AM de l’usage des chants par un groupe.

Le recueil du groupe est le sous-ensemble de chants LSS que le groupe utilise couramment.

Les tags de groupe :

- appartiennent à un seul groupe ;
- peuvent avoir le même nom dans plusieurs groupes sans représenter le même objet ;
- servent à qualifier les chants et leurs blocs/couplets ;
- sont utilisés par les gabarits et les blocs chants de célébration.

`app_group` ne copie jamais les textes de chants LSS comme contenu métier officiel.

La suppression d’un chant dans LSS retire le chant des usages courants et sélections futures, mais ne supprime pas silencieusement les blocs déjà présents dans des célébrations.

---

# 5. Règles fonctionnelles

**GROUP-ROLE-01** — Un groupe AM utilise les rôles Responsable, Membre et Membre AM.

**GROUP-ROLE-02** — Un groupe doit toujours avoir au moins un Responsable.

**GROUP-ROLE-03** — Les rôles de groupe sont distincts des rôles globaux de `app_member`.

**GROUP-ACCESS-01** — L’accès LSS à un groupe ne donne pas automatiquement accès AM.

**GROUP-ACCESS-02** — L’accès AM implique l’accès au même groupe côté LSS.

**GROUP-AM-01** — Un Membre AM est une personne réelle sans compte CARThographie.

**GROUP-AM-02** — Un Membre AM ne possède aucun droit applicatif.

**GROUP-AM-03** — La création d’un Membre AM nécessite un consentement explicite.

**GROUP-AM-04** — Le Membre AM doit pouvoir retirer son consentement via un secret personnel vérifiable.

**GROUP-SONG-01** — Le recueil du groupe contient les chants LSS utilisés couramment par le groupe.

**GROUP-SONG-02** — Les tags de groupe appartiennent exclusivement à leur groupe.

**GROUP-SONG-03** — Les tags de groupe peuvent piloter la sélection par défaut des blocs/couplets.

**GROUP-SONG-04** — Retirer un chant du recueil ne modifie pas les célébrations existantes.

**GROUP-PARAM-01** — Les lieux habituels sont des suggestions et ne bloquent pas la saisie libre.

**GROUP-PARAM-02** — La durée de conservation des célébrations est paramétrée au niveau du groupe, dans la limite fonctionnelle définie par `SFD-04`.

---

# 6. Points encore à spécifier

1. modèle exact des groupes communs AM/LSS et frontière de synchronisation ;
2. workflow complet de demande d’accès AM pour un membre déjà présent dans LSS ;
3. effet exact du retrait de consentement d’un Membre AM sur les affectations historiques ;
4. structure technique des tags appliqués aux chants et aux blocs/couplets ;
5. pouvoirs éventuels d’un modérateur global sur les groupes.
