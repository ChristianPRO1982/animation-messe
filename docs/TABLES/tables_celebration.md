# Directive Codex — migrations initiales `app_celebration`

## 1. Objectif

Créer le socle de données de `app_celebration` sur la branche `init`.

`app_celebration` porte l'objet métier central d'Animation Messe :

* les célébrations ;
* leurs groupes participants ;
* les personnes affectées ;
* leurs fonctions réellement exercées sur la célébration ;
* les droits effectifs de modification ;
* les gabarits de célébration ;
* le déroulé ;
* les blocs chants ;
* les blocs textes ;
* les balises de section ;
* le cache AELF ;
* la validation ;
* l'archivage ;
* les gabarits d'impression ;
* les feuilles de messe.

Le planning doit rester dérivé des célébrations.

Ne pas créer une seconde entité métier représentant une « ligne de planning ».

---

# 2. Sources de vérité

Lire avant toute modification :

* `docs/app_celebration/functional_requirements.md`
* `docs/SFD-04-celebrations.md`
* `docs/SFD-03-chants.md`
* `docs/SFD-02-planning.md`
* `docs/SFD-01-groupes_et_membres.md`

En cas de contradiction :

> la SFD la plus récente prime.

Tenir également compte des modèles désormais définis dans :

* `app_member`
* `app_group`

et des tables partagées du schéma :

```text
common
```

Ne pas recréer dans `app_celebration` des données dont une autre application est déjà propriétaire.

---

# 3. Décisions fonctionnelles désormais figées

Les décisions suivantes sont obligatoires.

## 3.1. Validation

Un Membre autorisé à modifier une célébration :

```text
NE PEUT PAS la valider.
```

Seuls les Responsables du groupe créateur/responsable peuvent :

* valider ;
* dévalider.

## 3.2. Gabarits

Les gabarits de célébration appartiennent à :

```text
app_celebration
```

même lorsqu'ils appartiennent à un groupe.

Les gabarits d'impression appartiennent également à :

```text
app_celebration
```

Ils ne doivent pas être déplacés vers `app_group`.

Ils constituent des objets métier vivants de la célébration, et non de simples paramètres techniques du groupe.

## 3.3. Référence LSS cassée

Lorsqu'un chant LSS utilisé par une célébration est supprimé :

* le bloc chant AM doit survivre ;
* la FK vivante vers LSS peut devenir `NULL` ;
* AM conserve au minimum :

  * l'identifiant historique LSS ;
  * le titre historique du chant.

## 3.4. AELF

Le payload AELF brut doit être conservé intégralement dans PostgreSQL.

Utiliser :

```text
JSONB
```

La structure du JSON ne doit pas être normalisée en dizaines de tables AELF.

## 3.5. Traçabilité

Pour validation et archivage, stocker les dates/heures nécessaires.

Ne pas stocker l'identité de la personne ayant effectué l'action.

Ne pas créer notamment :

```text
validated_by_ggm_id
archived_by_ggm_id
```

## 3.6. Feuilles

Le contenu éditable d'une feuille est stocké sous forme de :

```text
TEXT
```

La convention exacte de contenu WYSIWYG/HTML relève de la couche applicative.

Ne pas créer une structure relationnelle représentant les paragraphes, styles, lignes ou éléments du document.

---

# 4. Convention de nommage

Toutes les tables appartiennent au schéma PostgreSQL :

```text
am
```

Toutes les tables de cette application sont préfixées :

```text
c_
```

La PK reprend l'alias naturel de la table.

Exemples :

```text
c_celebration                    -> cc_id
c_celebration_group              -> ccg_id
c_celebration_member             -> ccm_id
c_celebration_member_function    -> ccmf_id

c_template                       -> ct_id
c_template_item                  -> cti_id

c_flow_item                      -> cfi_id
c_song_block                     -> csb_id
c_text_block                     -> ctb_id
c_section_marker                 -> csm_id

c_aelf_cache                     -> cac_id

c_print_template                 -> cpt_id
c_sheet                          -> cs_id
```

Une FK reprend normalement exactement le nom de la PK référencée.

Exemple :

```text
c_celebration_group.cc_id
    -> c_celebration.cc_id
```

Lorsqu'une table possède plusieurs relations fonctionnelles vers le même type d'objet, utiliser une table d'association plutôt que multiplier inutilement des colonnes ambiguës.

---

# 5. Table centrale `c_celebration`

Créer :

```text
am.c_celebration
```

Alias :

```text
cc
```

PK :

```text
cc_id
```

Champs minimum :

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

validated_at
archived_at

created_at
updated_at
```

## 5.1. Groupe créateur

```text
gg_id
    -> am.g_group.gg_id
```

Le `gg_id` représente :

> le groupe créateur et responsable de la célébration.

Pour une célébration non partagée, c'est simplement son groupe.

Pour une célébration partagée, ce groupe reste responsable.

En V1, il n'existe aucun transfert de responsabilité.

La suppression du groupe créateur peut supprimer ses célébrations selon le cycle de suppression du groupe.

Utiliser :

```text
ON DELETE CASCADE
```

## 5.2. Gabarit utilisé

```text
ct_id
    -> c_template.ct_id
    ON DELETE SET NULL
