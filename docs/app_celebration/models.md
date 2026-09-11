# app_celebration — Modèle BDD

Ce document est le contrat BDD canonique de `app_celebration` pour la V1.

Il consolide les décisions issues des SFD, de `docs/TABLES/tables_celebration.md`
et des contrats déjà posés pour `app_member` et `app_group`. Les SFD restent
prioritaires en cas de contradiction fonctionnelle.

Sources principales :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/SFD-02-planning.md`
- `docs/SFD-03-chants.md`
- `docs/SFD-04-celebrations.md`
- `docs/app_member/models.md`
- `docs/app_group/models.md`

---

# 1. Frontière

`app_celebration` possède :

- les célébrations réelles ;
- leurs groupes participants ;
- les cellules persistantes vues par le planning ;
- les personnes affectées et leurs fonctions réellement exercées ;
- les droits effectifs de modification d'une célébration ;
- le déroulé réel ;
- les blocs chants, blocs textes et balises de section ;
- le cache AELF de la célébration ;
- la validation de célébration ;
- la validation du planning ;
- l'archivage ;
- les gabarits de célébration ;
- les gabarits d'impression ;
- les feuilles de messe.

`app_celebration` ne possède pas :

- les comptes `users.users` ;
- les profils globaux `app_member` ;
- les groupes, membres, rôles, fonctions et lieux de référence ;
- les états et règles durables du planning ;
- le recueil de chants `am.s_*` ;
- les tags partagés `common.*` ;
- les chants et blocs sources LSS ;
- les textes officiels LSS ;
- les payloads AELF normalisés en tables relationnelles.

---

# 2. Conventions

Toutes les tables propriétaires sont dans le schéma :

```text
am
```

Les tables utilisent le préfixe :

```text
c_*
```

Chaque table possède une PK explicite nommée selon l'alias naturel.

Une FK reprend normalement le nom exact de la PK référencée. Lorsque la FK cible
une table LSS existante, conserver le nom de la PK LSS, par exemple `song_id`
ou `verse_id`.

Les FK cross-schema vers `lss` ou `common` doivent exister réellement dans
PostgreSQL. Utiliser `RunSQL` lorsque Django ne sait pas produire proprement la
contrainte.

---

# 3. Dépendances externes

Ces tables ne sont pas possédées par `app_celebration`.

```text
am.g_group
    PK gg_id
    groupe AM créateur ou participant

am.g_group_member
    PK ggm_id
    personne dans un groupe, Membre avec compte ou Membre AM

am.g_function
    PK gf_id
    fonction possible définie par le groupe

am.g_planning_state
    PK gps_id
    état de planning défini par le groupe

am.s_song
am.s_verse
am.s_song_tag
am.s_song_tag_verse
    recueil et présélections de chants du groupe

common.group_tags
    PK gt_id
    tags de groupe partagés avec LSS

lss.s_songs
    PK song_id
    source de vérité des chants

lss.s_verses
    PK verse_id
    source de vérité des blocs de chants
```

Les éventuels modèles Django représentant ces tables externes doivent être
`managed = False`.

---

# 4. Célébration

## `am.c_celebration`

```text
alias : cc
PK    : cc_id
```

Champs :

```text
cc_id
gg_id
ct_id
celebration_date
celebration_time
aelf_date
place
title
subtitle
description
planning_validated_at
planning_validated_by_ggm_id
validated_at
archived_at
created_at
updated_at
```

Relations :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE

ct_id
    -> am.c_template.ct_id
    ON DELETE SET NULL

planning_validated_by_ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE SET NULL
```

`gg_id` est le groupe créateur et responsable de la célébration. En V1, il
n'existe pas de transfert de responsabilité.

`ct_id` indique le gabarit utilisé lorsque cette information existe. Le déroulé
réel reste autonome : supprimer ou modifier un gabarit ne modifie jamais une
célébration existante.

`aelf_date` est distincte de `celebration_date`.

`place` est un texte libre. Ne pas créer de FK obligatoire vers `g_location`.

