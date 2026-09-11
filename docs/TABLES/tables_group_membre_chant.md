# Directive Codex — migrations Django des `songs` dans `app_group`

## 1. Objectif

Créer les modèles et migrations Django nécessaires à la gestion des chants dans **Animation Messe**.

Il n'existe pas d'application Django `app_song`.

Les chants sont gérés par **Lyrics Slide Show (LSS)**.

Animation Messe ne possède qu'une **vue métier des chants propre à chaque groupe** :

* présence d'un chant dans le recueil du groupe ;
* références aux blocs LSS utilisés par AM ;
* association du chant avec les tags du groupe ;
* configuration par défaut des blocs pour chaque tag.

Ces données appartiennent donc à :

```text
app_group
```

même si les tables correspondantes utilisent le préfixe métier :

```text
s_*
```

---

# 2. Principe architectural

La règle fondamentale est :

> LSS possède le chant.
> AM possède uniquement la manière dont un groupe utilise ce chant.

Animation Messe ne doit jamais recopier depuis LSS :

* le titre ;
* la description ;
* le texte ;
* le type des blocs ;
* leur libellé ;
* leurs métadonnées éditoriales.

AM conserve uniquement les **identifiants LSS nécessaires**.

Les données LSS doivent être lues directement lorsque l'application en a besoin.

---

# 3. Aucun `app_song`

Ne pas créer :

```text
app_song
```

Ne pas créer non plus :

```text
app_chant
```

Les modèles concernés doivent être placés dans :

```text
app_group
```

Ils peuvent éventuellement être organisés dans un fichier dédié à l'intérieur de l'app, par exemple :

```text
app_group/models/song.py
```

si l'architecture actuelle du projet permet proprement de découper les modèles.

Mais ils appartiennent toujours à l'application Django :

```text
app_group
```

---

# 4. Langue utilisée

Le code et les noms SQL sont en anglais.

Utiliser :

```text
song
verse
tag
group
```

Ne jamais utiliser dans les modèles ou tables :

```text
chant
couplet
refrain
```

Ces notions restent des libellés métier ou des valeurs provenant de LSS.

---

# 5. Schéma PostgreSQL

Les tables AM créées ici appartiennent au schéma :

```text
am
```

Les données sources restent dans leurs schémas actuels :

```text
lss
common
```

Ne déplacer aucune table existante entre les schémas.

---

# 6. Préfixe des tables

Toutes les tables de cette partie utilisent :

```text
s_*
```

Exemples :

```text
s_song
s_verse
s_song_tag
s_song_tag_verse
```

Même si ces modèles sont techniquement définis dans `app_group`.

---

# 7. Convention obligatoire des PK

Chaque table doit avoir une PK explicite.

Le nom de la PK est construit à partir de l'alias naturel de la table.

Exemples :

```text
am.s_song
alias : ss
PK    : ss_id
```

```text
am.s_verse
alias : sv
PK    : sv_id
```

```text
am.s_song_tag
alias : sst
PK    : sst_id
```

```text
am.s_song_tag_verse
alias : sstv
PK    : sstv_id
```

Ne jamais laisser Django créer implicitement :

```text
id
```

ou :

```text
song_id
```

comme PK locale.

Toutes les PK doivent être déclarées explicitement dans les modèles.

---

# 8. Convention obligatoire des FK

Une FK doit reprendre **exactement le nom de la PK qu'elle référence**.

Exemple :

```text
am.s_song.ss_id
```

sera référencée ailleurs sous le nom :

```text
ss_id
```

et jamais :

```text
song_id
am_song_id
song_fk
```

Même règle pour :

```text
gg_id
sv_id
sst_id
gt_id
```

En revanche, lorsqu'une FK pointe vers une table LSS dont la PK existante s'appelle :

```text
song_id
```

la colonne reste :

```text
song_id
```

Lorsqu'elle pointe vers :

```text
verse_id
```

la colonne reste :

```text
verse_id
```

Le nom d'une FK est donc toujours celui de la **PK référencée**.

