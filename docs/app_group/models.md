# app_group — Modèle BDD

Ce document est le contrat BDD canonique de `app_group` pour la V1.

Il consolide les décisions issues des SFD et des fichiers de travail
`docs/TABLES/*`. Les SFD restent prioritaires en cas de contradiction
fonctionnelle.

Sources principales :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/SFD-02-planning.md`
- `docs/SFD-03-chants.md`
- `docs/SFD-04-celebrations.md`
- `docs/app_member/models.md`

---

# 1. Frontière

`app_group` possède :

- l'extension AM des groupes communs LSS/AM ;
- l'appartenance AM aux groupes ;
- les rôles de groupe ;
- les Membres AM sans compte ;
- les demandes d'accès et de création de Membre AM ;
- les fonctions possibles des personnes du groupe ;
- les lieux habituels ;
- les paramètres durables consommés par le planning ;
- le recueil de chants du groupe et les sélections par tags.

`app_group` ne possède pas :

- les comptes `users.users` ;
- les groupes sources LSS ;
- les textes, titres et métadonnées éditoriales des chants LSS ;
- les célébrations réelles ;
- les cellules réelles d'une célébration ;
- les gabarits de célébration ou d'impression ;
- les caches AELF.

---

# 2. Conventions

Toutes les tables propriétaires AM sont dans le schéma :

```text
am
```

Les tables de groupes utilisent le préfixe :

```text
g_*
```

Les tables du recueil de chants, bien que déclarées dans `app_group`, utilisent
le préfixe :

```text
s_*
```

Chaque table possède une PK explicite nommée selon l'alias naturel.

Une FK reprend exactement le nom de la PK référencée. Lorsqu'une FK cible une
table externe dont la PK s'appelle `song_id` ou `verse_id`, la colonne AM garde
ce nom.

Les FK cross-schema vers `users`, `lss` ou `common` doivent exister réellement
dans PostgreSQL. Utiliser `RunSQL` lorsque Django ne sait pas produire
proprement la contrainte.

---

# 3. Dépendances externes

Ces tables ne sont pas possédées par `app_group`.

```text
users.users
    PK id
    source de vérité des comptes CARThographie

lss.g_groups
    PK group_id
    source du groupe commun LSS/AM

lss.s_songs
    PK song_id
    source de vérité des chants

lss.s_verses
    PK verse_id
    source de vérité des blocs de chants

common.tags
    PK tag_id
    tags communs partagés

common.group_tags
    PK gt_id
    tags de groupe partagés avec LSS
```

Les éventuels modèles Django représentant ces tables doivent être
`managed = False`.

`common.*` est un schéma partagé avec LSS. Les migrations Django de
`app_group` ne doivent pas créer ni modifier ces tables comme si elles étaient
propriétaires AM.

Pour l'usage AM du recueil, utiliser les tables `am.s_*` décrites plus bas. Ne
pas introduire d'application `app_song` ou `app_chant`.

---

# 4. Groupe commun LSS/AM

## `am.g_group`

```text
alias : gg
PK    : gg_id INTEGER
```

Champs :

```text
gg_id
is_open
celebration_retention_months
created_at
updated_at
```

Relations :

```text
gg_id
    -> lss.g_groups.group_id
    ON DELETE CASCADE
```

Contraintes :

```text
1 <= celebration_retention_months <= 24
```

`gg_id` reprend exactement la valeur `lss.g_groups.group_id`.

Ne pas recopier le nom, la description ou les propriétés intrinsèques du groupe
LSS dans `am.g_group`.

La présence d'une ligne `am.g_group` signifie que le groupe dispose de son
environnement AM.

---

# 5. Membres du groupe

## `am.g_group_member`

```text
alias : ggm
PK    : ggm_id
```

Champs :

```text
ggm_id
gg_id
mm_id
member_kind
joined_at
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE

mm_id
    -> am.m_member.mm_id
    ON DELETE CASCADE
```

Contraintes :

```text
member_kind IN ('account', 'am')
member_kind = 'account' => mm_id IS NOT NULL
member_kind = 'am'      => mm_id IS NULL
UNIQUE (gg_id, mm_id) pour les membres account
```

Pour un utilisateur CARThographie, l'existence d'une ligne
`g_group_member(member_kind = 'account')` signifie être Membre du groupe dans
AM. Ne pas créer de rôle `Membre` redondant.

`ggm_id` est l'ancre stable d'une personne dans un groupe. Une future fusion
Membre AM vers compte CARThographie doit conserver le même `ggm_id`.

## `am.g_am_member_title`

```text
alias : gamt
PK    : gamt_id
```

Champs :

```text
gamt_id
gg_id
label
position
is_active
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Les titres sont configurables et ordonnés par groupe. Ne pas coder en dur une
liste de titres.

## `am.g_am_member`