`planning_validated_at` représente la validation du planning. `validated_at`
représente la validation de célébration. Ces deux validations ne doivent jamais
être fusionnées.

`archived_at` représente l'archivage courant.

Ne pas créer :

```text
validated_by_ggm_id
archived_by_ggm_id
status
is_past
```

Les états `validée`, `archivée` et `passée` sont dérivés des dates.

---

# 5. Groupes participants

## `am.c_celebration_group`

```text
alias : ccg
PK    : ccg_id
```

Champs :

```text
ccg_id
cc_id
gg_id
created_at
```

Relations :

```text
cc_id
    -> am.c_celebration.cc_id
    ON DELETE CASCADE

gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (cc_id, gg_id)
```

Validations service :

- une célébration possède au moins un groupe participant ;
- le groupe créateur `c_celebration.gg_id` possède toujours une ligne
  `c_celebration_group` ;
- pour chaque groupe participant, `gg_id + celebration_date + celebration_time
  + place normalisé` reste unique.

La règle d'unicité métier doit être implémentée dans un service transactionnel
utilisé pour créer, déplacer, modifier et partager une célébration.

---

# 6. Cellules du planning et participants

## `am.c_celebration_member`

```text
alias : ccm
PK    : ccm_id
```

Champs :

```text
ccm_id
ccg_id
ggm_id
gps_id
can_edit
created_at
updated_at
```

Relations :

```text
ccg_id
    -> am.c_celebration_group.ccg_id
    ON DELETE CASCADE

ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE CASCADE

gps_id
    -> am.g_planning_state.gps_id
    ON DELETE PROTECT
```

Contraintes :

```text
UNIQUE (ccg_id, ggm_id)
```

Cette table est la cellule persistante vue par `app_planning`. Elle représente
la personne, son état de planning courant et son droit effectif de modification
sur cette célébration.

Validations service :

- `g_group_member.gg_id == c_celebration_group.gg_id` ;
- `g_planning_state.gg_id == c_celebration_group.gg_id` ;
- un Membre AM a toujours `can_edit = FALSE` ;
- une fois le planning validé, les membres et fonctions attachés ne sont plus
  modifiables sans dévalidation.

La suppression RGPD de `g_group_member` supprime les cellules et donc
l'historique nominatif associé.

## `am.c_celebration_member_function`

```text
alias : ccmf
PK    : ccmf_id
```

Champs :

```text
ccmf_id
ccm_id
gf_id
created_at
```

Relations :

```text
ccm_id
    -> am.c_celebration_member.ccm_id
    ON DELETE CASCADE

gf_id
    -> am.g_function.gf_id
    ON DELETE PROTECT
```

Contraintes :

```text
UNIQUE (ccm_id, gf_id)
```

Cette table stocke les fonctions réellement exercées par cette personne pour
cette célébration.

Validations service :

- la fonction appartient au même groupe que la cellule ;
- la fonction fait partie des fonctions possibles de la personne au moment de
  la sélection ;
- une cellule possède au moins une fonction sélectionnée.

Une fonction déjà utilisée doit être désactivée dans `app_group` plutôt que
supprimée silencieusement.

---

# 7. Déroulé réel

## `am.c_flow_item`

```text
alias : cfi
PK    : cfi_id
```

Champs :

```text
cfi_id
cc_id
kind
position
interface_title
sheet_title
sheet_subtitle
show_on_sheet
created_at
updated_at
```

Relations :

```text
cc_id
    -> am.c_celebration.cc_id
    ON DELETE CASCADE
```

Contraintes :

```text
kind IN ('song', 'text', 'section')
UNIQUE (cc_id, position)
show_on_sheet = FALSE OR trim(sheet_title) != ''
```

Le déroulé est une liste plate ordonnée. Ne créer aucune hiérarchie, relation
parent/enfant ou section conteneur.

Le service de création applique les valeurs par défaut dépendant du type :
`show_on_sheet = TRUE` pour chant/texte, `FALSE` pour section.

## `am.c_section_marker`

```text
alias : csm
PK    : csm_id
```

Champs :