---

# 9. Table `am.s_song`

## Rôle

Cette table représente :

> un chant LSS présent dans le recueil d'un groupe AM.

Elle ne représente pas un nouveau chant.

Le chant reste exclusivement propriété de LSS.

## Table

```text
am.s_song
```

Alias :

```text
ss
```

PK :

```text
ss_id
```

Champs :

```text
ss_id
gg_id
song_id
created_at
updated_at
```

## FK vers le groupe AM

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

## FK vers LSS

```text
song_id
    -> lss.s_songs.song_id
    ON DELETE CASCADE
```

## Unicité

Un chant LSS ne peut apparaître qu'une seule fois dans le recueil d'un même groupe :

```text
UNIQUE (gg_id, song_id)
```

## Conséquence

Si un chant est supprimé définitivement dans LSS :

```text
lss.s_songs
```

sa ligne correspondante dans :

```text
am.s_song
```

est automatiquement supprimée.

Toutes les données courantes AM dépendantes seront ensuite supprimées par cascade.

---

# 10. Table `am.s_verse`

## Rôle

Cette table représente uniquement :

> une référence AM vers un bloc LSS appartenant à un chant du recueil.

Le mot `verse` reprend ici la terminologie technique existante de LSS.

Le bloc LSS peut fonctionnellement être :

* un refrain ;
* un couplet ;
* un pont ;
* un pré-refrain ;
* un refrain final ;
* tout autre type supporté par LSS.

AM ne copie pas ce type.

Il le lit depuis LSS.

## Table

```text
am.s_verse
```

Alias :

```text
sv
```

PK :

```text
sv_id
```

Champs :

```text
sv_id
ss_id
verse_id
created_at
```

## FK vers le chant AM

```text
ss_id
    -> am.s_song.ss_id
    ON DELETE CASCADE
```

## FK vers LSS

```text
verse_id
    -> lss.s_verses.verse_id
    ON DELETE CASCADE
```

## Unicité

```text
UNIQUE (ss_id, verse_id)
```

Un bloc LSS ne peut être référencé qu'une fois dans la représentation AM d'un chant.

---

# 11. Ne pas recopier l'ordre des blocs

Ne pas ajouter dans `s_verse` :

```text
position
order
verse_number
type
label
text
```

L'ordre officiel appartient à LSS.

Lorsqu'AM affiche un chant, il récupère l'ordre courant depuis LSS.

Ainsi, une modification d'ordre dans LSS ne nécessite aucune synchronisation particulière dans AM.

Cette règle simplifie volontairement le modèle précédent de la SFD.

Le miroir AM contient uniquement :

```text
song_id
verse_id
```

et les données réellement propres au groupe.

---

# 12. Tags du groupe

La définition des tags du groupe ne doit pas être créée par ces migrations.

Les tags appartiennent fonctionnellement à :

```text
app_group
```

mais leurs tables physiques partagées avec LSS sont dans :

```text
common
```

La table de référence utilisée ici est :

```text
common.group_tags
```

avec :

```text
gt_id
```

comme PK.

Ne pas recréer cette table dans le schéma `am`.

Ne pas créer de copie des tags dans `s_*`.

---

# 13. Table `am.s_song_tag`

## Rôle

Cette table signifie :

> ce chant du recueil est utilisé par ce groupe pour ce tag.

Exemple :

```text
Messe de Saint-Paul
├── Kyrie
├── Sanctus
└── Agnus
```

## Table

```text
am.s_song_tag
```

Alias :

```text
sst
```

PK :

```text
sst_id
```

Champs :

```text
sst_id
ss_id
gt_id
created_at
```

## FK vers le chant AM

```text
ss_id
    -> am.s_song.ss_id
    ON DELETE CASCADE
```

## FK vers le tag groupe

```text
gt_id
    -> common.group_tags.gt_id
    ON DELETE CASCADE
```

## Unicité

```text
UNIQUE (ss_id, gt_id)
```