```text
alias : gam
PK    : gam_id
```

Champs :

```text
gam_id
ggm_id
first_name
last_name
gamt_id
consented_at
consent_version
consent_email_fingerprint
withdrawal_secret_hash
created_at
updated_at
```

Relations :

```text
ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE CASCADE

gamt_id
    -> am.g_am_member_title.gamt_id
    ON DELETE SET NULL
```

Contraintes :

```text
UNIQUE (ggm_id)
```

Un Membre AM ne possède pas de compte, ne peut pas se connecter, ne peut pas
être Responsable, ne peut pas être Responsable impression et ne possède aucun
droit applicatif.

Il peut recevoir des fonctions, apparaître dans le planning et être affecté à
des célébrations.

Le secret personnel ne doit jamais être stocké en clair.

---

# 6. Rôles de groupe

## `am.g_role`

```text
alias : gr
PK    : gr_id
```

Champs :

```text
gr_id
gg_id
code
label
position
is_system
is_active
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (gg_id, code)
```

Dans ce document, `g_role` porte les rôles assignés qui ajoutent des droits.
Membre et Membre AM restent des statuts d'appartenance, pas des lignes
`g_role`.

Rôles système V1 :

```text
responsable
responsable_impression
```

Ces rôles sont cumulables.

`responsable` donne les pouvoirs administratifs du groupe, dont les validations
du planning et des célébrations.

`responsable_impression` donne uniquement les droits liés aux feuilles de messe
après validation d'une célébration. Il ne donne aucun droit sur le planning, le
déroulé, la validation ou l'administration du groupe.

## `am.g_group_member_role`

```text
alias : ggmr
PK    : ggmr_id
```

Champs :

```text
ggmr_id
ggm_id
gr_id
created_at
```

Relations :

```text
ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE CASCADE

gr_id
    -> am.g_role.gr_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (ggm_id, gr_id)
```

Validations service :

- `g_group_member.gg_id == g_role.gg_id` ;
- un Membre AM ne reçoit aucun rôle donnant des droits ;
- un groupe conserve toujours au moins un Responsable.

Le garde-fou du dernier Responsable doit être transactionnel :
`transaction.atomic()` et verrouillage des lignes concernées avec
`select_for_update()`.

---

# 7. Fonctions et lieux

## `am.g_function`

```text
alias : gf
PK    : gf_id
```

Champs :

```text
gf_id
gg_id
name
position
is_active
auto_edit_celebration
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (gg_id, lower(trim(name)))
```

Les fonctions sont configurables par groupe. Les exemples recommandés sont
`Chantre`, `Organiste`, `Maître de chœur` et `Responsable de groupe musical`,
sans enum rigide.

`auto_edit_celebration` signifie qu'une personne attachée à une célébration
avec cette fonction peut recevoir automatiquement le droit de modification de
cette célébration, selon le service métier.

## `am.g_group_member_function`

```text
alias : ggmf
PK    : ggmf_id
```

Champs :

```text
ggmf_id
ggm_id
gf_id
created_at
```

Relations :

```text
ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE CASCADE

gf_id
    -> am.g_function.gf_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (ggm_id, gf_id)
```

Validations service :

- la fonction et la personne appartiennent au même groupe ;
- chaque Membre ou Membre AM actif dispose normalement d'au moins une fonction.

## `am.g_location`

```text
alias : gl
PK    : gl_id
```

Champs :

```text
gl_id
gg_id
name
address
position
is_active
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Un lieu habituel est une suggestion de saisie. Une célébration garde son lieu
sous forme de texte libre et ne doit pas dépendre obligatoirement de
`g_location`.

---

# 8. Demandes et consentement

## `am.g_access_request`

```text
alias : gar
PK    : gar_id
```

Champs :

```text
gar_id
gg_id
mm_id
request_type
consented_at
consent_version
created_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE

mm_id
    -> am.m_member.mm_id
    ON DELETE CASCADE
```

Contraintes :

```text
request_type IN ('join_group', 'am_access')
une seule demande active par (gg_id, mm_id)
```

`join_group` concerne un utilisateur extérieur au groupe commun.

`am_access` concerne un utilisateur déjà membre du groupe côté LSS mais pas
encore autorisé dans AM.

Les demandes sont transitoires et ne doivent pas rester actives après décision.

## `am.g_am_member_request`

```text
alias : gamr
PK    : gamr_id
```

Champs :

```text
gamr_id
gg_id
requested_by_ggm_id
first_name
last_name
email
consent_token_hash
consent_version
status
expires_at
refused_at
display_hint
purge_at
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE

requested_by_ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE SET NULL
```

Validations service :

- seul un Responsable initie la demande ;
- la demande expire après 14 jours ;
- l'acceptation crée `g_group_member(member_kind = 'am')`, puis `g_am_member`,
  puis les fonctions nécessaires, et supprime la demande ;
- l'expiration supprime les données identifiantes ;
- le refus ne crée aucun Membre AM et conserve seulement un indicateur
  pseudonymisé temporaire visible des Responsables.

L'adresse email en clair ne doit pas être conservée dans le Membre AM actif.

---

# 9. Paramètres de planning appartenant au groupe

`app_planning` orchestre et affiche le planning, mais les paramètres durables du
groupe sont stockés dans `app_group`.

## `am.g_planning_state`

```text
alias : gps
PK    : gps_id
```

Champs :

```text
gps_id
gg_id
name
color
kind
position
is_active
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Contraintes :

```text
kind IN ('selection', 'default', 'custom')
exactement un état actif kind = 'selection' par groupe
exactement un état actif kind = 'default' par groupe
```

`selection` désigne l'état retenu lors de la validation du planning.

`default` désigne l'état initial des nouvelles cellules.

Les noms et couleurs sont configurables et n'ont aucune signification métier.

Un état déjà utilisé doit être désactivé avec `is_active = FALSE` plutôt que
supprimé physiquement.

## `am.g_celebration_rule`

```text
alias : gcr
PK    : gcr_id
```

Champs :

```text
gcr_id
gg_id
parent_gcr_id
weekday
time
gl_id
position
is_active
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE

parent_gcr_id
    -> am.g_celebration_rule.gcr_id
    ON DELETE CASCADE

gl_id
    -> am.g_location.gl_id
    ON DELETE PROTECT
```

Une règle principale a `parent_gcr_id = NULL`.

Une règle liée pointe vers une règle principale du même groupe.

Contraintes et validations :

- unicité des règles actives sur `gg_id + weekday + time + gl_id` ;
- une règle liée appartient au même groupe que sa règle principale ;
- modifier ou désactiver une règle ne modifie jamais les célébrations déjà
  générées.

## `am.g_special_date_rule`

```text
alias : gsdr
PK    : gsdr_id
```

Champs :

```text
gsdr_id
gg_id
name
rule_type
collision_mode
month
day
exact_date
weekday
occurrence
is_active
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Contraintes :

```text
rule_type IN ('annual_fixed', 'one_off', 'nth_weekday')
collision_mode IN ('add', 'replace')
```

Validations service :

- `annual_fixed` utilise `month` et `day` ;
- `one_off` utilise `exact_date` ;
- `nth_weekday` utilise `month`, `weekday` et `occurrence` ;
- aucune déduction implicite n'est faite depuis le nom de la fête.

## `am.g_special_date_celebration`

```text
alias : gsdc
PK    : gsdc_id
```

Champs :

```text
gsdc_id
gsdr_id
parent_gsdc_id
time
gl_id
position
created_at
updated_at
```

Relations :

```text
gsdr_id
    -> am.g_special_date_rule.gsdr_id
    ON DELETE CASCADE

parent_gsdc_id
    -> am.g_special_date_celebration.gsdc_id
    ON DELETE CASCADE

gl_id
    -> am.g_location.gl_id
    ON DELETE PROTECT
```

`parent_gsdc_id` reproduit le mécanisme célébration principale + célébrations
liées pour une date particulière. La relation parent/enfant reste dans la même
règle spéciale.

---

# 10. Recueil de chants du groupe

LSS possède le chant. AM possède uniquement la manière dont un groupe utilise
ce chant.

Ne jamais recopier depuis LSS :

- le titre ;
- la description ;
- le texte ;
- le type ou libellé des blocs ;
- l'ordre officiel des blocs ;
- les métadonnées éditoriales.

## `am.s_song`

```text
alias : ss
PK    : ss_id
```

Champs :

```text
ss_id
gg_id
song_id
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE

song_id
    -> lss.s_songs.song_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (gg_id, song_id)
```

Cette table signifie : le chant LSS est présent dans le recueil courant du
groupe AM.

## `am.s_verse`

```text
alias : sv
PK    : sv_id
```

Champs :

```text
sv_id
ss_id
verse_id
created_at
```

Relations :

```text
ss_id
    -> am.s_song.ss_id
    ON DELETE CASCADE

verse_id
    -> lss.s_verses.verse_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (ss_id, verse_id)
```

Ne pas ajouter `position`, `order`, `type`, `label` ou `text` dans cette table.
Ces données appartiennent à LSS.

## `am.s_song_tag`

```text
alias : sst
PK    : sst_id
```

Champs :

```text
sst_id
ss_id
gt_id
created_at
```

Relations :

```text
ss_id
    -> am.s_song.ss_id
    ON DELETE CASCADE

gt_id
    -> common.group_tags.gt_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (ss_id, gt_id)