```text
csm_id
cfi_id
line_above
line_below
```

Relations :

```text
cfi_id
    -> am.c_flow_item.cfi_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (cfi_id)
```

Une balise se déplace et se supprime seule. Elle ne contient aucun bloc.

---

# 8. Blocs chants

## `am.c_song_block`

```text
alias : csb
PK    : csb_id
```

Champs :

```text
csb_id
cfi_id
song_id
source_song_id
source_song_title
```

Relations :

```text
cfi_id
    -> am.c_flow_item.cfi_id
    ON DELETE CASCADE

song_id
    -> lss.s_songs.song_id
    ON DELETE SET NULL
```

Contraintes :

```text
UNIQUE (cfi_id)
```

Pendant la préparation, un bloc chant peut être vide :

```text
song_id = NULL
source_song_id = NULL
```

Lorsqu'un chant est sélectionné, stocker aussi `source_song_id` et
`source_song_title`. Ces champs sont uniquement un snapshot de lisibilité pour
les références cassées ; LSS reste source de vérité tant que `song_id` existe.

La validation de célébration refuse un bloc chant vide.

## `am.c_song_block_tag`

```text
alias : csbt
PK    : csbt_id
```

Champs :

```text
csbt_id
csb_id
gt_id
role
tag_label_snapshot
```

Relations :

```text
csb_id
    -> am.c_song_block.csb_id
    ON DELETE CASCADE

gt_id
    -> common.group_tags.gt_id
    ON DELETE SET NULL
```

Contraintes :

```text
role IN ('primary', 'secondary')
UNIQUE (csb_id, role)
```

Validations service :

- un bloc chant possède exactement un tag `primary` avant validation ;
- il possède zéro ou un tag `secondary` ;
- le tag appartient au groupe créateur de la célébration ;
- les tags communs LSS ne remplacent pas les tags liturgiques de groupe.

`tag_label_snapshot` garde le bloc lisible si le tag est supprimé ou renommé.

## `am.c_song_block_part`

```text
alias : csbp
PK    : csbp_id
```

Champs :

```text
csbp_id
csb_id
verse_id
source_verse_id
source_verse_kind
source_position
selected
mandatory
created_at
updated_at
```

Relations :

```text
csb_id
    -> am.c_song_block.csb_id
    ON DELETE CASCADE

verse_id
    -> lss.s_verses.verse_id
    ON DELETE SET NULL
```

Contraintes :

```text
UNIQUE (csb_id, source_verse_id)
```

Utiliser le vocabulaire technique `verse_id` / `source_verse_id` pour rester
compatible avec `app_group` et `lss.s_verses`.

Ne pas recopier le texte du chant dans AM.

Lorsqu'un chant est choisi, le service crée les parts depuis les blocs LSS
courants, applique la configuration du tag principal issue du recueil
`am.s_*`, puis rend les valeurs `selected` propres à cette occurrence.

Ne jamais recalculer silencieusement les coches si les tags, le recueil, le
gabarit ou LSS évoluent. Recalculer seulement lors d'un remplacement réel du
chant ou d'une réinitialisation totale du déroulé.

---

# 9. Blocs textes et AELF

## `am.c_text_block`

```text
alias : ctb
PK    : ctb_id
```

Champs :

```text
ctb_id
cfi_id
source_mode
final_text
aelf_target
aelf_render_template
created_at
updated_at
```

Relations :

```text
cfi_id
    -> am.c_flow_item.cfi_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (cfi_id)
source_mode IN ('free', 'aelf')
```

`final_text` est un `TEXT`. Il peut être vide pendant la préparation, mais la
validation exige `trim(final_text) != ''`.

`aelf_target` est un `JSONB` structuré, pas une simple chaîne opaque. Il peut
contenir les informations nécessaires pour retrouver une messe, un texte, un
libellé, un type et des fallbacks positionnels.

Après import AELF, `final_text` devient indépendant de la source.

## `am.c_aelf_cache`

```text
alias : cac
PK    : cac_id
```

Champs :

```text
cac_id
cc_id
aelf_date
payload
source_endpoint
fetched_at
```