```

Une célébration peut ne jamais avoir utilisé de gabarit.

La suppression d'un gabarit ne doit jamais supprimer une célébration existante.

Le déroulé déjà instancié reste totalement autonome.

## 5.3. Dates

```text
celebration_date
```

est la date réelle de la célébration.

```text
aelf_date
```

est la date liturgique utilisée pour AELF.

Lors d'une création classique :

```text
aelf_date = celebration_date
```

mais elles restent indépendantes ensuite.

## 5.4. Lieu

`place` est un texte stocké dans la célébration.

Ne pas faire de FK obligatoire vers `g_location`.

Les lieux habituels du groupe ne sont qu'une aide à la saisie.

## 5.5. Validation

Utiliser :

```text
validated_at NULL
```

pour une célébration non validée.

Et :

```text
validated_at NOT NULL
```

pour une célébration actuellement validée.

Une dévalidation remet :

```text
validated_at = NULL
```

Il n'est pas demandé en V1 de conserver l'historique des cycles validation/dévalidation.

Ne pas créer d'identifiant du validateur.

## 5.6. Archivage

Même principe :

```text
archived_at NULL
```

signifie non archivée.

```text
archived_at NOT NULL
```

signifie archivée.

Un désarchivage remet :

```text
archived_at = NULL
```

Ne pas créer d'identifiant de l'auteur de l'archivage.

## 5.7. Ne pas créer de champ `status`

Ne pas dupliquer les états avec un enum du type :

```text
draft
validated
archived
past
```

Ces états sont dérivables de :

* `validated_at` ;
* `archived_at` ;
* `celebration_date`.

Éviter plusieurs sources de vérité.

---

# 6. Groupes participants

Créer :

```text
am.c_celebration_group
```

Alias :

```text
ccg
```

PK :

```text
ccg_id
```

Champs :

```text
ccg_id
cc_id
gg_id
```

FK :

```text
cc_id
    -> c_celebration.cc_id
    ON DELETE CASCADE
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Unicité :

```text
(cc_id, gg_id)
```

Une célébration doit posséder au moins un groupe participant.

Le groupe créateur :

```text
c_celebration.gg_id
```

doit obligatoirement posséder sa ligne dans :

```text
c_celebration_group
```

Cette règle sera contrôlée par le service métier.

---

# 7. Unicité métier groupe + date + heure + lieu

Pour chaque groupe participant, il ne peut exister deux célébrations avec simultanément :

```text
gg_id
celebration_date
celebration_time
place
```

Ne pas dupliquer date/heure/lieu dans `c_celebration_group` uniquement pour créer une contrainte SQL.

Conserver `c_celebration` comme source de vérité.

Implémenter cette règle dans un service transactionnel unique utilisé pour :

* création ;
* déplacement ;
* ajout d'un groupe participant ;
* modification de la date ;
* modification de l'heure ;
* modification du lieu.

Le service doit :

1. ouvrir `transaction.atomic()` ;
2. verrouiller les groupes concernés avec `select_for_update()` ;
3. rechercher un conflit ;
4. refuser l'opération avant écriture si nécessaire.

Normaliser le lieu avant comparaison au minimum avec :

```text
trim
```

et une comparaison insensible à la casse.

Ne pas introduire de géocodage.

Ajouter des tests vérifiant les conflits, notamment avec les célébrations partagées.

---

# 8. Membres attachés à une célébration

Créer :

```text
am.c_celebration_member
```

Alias :

```text
ccm
```

PK :

```text
ccm_id
```

Champs :

```text
ccm_id
ccg_id
ggm_id
can_edit
```

FK :

```text
ccg_id
    -> c_celebration_group.ccg_id
    ON DELETE CASCADE
```

FK :

```text
ggm_id
    -> am.g_group_member.ggm_id
```

Les affectations sont des données nominatives soumises à purge RGPD.

Ne pas concevoir leur FK de manière à conserver artificiellement un membre disparu.

Prévoir leur suppression indépendante de la célébration.

Unicité :

```text
(ccg_id, ggm_id)
```

## 8.1. Pourquoi référencer `ccg_id`

Une affectation doit appartenir à :

> la participation d'un groupe précis à une célébration.

Cela permet notamment que :

> retirer un groupe participant supprime automatiquement les affectations de ce groupe uniquement.

## 8.2. Souveraineté

Le service doit vérifier que :

```text
g_group_member.gg_id
==
c_celebration_group.gg_id
```

Un groupe ne peut pas affecter les membres d'un autre groupe participant.

## 8.3. Membres AM

Un Membre AM peut posséder une ligne `c_celebration_member`.

Cependant :

```text
can_edit = FALSE
```

doit toujours être imposé.

Un Membre AM n'obtient jamais d'accès logiciel.

## 8.4. `can_edit`

`can_edit` représente le droit effectif courant de modification donné à ce membre sur cette célébration.

Lors de l'affectation initiale, sa valeur peut être déterminée depuis :

```text
g_function.auto_edit_celebration
```

mais elle doit ensuite être persistée.

Cela permet l'attribution ou le retrait manuel du droit sans recalcul caché.

Les Responsables n'ont pas besoin d'une ligne artificielle `can_edit = TRUE` pour disposer de leurs droits :

> leur rôle Responsable leur donne toujours les droits de modification tant que la célébration est modifiable.

---

# 9. Fonctions exercées sur cette célébration

Créer :

```text
am.c_celebration_member_function
```

Alias :

```text
ccmf
```

PK :

```text
ccmf_id
```

Champs :

```text
ccmf_id
ccm_id
gf_id
```

FK :

```text
ccm_id
    -> c_celebration_member.ccm_id
    ON DELETE CASCADE
```