Un tag donné ne peut être associé qu'une seule fois au même chant du recueil.

---

# 14. Cohérence groupe ↔ tag

Le service métier doit vérifier que :

```text
s_song.gg_id
```

et :

```text
group_tags.gg_id
```

désignent le même groupe.

Il est interdit d'associer à un chant du groupe A un tag appartenant au groupe B.

Si cette contrainte peut être garantie proprement en base sans dupliquer inutilement les colonnes, le faire.

Sinon :

* conserver les FK simples ;
* réaliser le contrôle dans le service métier ;
* ajouter les tests nécessaires.

Ne pas complexifier excessivement le modèle uniquement pour obtenir une contrainte composite.

---

# 15. Table `am.s_song_tag_verse`

## Rôle

Cette table porte la règle métier :

> pour ce tag appliqué à ce chant, ce bloc doit-il être sélectionné par défaut ?

La donnée fonctionnelle est donc :

```text
song tag × verse -> boolean
```

## Table

```text
am.s_song_tag_verse
```

Alias :

```text
sstv
```

PK :

```text
sstv_id
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

## FK vers l'association chant/tag

```text
sst_id
    -> am.s_song_tag.sst_id
    ON DELETE CASCADE
```

## FK vers le bloc AM

```text
sv_id
    -> am.s_verse.sv_id
    ON DELETE CASCADE
```

## Valeur par défaut

```text
selected_by_default = TRUE
```

## Unicité

```text
UNIQUE (sst_id, sv_id)
```

---

# 16. Cohérence chant ↔ bloc

Le service doit vérifier que le bloc référencé par :

```text
sv_id
```

appartient au même :

```text
ss_id
```

que celui référencé par :

```text
sst_id
```

Il doit être impossible de construire :

```text
tag du chant A
+
verse du chant B
```

Même stratégie que pour la cohérence groupe/tag :

* contrainte DB simple si elle reste propre ;
* sinon validation transactionnelle dans le service métier ;
* tests obligatoires.

---

# 17. Valeur par défaut lors de l'ajout d'un tag

Lorsqu'un tag est associé à un chant déjà présent dans le recueil :

```text
s_song_tag
```

doit être créé.

Puis une ligne :

```text
s_song_tag_verse
```

doit être créée pour chaque :

```text
s_verse
```

existant pour ce chant.

Par défaut :

```text
selected_by_default = TRUE
```

Le groupe pourra ensuite désactiver individuellement certains blocs.

---

# 18. Aucun texte dans ces tables

Interdiction d'ajouter dans les tables `s_*` :

```text
title
description
lyrics
text
content
verse_text
song_title
song_description
```

Ces données appartiennent à LSS.

Même principe pour :

```text
verse_type
verse_label
verse_number
```

si ces informations existent déjà et peuvent être lues depuis LSS.

AM ne doit pas devenir un cache éditorial de LSS.

---

# 19. Politique de synchronisation

La synchronisation repose sur trois comportements différents.

## 19.1 Modification dans LSS

Exemples :

* changement de texte ;
* changement de titre ;
* modification de description ;
* changement du type/libellé d'un bloc ;
* changement d'ordre.

AM n'a rien à mettre à jour.

Il continue simplement à lire LSS.

Il n'existe donc aucune logique :

```text
ON UPDATE CASCADE
```

spécifique à mettre en place.

Les identifiants LSS sont considérés comme stables.

---

# 20. Suppression dans LSS

Les suppressions doivent être propagées automatiquement par PostgreSQL.

## Suppression d'un chant

```text
lss.s_songs
    DELETE
        ↓ CASCADE
am.s_song
        ↓ CASCADE
am.s_verse
am.s_song_tag
        ↓
am.s_song_tag_verse
```

## Suppression d'un bloc

```text
lss.s_verses
    DELETE
        ↓ CASCADE
am.s_verse
        ↓ CASCADE