Relations :

```text
cc_id
    -> am.c_celebration.cc_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (cc_id)
payload JSONB
```

Une célébration possède au maximum un cache AELF actif.

`aelf_date` est la date du payload stocké, distincte de
`c_celebration.aelf_date`. Un refresh remplace le payload, `aelf_date` et
`fetched_at`, mais ne modifie jamais automatiquement `c_text_block.final_text`.

Ne pas normaliser le payload AELF en tables relationnelles.

---

# 10. Gabarits de célébration

## `am.c_template`

```text
alias : ct
PK    : ct_id
```

Champs :

```text
ct_id
gg_id
scope
name
description
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
scope IN ('global', 'group')
scope = 'global' => gg_id IS NULL
scope = 'group'  => gg_id IS NOT NULL
UNIQUE lower(trim(name)) pour les gabarits globaux
UNIQUE (gg_id, lower(trim(name))) pour les gabarits de groupe
```

Les gabarits appartiennent à `app_celebration`, même lorsqu'ils sont propres à
un groupe.

## `am.c_template_item`

```text
alias : cti
PK    : cti_id
```

Champs :

```text
cti_id
ct_id
kind
position
interface_title
sheet_title
sheet_subtitle
show_on_sheet
created_at
updated_at
```

Relations :

```text
ct_id
    -> am.c_template.ct_id
    ON DELETE CASCADE
```

Contraintes :

```text
kind IN ('song', 'text', 'section')
UNIQUE (ct_id, position)
```

La liste de gabarit est plate comme le déroulé réel.

## `am.c_template_song_block`

```text
alias : ctsb
PK    : ctsb_id
```

Champs :

```text
ctsb_id
cti_id
```

Relations :

```text
cti_id
    -> am.c_template_item.cti_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (cti_id)
```

Un bloc chant de gabarit ne contient jamais de chant LSS précis.

## `am.c_template_song_tag`

```text
alias : ctst
PK    : ctst_id
```

Champs :

```text
ctst_id
ctsb_id
gt_id
role
tag_label
```

Relations :

```text
ctsb_id
    -> am.c_template_song_block.ctsb_id
    ON DELETE CASCADE

gt_id
    -> common.group_tags.gt_id
    ON DELETE SET NULL
```

Contraintes :

```text
role IN ('primary', 'secondary')
UNIQUE (ctsb_id, role)
```

Pour un gabarit de groupe, `gt_id` peut référencer un tag du même groupe.

Pour un gabarit global, utiliser `gt_id = NULL` et `tag_label` comme valeur
logique attendue. Le service tente de résoudre ce libellé lors de l'application
du gabarit, sans créer automatiquement de tag.

## `am.c_template_text_block`

```text
alias : cttb
PK    : cttb_id
```

Champs :

```text
cttb_id
cti_id
source_mode
default_text
aelf_target
aelf_render_template
```

Relations :

```text
cti_id
    -> am.c_template_item.cti_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (cti_id)
source_mode IN ('free', 'aelf')
```

Lorsqu'une célébration est créée depuis un gabarit, ces informations sont
copiées dans le bloc réel. Le bloc réel devient ensuite autonome.

## `am.c_template_section_marker`

```text
alias : ctsm
PK    : ctsm_id
```

Champs :

```text
ctsm_id
cti_id
line_above
line_below
```

Relations :

```text
cti_id
    -> am.c_template_item.cti_id
    ON DELETE CASCADE
```

Contraintes :

```text
UNIQUE (cti_id)
```

---

# 11. Feuilles de messe

## `am.c_print_template`

```text
alias : cpt
PK    : cpt_id
```

Champs :

```text
cpt_id
gg_id
name
content
is_primary
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
un seul is_primary = TRUE par gg_id
```

`content` est un `TEXT`.

Les gabarits d'impression appartiennent à `app_celebration`, pas à
`app_group`.

## `am.c_sheet`

```text
alias : cs
PK    : cs_id
```

Champs :

```text
cs_id
cc_id
cpt_id
name
content
is_primary
created_at
updated_at
```