FK :

```text
gf_id
    -> am.g_function.gf_id
```

Unicité :

```text
(ccm_id, gf_id)
```

Cette table représente :

> la ou les fonctions réellement exercées par cette personne pour cette célébration.

Exemples :

```text
Chantre
Organiste
```

Une personne peut assurer plusieurs fonctions.

Les fonctions possibles générales restent dans :

```text
app_group
```

La table `c_celebration_member_function` stocke uniquement le choix concret de cette célébration.

Le service doit vérifier :

* que la fonction appartient au même groupe ;
* que cette fonction fait partie des fonctions possibles de la personne.

---

# 10. Déroulé : liste plate unique

Créer :

```text
am.c_flow_item
```

Alias :

```text
cfi
```

PK :

```text
cfi_id
```

Champs minimum :

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

FK :

```text
cc_id
    -> c_celebration.cc_id
    ON DELETE CASCADE
```

`kind` accepte uniquement :

```text
song
text
section
```

Unicité :

```text
(cc_id, position)
```

La position n'a aucune signification métier autre que l'ordre.

## Principe fondamental

Ne créer :

* aucun parent ;
* aucun enfant ;
* aucune section contenant des blocs ;
* aucune arborescence.

Le déroulé est :

> une liste strictement plate.

Les balises de section sont simplement des éléments de cette liste.

---

# 11. Propriétés communes du déroulé

`interface_title` est obligatoire.

Lorsque :

```text
show_on_sheet = TRUE
```

alors :

```text
trim(sheet_title)
```

doit être non vide.

Ajouter cette contrainte si elle peut être exprimée proprement en PostgreSQL/Django.

Pour les blocs chant et texte :

```text
show_on_sheet = TRUE
```

par défaut lors de leur création.

Pour une balise :

```text
show_on_sheet = FALSE
```

par défaut.

Ce défaut dépend du type et doit donc être appliqué par le service de création plutôt que par un défaut ambigu de la table générique.

---

# 12. Balises de section

Créer :

```text
am.c_section_marker
```

Alias :

```text
csm
```

PK :

```text
csm_id
```

Champs :

```text
csm_id
cfi_id
line_above
line_below
```

`cfi_id` est UNIQUE et référence :

```text
c_flow_item.cfi_id
    ON DELETE CASCADE
```

Une balise :

* n'est pas un conteneur ;
* se déplace seule ;
* se supprime seule.

Aucune FK parent/enfant ne doit être créée.

---

# 13. Blocs chants

Créer :

```text
am.c_song_block
```

Alias :

```text
csb
```

PK :

```text
csb_id
```

Champs principaux :

```text
csb_id
cfi_id

song_id
source_song_id
source_song_title
```

`cfi_id` :

```text
UNIQUE
FK -> c_flow_item.cfi_id
ON DELETE CASCADE
```

## 13.1. Référence vivante LSS

`song_id` référence le chant LSS actuel.

Inspecter le modèle/table LSS réellement présent avant de créer la FK.

Ne pas inventer le nom physique de la table.

Utiliser :

```text
ON DELETE SET NULL
```

## 13.2. Snapshot historique

Lorsqu'un chant est sélectionné, stocker également :

```text
source_song_id
source_song_title
```

Ces valeurs ne constituent pas la donnée éditoriale officielle du chant.

Elles servent uniquement à comprendre une référence cassée.

Lorsque le chant existe encore :

```text
song_id != NULL
```

LSS reste la source de vérité du titre et du texte.

Lorsque le chant a été supprimé :

```text
song_id = NULL
source_song_id != NULL
```

le bloc est une référence historique cassée.

Ne jamais supprimer le bloc automatiquement.

## 13.3. Bloc chant vide

Pendant la préparation, un bloc chant peut ne contenir encore aucun chant.

Dans ce cas :

```text
song_id = NULL
source_song_id = NULL
```

La validation doit refuser la célébration tant que le bloc reste vide.

---

# 14. Type principal et secondaire du bloc chant

Ne pas créer :

```text
primary_gt_id
secondary_gt_id
```

car cela casserait la convention de nommage des FK.

Créer une table d'association :

```text
am.c_song_block_tag
```

Alias :

```text
csbt
```

PK :

```text
csbt_id
```

Champs :

```text
csbt_id
csb_id
gt_id
role
tag_label_snapshot
```

FK :

```text
csb_id
    -> c_song_block.csb_id
    ON DELETE CASCADE
```

`gt_id` référence :

```text
common.group_tags.gt_id
```

La table `common.group_tags` reste externe à Django et n'est pas créée par `app_celebration`.

Si nécessaire, ajouter la FK PostgreSQL par `RunSQL`.

`role` accepte :

```text
primary
secondary
```

Contraintes :

```text
UNIQUE(csb_id, role)
```

Il doit exister exactement un `primary`.

Il peut exister zéro ou un `secondary`.

La présence du `primary` sera contrôlée par le service métier.

## Snapshot du tag

Conserver :

```text
tag_label_snapshot
```

afin qu'une célébration existante reste compréhensible si le tag utilisé est ensuite supprimé ou renommé.

La FK peut donc utiliser :

```text
ON DELETE SET NULL
```

Les types principal/secondaire d'une célébration représentent des **tags de groupe**.

Les tags communs LSS restent utiles pour les recherches et classifications générales mais ne doivent pas remplacer les tags liturgiques du groupe dans cette relation.

---

# 15. Blocs du chant sélectionnés