am.s_song_tag_verse
```

Les contraintes doivent donc être de véritables FK PostgreSQL avec :

```text
ON DELETE CASCADE
```

Ne pas se contenter du comportement Python de Django.

---

# 21. INSERT dans LSS

Un nouvel objet LSS ne peut évidemment pas provoquer automatiquement un INSERT AM.

Exemples :

* nouveau chant ;
* nouveau bloc ajouté dans un chant.

Ces cas seront gérés par un processus applicatif séparé :

```text
cron de synchronisation
```

Ne pas implémenter ce cron dans cette migration sauf si une tâche séparée le demande.

---

# 22. Nouveau chant LSS

Un nouveau chant ajouté dans LSS ne doit pas automatiquement être ajouté au recueil de tous les groupes.

Il devient simplement disponible dans l'espace d'échange / catalogue LSS.

Une ligne :

```text
am.s_song
```

n'est créée que lorsqu'un groupe ajoute explicitement le chant à son recueil.

---

# 23. Ajout d'un chant au recueil

Lorsque le groupe ajoute un chant LSS à son recueil :

1. créer :

```text
am.s_song
```

avec :

```text
gg_id
song_id
```

2. récupérer dans LSS les blocs actuels du chant ;

3. créer une ligne :

```text
am.s_verse
```

pour chaque :

```text
verse_id
```

LSS ;

4. ne copier aucune autre donnée LSS.

---

# 24. Nouveau bloc ajouté dans LSS

Si LSS ajoute ultérieurement un nouveau bloc à un chant déjà présent dans un recueil AM :

```text
lss.s_verses
```

contient un `verse_id` qui n'existe pas encore dans :

```text
am.s_verse
```

Le cron devra détecter cet écart.

Il créera la nouvelle référence :

```text
am.s_verse
```

La politique métier concernant :

```text
s_song_tag_verse
```

pour les tags déjà présents devra respecter la SFD.

Ne pas considérer automatiquement qu'un nouveau bloc est forcément actif pour tous les tags existants.

Ce traitement appartient au service/cron de synchronisation, pas à la migration.

---

# 25. Retrait d'un chant du recueil

Lorsqu'un groupe retire volontairement un chant de son recueil :

```text
DELETE am.s_song
```

La cascade doit supprimer automatiquement :

```text
s_verse
s_song_tag
s_song_tag_verse
```

Cela ne doit évidemment jamais supprimer :

```text
lss.s_songs
lss.s_verses
```

Une FK ne fonctionne que du parent vers l'enfant.

Supprimer une ligne AM ne doit avoir aucun effet sur LSS.

---

# 26. Retrait d'un tag du chant

Supprimer :

```text
am.s_song_tag
```

doit supprimer automatiquement ses :

```text
am.s_song_tag_verse
```

avec :

```text
ON DELETE CASCADE
```

Cela ne supprime :

* ni le chant ;
* ni les blocs ;
* ni le tag dans `common`.

---

# 27. Suppression d'un tag de groupe

Si un tag est supprimé dans :

```text
common.group_tags
```

alors toutes les associations :

```text
am.s_song_tag
```

utilisant ce tag doivent être supprimées par :

```text
ON DELETE CASCADE
```

et donc également :

```text
am.s_song_tag_verse
```

par cascade indirecte.

Aucun chant LSS n'est supprimé.

---

# 28. FK vers des tables externes à l'app Django

Certaines FK ciblent des tables dont `app_group` n'est pas propriétaire :

```text
lss.s_songs
lss.s_verses
common.group_tags
```

Ne jamais faire croire à Django qu'il doit créer, modifier ou supprimer ces tables.

Les modèles représentant ces tables doivent être :

```python
managed = False
```

lorsqu'ils sont nécessaires côté ORM.

---

# 29. Contraintes PostgreSQL cross-schema

Pour les FK entre :

```text
am
```

et :

```text
lss
common
```

ne pas sacrifier la contrainte SQL réelle simplement parce que Django gère mal une relation cross-schema.

Si nécessaire :

1. représenter proprement la relation dans les modèles ;
2. empêcher Django de devenir propriétaire de la table externe ;
3. créer la vraie FK PostgreSQL dans la migration avec :

```python
RunSQL
```

Les contraintes doivent réellement exister dans PostgreSQL.

Exemple conceptuel :

```sql
ALTER TABLE am.s_song
ADD CONSTRAINT ...
FOREIGN KEY (song_id)
REFERENCES lss.s_songs(song_id)
ON DELETE CASCADE;
```

Même principe pour :

```text
verse_id
gt_id
```

---

# 30. Pas de `ON UPDATE CASCADE`

Ne pas créer :

```text
ON UPDATE CASCADE
```

pour les identifiants LSS.

Les PK LSS sont considérées comme immuables.

Une modification métier du chant ne modifie pas son ID.

Une hypothétique modification de PK LSS serait une opération exceptionnelle de migration de données et non un fonctionnement normal d'AM.

---

# 31. Modèles attendus

Dans `app_group`, créer conceptuellement les quatre modèles suivants :

```text
Song
    -> am.s_song