Relations :

```text
cc_id
    -> am.c_celebration.cc_id
    ON DELETE CASCADE

cpt_id
    -> am.c_print_template.cpt_id
    ON DELETE SET NULL
```

Contraintes :

```text
UNIQUE (cc_id, lower(trim(name)))
un seul is_primary = TRUE par cc_id
```

`content` est un `TEXT`. Le PDF est une sortie générée, pas une donnée métier de
base.

Lorsqu'une célébration est validée, générer une feuille par gabarit d'impression
du groupe créateur. Si aucun gabarit n'existe, créer une feuille vide principale.

Une feuille devient autonome après génération. Supprimer ou modifier le gabarit
n'altère pas les feuilles existantes.

---

# 12. Services transactionnels

À implémenter dans des services Django, pas directement dans les vues :

- création, déplacement et partage d'une célébration avec contrôle
  `groupe + date + heure + lieu` ;
- création automatique du groupe participant créateur ;
- création des cellules manquantes lors de la création d'une célébration ou de
  l'arrivée d'un membre ;
- validation et dévalidation du planning ;
- validation et dévalidation de la célébration ;
- génération et suppression atomiques des feuilles ;
- réinitialisation totale depuis un gabarit ;
- remplacement d'un chant et recréation de ses parts ;
- refresh AELF sans toucher aux textes finaux ;
- archivage, désarchivage, purge automatique et purge RGPD.

Une célébration passée est calculée avec `celebration_date` et le fuseau de
l'application. Une célébration du jour reste modifiable toute la journée.

---

# 13. Règles garanties par PostgreSQL

À viser en contrainte SQL :

- PK explicite sur chaque table ;
- FK de possession en `ON DELETE CASCADE` ;
- FK historiques en `ON DELETE SET NULL` ;
- FK vers état ou fonction utilisée en `ON DELETE PROTECT` ;
- unicité `(cc_id, gg_id)` ;
- unicité `(ccg_id, ggm_id)` ;
- unicité `(ccm_id, gf_id)` ;
- unicité des positions dans le déroulé et les gabarits ;
- unicité des spécialisations 1–1 ;
- unicité des rôles primary/secondary des tags de blocs chants ;
- unicité des noms de gabarits et feuilles par périmètre ;
- unicité partielle des gabarits ou feuilles principaux.

---

# 14. Règles garanties par services Django

À garantir par service :

- cohérence groupe créateur et groupes participants ;
- unicité métier `groupe + date + heure + lieu` ;
- cohérence groupe/personne/état/fonction ;
- interdiction de `can_edit = TRUE` pour un Membre AM ;
- validation de planning réservée aux Responsables ;
- validation de célébration réservée aux Responsables du groupe créateur ;
- verrouillage des cellules après validation du planning ;
- refus de validation avec bloc chant vide ou bloc texte vide ;
- refus de modification d'une célébration passée ;
- application du gabarit global sans création silencieuse de tags ;
- non-recalcul des parts de chant après évolution des tags ou du recueil ;
- purge RGPD des affectations même si la célébration est archivée.

---

# 15. À ne pas faire

Ne pas :

- créer une table de planning `p_*` ;
- créer une célébration par groupe pour une célébration partagée ;
- créer une hiérarchie de sections ;
- recopier le texte officiel des chants LSS ;
- supprimer un bloc chant quand le chant LSS disparaît ;
- recalculer silencieusement les parts d'un chant existant ;
- modifier `final_text` lors d'un refresh AELF ;
- normaliser le payload AELF en dizaines de tables ;
- enregistrer l'auteur d'une validation ou d'un archivage ;
- créer `validated_by_ggm_id`, `archived_by_ggm_id`, `status` ou `is_past` ;
- donner la validation à un simple Membre modificateur ;
- permettre au Responsable impression de modifier le déroulé ;
- déplacer les gabarits dans `app_group` ;
- stocker le PDF comme donnée métier de base ;
- créer ou modifier des tables `common` ou `lss` depuis `app_celebration`.