Lorsqu'un chant est choisi, AM doit mémoriser l'état des blocs/couplets de cette occurrence.

Créer :

```text
am.c_song_block_part
```

Alias :

```text
csbp
```

PK :

```text
csbp_id
```

Prévoir au minimum :

```text
csbp_id
csb_id

block_id
source_block_id

source_block_kind
source_position

selected
mandatory
```

`block_id` référence, lorsque possible, le bloc source LSS correspondant.

Inspecter le schéma LSS réel avant de créer cette FK.

Utiliser :

```text
ON DELETE SET NULL
```

`source_block_id` conserve l'identifiant historique.

Ne pas recopier le texte du chant dans AM.

LSS reste propriétaire du contenu éditorial.

## Initialisation

Lorsqu'un chant est choisi :

* créer l'état de ses blocs ;
* appliquer la configuration du type principal ;
* les refrains obligatoires ont :

  * `mandatory = TRUE`
  * `selected = TRUE`
* les autres blocs reçoivent leur valeur initiale depuis la configuration du groupe.

## Après initialisation

Les valeurs `selected` appartiennent désormais à cette occurrence.

Ne jamais les recalculer silencieusement lorsque :

* le tag du chant change ;
* le tag d'un couplet change ;
* le type principal du bloc change ;
* le type secondaire change ;
* le gabarit source évolue.

Recalcul uniquement :

* lorsqu'un nouveau chant remplace réellement l'ancien ;
* lors d'une réinitialisation totale du déroulé.

---

# 16. Blocs texte

Créer :

```text
am.c_text_block
```

Alias :

```text
ctb
```

PK :

```text
ctb_id
```

Champs minimum :

```text
ctb_id
cfi_id

source_mode

final_text

aelf_target
aelf_render_template
```

`cfi_id` :

```text
UNIQUE
FK -> c_flow_item.cfi_id
ON DELETE CASCADE
```

`source_mode` :

```text
free
aelf
```

`final_text` est :

```text
TEXT
```

et peut être vide pendant la préparation.

La validation exige :

```text
trim(final_text) != ""
```

## Bloc libre

En mode :

```text
free
```

les champs AELF peuvent être NULL.

## Bloc AELF

En mode :

```text
aelf
```

conserver :

* la cible AELF logique ;
* le template permettant de construire/importer le texte final.

Après import, `final_text` devient indépendant de la source.

---

# 17. Représentation d'une cible AELF

Ne pas revenir à une simple chaîne opaque du type :

```text
2-4
```

Utiliser un descripteur structuré.

Pour la V1, utiliser :

```text
JSONB
```

dans :

```text
aelf_target
```

Ce JSON peut notamment mémoriser :

* index de la messe ;
* libellé de la messe ;
* index du texte ;
* type du texte ;
* libellé ;
* identifiants éventuels proposés par AELF ;
* informations de fallback nécessaires.

Le code métier ne doit pas dépendre uniquement d'un index positionnel.

L'index peut cependant rester un fallback utile.

Cette structure JSON permet de gérer les variantes AELF sans créer de nombreuses colonnes nullable.

---

# 18. Cache AELF

Créer :

```text
am.c_aelf_cache
```

Alias :

```text
cac
```

PK :

```text
cac_id
```

Champs :

```text
cac_id
cc_id

aelf_date
payload

fetched_at
```

Optionnellement :

```text
source_endpoint
```

si utile au diagnostic.

`cc_id` :

```text
UNIQUE
FK -> c_celebration.cc_id
ON DELETE CASCADE
```

Une célébration possède au maximum un cache AELF actif.

## 18.1. Payload

Utiliser un `JSONField` Django/PostgreSQL :

```text
payload JSONB
```

Conserver l'intégralité de la réponse utile reçue de l'API.

Ne pas extraire automatiquement chaque propriété vers une table relationnelle.

## 18.2. Date propre au cache

`c_aelf_cache.aelf_date` indique :

> la date du payload actuellement stocké.

Cette valeur est volontairement distincte de :

```text
c_celebration.aelf_date
```

Exemple :

1. cache actuel = dimanche 13 septembre ;
2. utilisateur modifie `c_celebration.aelf_date` vers dimanche 20 septembre ;
3. aucun refresh automatique ;
4. le cache indique toujours le 13 septembre ;
5. l'application peut détecter la différence et proposer un refresh.

## 18.3. Refresh

Le refresh :

* remplace le payload ;
* met à jour la date du cache ;
* met à jour `fetched_at`.

Il ne modifie jamais automatiquement :

```text
c_text_block.final_text
```

---

# 19. Stratégie technique AELF

Ne pas créer un système qui analyse des payloads d'exemple pour générer dynamiquement le schéma PostgreSQL.

La stratégie recommandée est :

```text
API AELF
    ↓
payload JSON brut
    ↓
c_aelf_cache.payload JSONB
    ↓
adaptateur Python
    ↓
résolution des cibles
```

Créer un composant applicatif dédié, par exemple conceptuellement :

```text
AelfPayloadAdapter
```

Son rôle :

* lire la structure AELF connue ;
* exposer les messes disponibles ;
* exposer leurs textes ;
* résoudre un `aelf_target` ;
* tolérer des champs supplémentaires inconnus ;
* permettre des fallbacks lorsque nécessaire.

Le parser ne doit pas être inutilement strict.

Une nouvelle propriété AELF inconnue ne doit pas rendre tout le payload invalide.

## Tests AELF