Verse
    -> am.s_verse

SongTag
    -> am.s_song_tag

SongTagVerse
    -> am.s_song_tag_verse
```

Les noms Python peuvent être légèrement adaptés pour éviter les ambiguïtés avec les modèles LSS.

Par exemple :

```text
GroupSong
GroupSongVerse
GroupSongTag
GroupSongTagVerse
```

si cela améliore fortement la lisibilité du code.

Mais les noms SQL restent obligatoirement :

```text
s_song
s_verse
s_song_tag
s_song_tag_verse
```

---

# 32. Tableau récapitulatif

| Table              | PK        | FK principales      |
| ------------------ | --------- | ------------------- |
| `s_song`           | `ss_id`   | `gg_id`, `song_id`  |
| `s_verse`          | `sv_id`   | `ss_id`, `verse_id` |
| `s_song_tag`       | `sst_id`  | `ss_id`, `gt_id`    |
| `s_song_tag_verse` | `sstv_id` | `sst_id`, `sv_id`   |

Toutes les relations de possession utilisent :

```text
ON DELETE CASCADE
```

---

# 33. Graphe des relations

```text
am.g_group
   │
   │ gg_id
   │ CASCADE
   ▼
am.s_song
   │
   ├──────────── song_id ────────────► lss.s_songs
   │                                  CASCADE vers AM
   │
   ├── ss_id
   │   CASCADE
   │
   ▼
am.s_verse
   │
   └──────────── verse_id ───────────► lss.s_verses
                                      CASCADE vers AM
```

Et pour les tags :

```text
am.s_song
   │
   │ ss_id
   ▼
am.s_song_tag
   │
   ├──────────── gt_id ──────────────► common.group_tags
   │                                  CASCADE vers AM
   │
   │ sst_id
   ▼
am.s_song_tag_verse
   ▲
   │ sv_id
   │
am.s_verse
```

---

# 34. Attention aux célébrations futures

Les cascades décrites ici concernent :

> la vue courante du recueil du groupe.

Elles ne doivent pas conduire plus tard à supprimer silencieusement l'historique d'une célébration.

Lorsque `app_celebration` référencera un chant ou des blocs utilisés historiquement, sa stratégie de conservation devra être étudiée séparément.

En particulier :

```text
suppression LSS
```

peut casser une référence historique, mais ne doit pas supprimer une célébration existante.

Ne pas anticiper ce problème en faisant dépendre les célébrations directement par cascade de :

```text
s_song
s_verse
```

---

# 35. Tests obligatoires

Créer au minimum des tests vérifiant :

### `s_song`

* PK nommée `ss_id` ;
* unicité `(gg_id, song_id)` ;
* suppression du groupe → suppression du `s_song` ;
* suppression du chant LSS → suppression du `s_song`.

### `s_verse`

* PK nommée `sv_id` ;
* unicité `(ss_id, verse_id)` ;
* suppression du `s_song` → suppression des `s_verse` ;
* suppression du verse LSS → suppression du `s_verse`.

### `s_song_tag`

* PK nommée `sst_id` ;
* unicité `(ss_id, gt_id)` ;
* suppression du chant AM → suppression des associations ;
* suppression du tag groupe → suppression des associations ;
* impossibilité métier d'utiliser un tag appartenant à un autre groupe.

### `s_song_tag_verse`

* PK nommée `sstv_id` ;
* unicité `(sst_id, sv_id)` ;
* `selected_by_default = TRUE` par défaut ;
* suppression de `s_song_tag` → cascade ;
* suppression de `s_verse` → cascade ;
* impossibilité métier d'associer un verse d'un autre chant.

---

# 36. Vérification SQL réelle

Les tests Django ne suffisent pas.

Après migration, vérifier dans PostgreSQL que les vraies contraintes existent.

Contrôler notamment :

```text
am.s_song.gg_id
am.s_song.song_id