```

Validation service :

```text
s_song.gg_id == common.group_tags.gg_id
```

Il est interdit d'associer à un chant du groupe A un tag appartenant au groupe B.

## `am.s_song_tag_verse`

```text
alias : sstv
PK    : sstv_id
```

Champs :

```text
sstv_id
sst_id
sv_id
selected_by_default
created_at
updated_at
```

Relations :

```text
sst_id
    -> am.s_song_tag.sst_id
    ON DELETE CASCADE

sv_id
    -> am.s_verse.sv_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (sst_id, sv_id)
selected_by_default DEFAULT TRUE
```

Validation service :

```text
s_song_tag.ss_id == s_verse.ss_id
```

Lorsqu'un tag est associé à un chant du recueil, créer une ligne
`s_song_tag_verse` pour chaque `s_verse` existant du chant, avec
`selected_by_default = TRUE`.

---

# 11. Synchronisation LSS

Les identifiants LSS sont considérés comme stables. Ne pas créer de règle
`ON UPDATE CASCADE`.

Une modification de contenu dans LSS ne nécessite pas de mise à jour AM :
`app_group` relit LSS.

Une suppression LSS doit cascader vers les usages courants AM :

```text
lss.s_songs
    CASCADE -> am.s_song
        CASCADE -> am.s_verse
        CASCADE -> am.s_song_tag
            CASCADE -> am.s_song_tag_verse

lss.s_verses
    CASCADE -> am.s_verse
        CASCADE -> am.s_song_tag_verse
```

La suppression d'un chant du recueil supprime seulement les lignes `am.s_*`.
Elle ne supprime jamais les données LSS ni les blocs déjà présents dans des
célébrations existantes.

L'ajout d'un nouveau chant LSS ou d'un nouveau bloc LSS ne crée pas
automatiquement une ligne AM. Ce travail appartient à un service ou cron de
synchronisation séparé.

---

# 12. Contrats vers les autres apps

`app_planning` consomme :

- `g_planning_state` ;
- `g_function` ;
- `g_group_member_function` ;
- `g_location` ;
- `g_celebration_rule` ;
- `g_special_date_rule` ;
- `g_special_date_celebration`.

Il ne crée pas de tables `p_*` en V1.

`app_celebration` consomme :

- `g_group` ;
- `g_group_member` ;
- `g_function` ;
- `g_location` comme aide de saisie ;
- `common.group_tags` ;
- les références `am.s_*` pour initialiser les blocs chants.

Les célébrations, leurs participants effectifs, leurs fonctions réellement
exercées, leurs validations, leurs gabarits, leurs feuilles et leurs caches
AELF restent propriétaires de `app_celebration`.

---

# 13. Règles garanties par PostgreSQL

À viser en contrainte SQL :

- PK explicite sur chaque table ;
- FK de possession en `ON DELETE CASCADE` ;
- FK optionnelles historiques en `ON DELETE SET NULL` ;
- protection des lieux référencés par des règles de génération ;
- unicité `(gg_id, mm_id)` pour les membres avec compte ;
- unicité `(gg_id, code)` pour les rôles ;
- unicité `(ggm_id, gr_id)` pour les rôles attribués ;
- unicité `(ggm_id, gf_id)` pour les fonctions attribuées ;
- unicité `(gg_id, song_id)` pour le recueil ;
- unicité `(ss_id, verse_id)` pour les blocs référencés ;
- unicité `(ss_id, gt_id)` pour les tags du chant ;
- unicité `(sst_id, sv_id)` pour la sélection par défaut.

---

# 14. Règles garanties par services Django

À implémenter dans des services transactionnels :

- création d'un groupe avec au moins un Responsable ;
- interdiction de retirer le dernier Responsable ;
- cohérence groupe/personne/rôle ;
- cohérence groupe/personne/fonction ;
- interdiction d'attribuer un rôle applicatif à un Membre AM ;
- cycle demande, consentement, acceptation, refus et expiration de Membre AM ;
- fusion explicite Membre AM vers compte CARThographie en conservant `ggm_id` ;
- cohérence groupe/tag pour `s_song_tag` ;
- cohérence chant/bloc pour `s_song_tag_verse` ;
- création des références `s_verse` lors de l'ajout d'un chant au recueil ;
- création des sélections par défaut lors de l'ajout d'un tag à un chant ;
- exactement un état actif `selection` et un état actif `default` par groupe.

---

# 15. À ne pas faire

Ne pas :

- créer ou modifier `users.users` ;
- recopier l'identité des utilisateurs avec compte ;
- créer un rôle global ou de groupe `moderator` ;
- créer un rôle `Membre` redondant ;
- créer `app_song` ou `app_chant` ;
- stocker dans AM les textes officiels LSS ;
- créer des tables `p_*` en V1 ;
- déplacer les gabarits de célébration ou d'impression dans `app_group` ;
- faire dépendre une célébration d'une FK obligatoire vers `g_location` ;
- modéliser une deuxième équipe réelle séparée du planning.