Conserver plusieurs payloads réels représentatifs sous forme de fixtures de tests.

Prévoir au minimum des cas correspondant à :

* dimanche ordinaire ;
* plusieurs messes le même jour ;
* messe anticipée ;
* Noël ou autre journée comportant plusieurs formulaires ;
* lectures optionnelles ;
* psaume/cantique ;
* cas comportant des éléments supplémentaires.

Ces fixtures servent à :

> vérifier l'adaptateur.

Elles ne servent pas à :

> générer le schéma de la base.

Si AELF modifie réellement son format un jour :

* adapter le parser ;
* ajouter/modifier les fixtures ;
* ne pas migrer toute la BDD simplement parce que le JSON externe a évolué.

---

# 20. Gabarits de célébration

Créer :

```text
am.c_template
```

Alias :

```text
ct
```

PK :

```text
ct_id
```

Champs minimum :

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

`scope` :

```text
global
group
```

Contraintes :

```text
scope = global -> gg_id IS NULL
scope = group  -> gg_id IS NOT NULL
```

Un gabarit global est administré au niveau du site.

Un gabarit de groupe appartient à un seul groupe.

Les gabarits ne sont pas partagés directement entre groupes en V1.

Prévoir une unicité de nom insensible à la casse :

* dans les gabarits globaux ;
* dans chaque groupe.

---

# 21. Éléments d'un gabarit

Créer une liste plate équivalente au déroulé réel :

```text
am.c_template_item
```

Alias :

```text
cti
```

PK :

```text
cti_id
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
```

FK :

```text
ct_id
    -> c_template.ct_id
    ON DELETE CASCADE
```

Unicité :

```text
(ct_id, position)
```

`kind` :

```text
song
text
section
```

Même philosophie que le déroulé réel :

> liste plate, aucune relation parent/enfant.

---

# 22. Spécialisations des éléments de gabarit

Créer :

```text
c_template_song_block
c_template_text_block
c_template_section_marker
```

Avec les alias et PK correspondants :

```text
ctsb_id
cttb_id
ctsm_id
```

Chaque spécialisation possède une FK UNIQUE :

```text
cti_id
```

vers :

```text
c_template_item.cti_id
```

avec :

```text
ON DELETE CASCADE
```

---

# 23. Bloc chant d'un gabarit

Un bloc chant de gabarit :

> ne contient jamais de chant LSS précis.

Il conserve uniquement :

* un type principal ;
* éventuellement un type secondaire.

Créer :

```text
am.c_template_song_tag
```

Alias :

```text
ctst
```

PK :

```text
ctst_id
```

Champs :

```text
ctst_id
ctsb_id
gt_id
role
tag_label
```

`role` :

```text
primary
secondary
```

Unicité :

```text
(ctsb_id, role)
```

## Gabarit de groupe

Pour un gabarit de groupe :

```text
gt_id
```

peut référencer directement :

```text
common.group_tags.gt_id
```

## Gabarit global

Un gabarit global n'appartient à aucun groupe.

Il ne peut donc pas dépendre d'un `gt_id` propre à un groupe particulier.

Pour un gabarit global :

```text
gt_id = NULL
tag_label = valeur logique attendue
```

Exemple :

```text
Kyrie
```

Lorsqu'un gabarit global est appliqué à un groupe, le service tente de résoudre ce libellé vers les tags de ce groupe.

Ne jamais créer automatiquement un tag de groupe de manière silencieuse.

Si aucune correspondance n'existe, l'application devra demander une résolution explicite ou signaler le gabarit incomplet.

L'UX exacte pourra être définie plus tard.

Le schéma doit seulement rendre ce cas possible.

---

# 24. Bloc texte d'un gabarit

`c_template_text_block` doit pouvoir conserver :

```text
source_mode
default_text
aelf_target
aelf_render_template
```

Un bloc texte libre peut donc proposer du contenu initial.

Un bloc AELF peut définir :

* une cible ;
* la manière de construire son texte final.

Lorsqu'une célébration est créée depuis le gabarit :

> ces informations sont copiées dans le bloc réel.

Après création :

> le bloc réel est indépendant du gabarit.

Modifier ultérieurement le gabarit ne modifie jamais automatiquement les célébrations existantes.

---

# 25. Réinitialisation depuis un gabarit

Changer le `ct_id` d'une célébration existante est une opération métier destructive.

Ne jamais implémenter cela comme un simple :

```text
UPDATE ct_id
```

Le service doit :

1. vérifier que la célébration est modifiable ;
2. supprimer le déroulé actuel ;
3. rattacher le nouveau `ct_id` ;
4. recréer tous les `c_flow_item` ;
5. recréer leurs spécialisations ;
6. recopier les paramètres du gabarit ;
7. recalculer les sélections initiales nécessaires.

Cette opération doit être atomique.

Utiliser :

```text
transaction.atomic()
```

Une erreur pendant la reconstruction doit restaurer l'ancien état.

---

# 26. Gabarits d'impression

Créer dans `app_celebration` :

```text
am.c_print_template
```

Alias :

```text
cpt
```

PK :

```text
cpt_id
```

Champs minimum :