am.s_verse.ss_id
am.s_verse.verse_id

am.s_song_tag.ss_id
am.s_song_tag.gt_id

am.s_song_tag_verse.sst_id
am.s_song_tag_verse.sv_id
```

Toutes les contraintes de suppression prévues doivent être réellement :

```text
ON DELETE CASCADE
```

---

# 37. Migration Django

Créer une migration dédiée dans :

```text
app_group/migrations/
```

Ne pas intégrer silencieusement ces tables dans une migration contenant des modifications sans rapport.

Si plusieurs migrations sont nécessaires à cause des FK cross-schema, une séparation acceptable est :

```text
00xx_song_models.py
00xy_song_external_constraints.py
```

La deuxième peut contenir les `RunSQL` nécessaires.

Prévoir également les opérations inverses (`reverse_sql`) lorsqu'elles sont raisonnablement possibles.

---

# 38. Commandes de contrôle

Avant de terminer :

```bash
python manage.py makemigrations --check
python manage.py showmigrations app_group
python manage.py migrate
python manage.py check
pytest
```

Puis les contrôles qualité configurés dans le projet, notamment Ruff.

Vérifier également :

```bash
git diff --check
```

---

# 39. Ce qu'il ne faut pas faire

Ne pas :

* créer `app_song` ;
* créer `app_chant` ;
* utiliser des noms SQL français ;
* laisser Django créer des PK génériques `id` ;
* appeler `song_id` une PK locale AM si elle doit s'appeler `ss_id` ;
* recopier les textes LSS ;
* recopier les titres ;
* recopier les descriptions ;
* recopier les types de verse ;
* recopier l'ordre des verses ;
* recréer les tags dans `am` ;
* modifier les tables LSS ;
* modifier les tables `common` depuis cette migration ;
* faire d'INSERT automatique AM lorsqu'un INSERT apparaît dans LSS ;
* créer du `ON UPDATE CASCADE` ;
* supprimer un objet LSS lorsqu'un objet AM est supprimé ;
* prévoir une cascade future capable de détruire une célébration historique.

---

# 40. Résultat attendu

Après migration, le modèle doit pouvoir représenter simplement :

```text
Groupe : Paroisse A

Recueil
└── song_id = 123
    ├── verse_id = 451
    ├── verse_id = 452
    ├── verse_id = 453
    └── verse_id = 454
```

sans avoir copié le moindre texte.

Puis :

```text
song 123
└── tag Communion
    ├── verse 451 -> TRUE
    ├── verse 452 -> TRUE
    ├── verse 453 -> FALSE
    └── verse 454 -> TRUE
```

Toutes les informations éditoriales affichées à l'utilisateur restent lues depuis LSS.

---

# 41. Principe final

La règle à préserver dans toute l'implémentation est :

```text
LSS
= source de vérité du chant

common
= référentiels réellement partagés

app_group / s_*
= vue et configuration du chant pour un groupe AM

app_celebration
= choix concret effectué pour une célébration
```

AM ne duplique pas LSS.

AM stocke uniquement les références nécessaires pour ajouter sa propre logique métier.