```text
cpt_id
gg_id

name
content

is_primary

created_at
updated_at
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

`content` :

```text
TEXT
```

Unicité insensible à la casse :

```text
(gg_id, name)
```

Il ne peut exister qu'un seul :

```text
is_primary = TRUE
```

par groupe.

Utiliser une contrainte unique partielle PostgreSQL lorsque Django permet de l'exprimer proprement.

Les gabarits d'impression sont des objets de `app_celebration`.

Ils ne doivent pas être déplacés dans `app_group`.

---

# 27. Feuilles de messe

Créer :

```text
am.c_sheet
```

Alias :

```text
cs
```

PK :

```text
cs_id
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

FK :

```text
cc_id
    -> c_celebration.cc_id
    ON DELETE CASCADE
```

FK nullable :

```text
cpt_id
    -> c_print_template.cpt_id
    ON DELETE SET NULL
```

`content` :

```text
TEXT
```

## Unicité

Deux feuilles d'une même célébration ne peuvent avoir le même nom.

Utiliser une unicité insensible à la casse.

Une seule feuille peut être :

```text
is_primary = TRUE
```

par célébration.

---

# 28. Génération initiale des feuilles

La validation d'une célébration déclenche la génération des feuilles.

Pour une célébration partagée :

> utiliser uniquement les gabarits d'impression du groupe créateur.

## Si le groupe possède des gabarits

Créer :

> une feuille par gabarit.

Le gabarit principal génère la feuille principale.

## Si le groupe n'en possède aucun

Créer automatiquement :

> une feuille vide principale.

Ne pas stocker un PDF pré-généré dans la migration actuelle.

Le PDF sera une sortie générée à partir de la feuille.

---

# 29. Autonomie des feuilles

Après génération :

> la feuille est indépendante de son gabarit.

Modifier le gabarit ne modifie pas les feuilles existantes.

La référence `cpt_id` sert uniquement notamment à :

* connaître l'origine ;
* permettre une réinitialisation explicite.

La suppression d'un gabarit :

```text
cpt_id -> NULL
```

mais ne supprime jamais ses anciennes feuilles.

---

# 30. Dévalidation

Lorsqu'un Responsable dévalide une célébration future ou du jour :

1. vérifier qu'elle peut encore être dévalidée ;
2. supprimer toutes ses feuilles ;
3. remettre :

   ```text
   validated_at = NULL
   ```

Cette opération doit être atomique.

Lors de la validation suivante :

> les feuilles sont recréées depuis les versions actuelles des gabarits d'impression.

---

# 31. Feuille principale

Une feuille principale ne doit pas pouvoir être supprimée directement lorsqu'elle est la feuille principale active.

Pour la supprimer :

1. désigner une autre feuille principale ;
2. supprimer ensuite l'ancienne.

Cette règle est portée par le service métier.

Ne pas utiliser une FK circulaire depuis `c_celebration` vers `c_sheet`.

Le booléen :

```text
c_sheet.is_primary
```

avec contrainte d'unicité suffit.

---

# 32. Droits sur les feuilles

Le rôle de groupe à utiliser est :

```text
responsable_impression
```

Ne pas recréer l'ancien nom :

```text
éditeur de feuilles
```

Les personnes pouvant gérer les feuilles sont :

* les Responsables du groupe créateur ;
* les Responsables impression du groupe créateur.

Elles peuvent gérer les feuilles uniquement pour une célébration :

* validée ;
* du jour ;
* future.

Un Responsable impression ne gagne aucun droit sur :

* le déroulé ;
* le planning ;
* la validation ;
* les membres.

Tous les Membres avec compte ayant accès à la célébration peuvent :

* consulter la feuille ;
* générer le PDF.

Les Membres AM n'ont évidemment aucun accès logiciel.

---

# 33. Validation de la célébration

La validation doit être un service transactionnel.

Conditions :

* utilisateur Responsable du groupe créateur ;
* célébration pas passée ;
* célébration actuellement non validée ;
* tous les blocs chants possèdent un chant ;
* tous les blocs textes possèdent un `final_text` non vide après `trim()`.

Le contrôle est volontairement simple.

Ne pas ajouter :

* validation liturgique automatique ;
* analyse sémantique ;
* LLM ;
* contrôle de longueur ;
* validation intelligente du contenu.

Si tout est correct :

1. définir `validated_at` ;
2. générer les feuilles ;
3. valider la transaction.

Si la génération des feuilles échoue :

> la validation entière doit être rollbackée.

---

# 34. Célébration passée

La règle repose uniquement sur :

```text
celebration_date
```

et non sur l'heure.

Une célébration ayant lieu aujourd'hui reste modifiable aujourd'hui, même après son heure prévue.

À partir du lendemain :

* aucune modification du déroulé ;
* aucune modification des informations structurantes ;
* aucune dévalidation ;
* aucune édition de feuille ;
* aucune modification des affectations.

Ne pas stocker :

```text
is_past
```

Cet état est calculé.

Utiliser le fuseau horaire configuré pour l'application.

---

# 35. Archivage

Tous les Membres ayant accès à la célébration peuvent :

* archiver ;
* désarchiver.

L'archivage ne change pas :

* la validation ;
* le droit d'édition du déroulé ;
* la date ;
* le planning.

Il protège uniquement la célébration de :

* la suppression manuelle ;
* la purge automatique.

Une célébration archivée peut être future.

`archived_at` suffit à représenter l'état actuel.

---

# 36. Suppression et conservation

La politique de conservation demeure dans :

```text
app_group
```

notamment :

```text
celebration_retention_months
```

`app_celebration` applique cette politique.

Pour une célébration partagée, utiliser en V1 :

> la politique du groupe créateur/responsable.

La purge automatique supprime les célébrations :

* non archivées ;
* ayant dépassé la conservation du groupe créateur.

La suppression d'une célébration cascade vers :

* groupes participants ;
* affectations ;
* fonctions d'affectation ;
* déroulé ;
* blocs ;
* cache AELF ;
* feuilles.

---

# 37. Purge RGPD des affectations

La purge RGPD des personnes est distincte de la purge des célébrations.

Après le délai global prévu :

> supprimer les `c_celebration_member` concernés.

La cascade supprime leurs :

```text
c_celebration_member_function
```

Cette purge s'applique même si :

```text
archived_at IS NOT NULL
```

Une célébration archivée peut donc rester dans les annales sans conserver les personnes qui y étaient affectées.

Ne pas stocker ailleurs un snapshot nominatif de ces membres dans `app_celebration`.

---

# 38. Célébrations partagées

Une célébration partagée reste :

> un seul `c_celebration`.

Les groupes supplémentaires sont uniquement des lignes :

```text
c_celebration_group
```

Le groupe créateur :

```text
c_celebration.gg_id
```

reste responsable.

En V1 :

* pas de transfert du groupe créateur ;
* seul le groupe créateur peut ajouter un autre groupe ;
* un groupe participant peut quitter ;
* le groupe créateur peut retirer un participant ;
* seuls les Responsables du créateur peuvent supprimer la célébration ;
* seuls les Responsables du créateur peuvent valider/dévalider.

Lorsqu'un groupe participant est retiré :

```text
c_celebration_group
```

est supprimé.

La cascade doit retirer :

* ses `c_celebration_member` ;
* leurs fonctions ;
* leurs droits `can_edit`.

Les données des autres groupes restent intactes.

---

# 39. Ressources de déroulé d'une célébration partagée

Le déroulé étant unique, les ressources permettant de le construire doivent être cohérentes.

En V1, considérer le :

```text
groupe créateur
```

comme contexte de référence pour :

* le gabarit de groupe ;
* les tags principaux/secondaires ;
* le recueil utilisé par le sélecteur normal ;
* les gabarits d'impression.

Les autres groupes participants peuvent contribuer au déroulé lorsqu'ils possèdent les droits requis, mais ils travaillent sur :

> le même déroulé canonique.

Ne pas mélanger simultanément les tags propres à plusieurs groupes dans un même bloc.

---

# 40. Autocomplétion

L'autocomplétion est un service métier.

Elle n'exige aucune table dédiée.

Deux modes :

```text
complete_empty
overwrite
```

plus annulation côté interface.

## `complete_empty`

Ne remplit que les éléments vides.

Ne remplace pas :

* un chant déjà choisi ;
* un texte final déjà renseigné.

## `overwrite`

Peut :

* remplacer un chant ;
* remplacer un texte final.

Si un chant est réellement remplacé :

> ses `c_song_block_part` sont recréés avec la sélection initiale du nouveau chant.

Lancer simplement l'autocomplétion ne recalcule jamais les coches d'un chant déjà présent.

---

# 41. Dépendances externes

`app_celebration` dépend de plusieurs structures qu'il ne possède pas :

```text
am.g_group
am.g_group_member
am.g_function

common.group_tags

LSS chants
LSS blocs de chants
```

Ne pas créer de migrations sur :

```text
users
lss
common
```

dans cette tâche.

Les modèles externes nécessaires doivent être :

```text
managed = False
```

lorsqu'ils représentent des tables hors propriété de Django AM.

Lorsque Django ne permet pas de créer proprement une FK cross-schema :

> créer uniquement la contrainte PostgreSQL nécessaire via `RunSQL`.

Toujours inspecter le schéma physique existant avant d'écrire une FK LSS.

---

# 42. Cascades principales

Utiliser :

```text
c_celebration
    CASCADE -> c_celebration_group
    CASCADE -> c_flow_item
    CASCADE -> c_aelf_cache
    CASCADE -> c_sheet

c_celebration_group
    CASCADE -> c_celebration_member

c_celebration_member
    CASCADE -> c_celebration_member_function

c_flow_item
    CASCADE -> c_song_block
    CASCADE -> c_text_block
    CASCADE -> c_section_marker

c_song_block
    CASCADE -> c_song_block_tag
    CASCADE -> c_song_block_part

c_template
    CASCADE -> c_template_item

c_template_item
    CASCADE -> spécialisations du gabarit

c_print_template
    SET NULL -> c_sheet.cpt_id

c_template
    SET NULL -> c_celebration.ct_id

LSS song
    SET NULL -> c_song_block.song_id

LSS block
    SET NULL -> c_song_block_part.block_id

common.group_tags
    SET NULL -> références des blocs/gabarits conservant un snapshot
```

---

# 43. Ne pas dupliquer l'information inutilement

Ne pas stocker dans `app_celebration` :

* nom/prénom/email des Membres avec compte ;
* identité des auteurs de validation/archive ;
* nom du groupe créateur en snapshot ;
* textes officiels LSS des chants ;
* données du recueil ;
* liste générale des fonctions d'un membre ;
* rôles du groupe ;
* durée de conservation du groupe ;
* PDF pré-généré ;
* structure relationnelle interne du JSON AELF.

Les seules exceptions historiques prévues ici concernent notamment :

```text
source_song_id
source_song_title
source_block_id
tag_label_snapshot
```

qui permettent à un objet de célébration de rester lisible après disparition d'une source.

---

# 44. Tests minimums

Créer des tests couvrant au minimum :

* création simple d'une célébration ;
* groupe créateur automatiquement participant ;
* unicité groupe/date/heure/lieu ;
* conflit lors de l'ajout d'un groupe à une célébration partagée ;
* retrait d'un groupe supprimant seulement ses affectations ;
* affectation Membre avec compte ;
* affectation Membre AM ;
* impossibilité pour un Membre AM d'avoir `can_edit = TRUE` ;
* plusieurs fonctions possibles pour une même affectation ;
* membre et fonction du même groupe ;
* Membre modificateur incapable de valider ;
* Responsable capable de valider ;
* groupe participant non créateur incapable de valider ;
* verrouillage après validation ;
* dévalidation supprimant toutes les feuilles ;
* impossibilité de dévalider une célébration passée ;
* célébration du jour encore modifiable ;
* archivage protégeant de la suppression ;
* purge RGPD des affectations malgré l'archive ;
* déroulé strictement plat ;
* unicité des positions ;
* suppression d'une balise sans effet sur les autres blocs ;
* bloc chant vide empêchant la validation ;
* texte vide empêchant la validation ;
* suppression LSS laissant une référence historique cassée ;
* changement de tags n'altérant pas les coches existantes ;
* type secondaire n'altérant pas les coches ;
* remplacement du chant recalculant ses blocs ;
* refresh AELF n'altérant jamais `final_text` ;
* changement de `aelf_date` ne rafraîchissant pas automatiquement le cache ;
* changement de gabarit reconstruisant complètement le déroulé ;
* modification d'un gabarit n'altérant pas une célébration existante ;
* unicité des noms de gabarits d'impression ;
* un seul gabarit d'impression principal par groupe ;
* unicité des noms de feuilles ;
* une seule feuille principale ;
* suppression d'un gabarit d'impression laissant ses feuilles intactes ;
* Responsable impression pouvant éditer une feuille mais pas le déroulé ;
* groupe participant pouvant lire une feuille mais pas l'éditer.

---

# 45. Tests AELF

Créer un dossier de fixtures représentatives.

Le but est de pouvoir détecter rapidement une évolution éventuelle de l'API AELF.

Tester au minimum :

* lecture des messes disponibles ;
* résolution d'un texte simple ;
* plusieurs messes le même jour ;
* plusieurs textes similaires ;
* fallback par position ;
* présence de propriétés inconnues ;
* propriété facultative absente ;
* refresh du cache ;
* cible devenue introuvable.

Un champ supplémentaire inconnu dans un payload AELF :

> ne doit pas provoquer une erreur globale.

---

# 46. Ce qu'il ne faut pas faire

Ne pas :

* créer une table de planning dupliquant la célébration ;
* créer une célébration par groupe pour une célébration partagée ;
* créer une hiérarchie de sections ;
* supprimer un bloc chant lorsque son chant LSS disparaît ;
* recopier le texte des chants LSS dans le déroulé ;
* recalculer automatiquement les couplets après chaque modification ;
* modifier un texte final lors d'un refresh AELF ;
* normaliser tout le payload AELF en tables SQL ;
* construire dynamiquement le schéma PostgreSQL depuis les payloads AELF ;
* enregistrer l'auteur d'une validation ou d'un archivage ;
* donner la validation à un simple Membre modificateur ;
* permettre au Responsable impression de modifier le déroulé ;
* créer les gabarits dans `app_group` ;
* créer les gabarits d'impression dans `app_group` ;
* stocker le PDF comme donnée métier de base ;
* créer des tables dans `common` ou `lss` depuis les migrations de cette app.

---

# 47. Livrables attendus

À la fin de la tâche, fournir :

1. les modèles Django `app_celebration` ;
2. les migrations initiales ;
3. les éventuels `RunSQL` pour les FK cross-schema ;
4. les services transactionnels nécessaires aux invariants non exprimables par simple contrainte ;
5. les tests ;
6. les fixtures AELF ;
7. l'adaptateur de lecture AELF minimal nécessaire aux tests ;
8. un inventaire des tables créées ;
9. un tableau des FK et stratégies `CASCADE` / `SET NULL` ;
10. la liste des règles garanties par PostgreSQL ;
11. la liste des règles garanties par les services Django.

L'application `app_celebration` ne possède actuellement pas encore de modèle métier à préserver.

Il est donc possible de créer une véritable migration :

```text
0001_initial
```

propre.

---

# 48. Vérifications finales

Exécuter au minimum :

```text
python manage.py makemigrations --check
python manage.py migrate
python manage.py check
pytest
ruff check .
```

ou les commandes équivalentes définies actuellement dans le projet.

Vérifier également :

* les noms physiques des tables ;
* les noms physiques des PK ;
* les noms physiques des FK ;
* les schémas PostgreSQL ciblés ;
* les contraintes uniques ;
* les cascades.

---

# 49. Principe architectural final

Conserver cette séparation :

```text
app_group
    définit les personnes, rôles, fonctions
    et paramètres durables du groupe

app_celebration
    définit ce qui est réellement célébré
    qui y participe
    dans quelle fonction
    son déroulé
    ses sources AELF
    sa validation
    ses gabarits
    ses feuilles

common
    porte les tags partagés

LSS
    reste propriétaire du contenu officiel des chants
```

Et surtout :

> une célébration réelle reste un seul objet canonique, même lorsqu'elle concerne plusieurs groupes.

Le planning doit être reconstruit à partir de cet objet et non l'inverse.
