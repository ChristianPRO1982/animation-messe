# app_planning — Contrat BDD V1

Ce document est le contrat BDD canonique de `app_planning` pour la V1.

`app_planning` est une app de services, vues, permissions et selectors. Elle ne
possede pas de tables persistantes en V1.

Sources consolidees :

- `docs/SFD-02-planning.md`
- `docs/app_group/models.md`
- `docs/app_celebration/models.md`

---

# 1. Principe de non-possession

`app_planning` ne cree aucune table proprietaire en V1.

Sont explicitement exclus :

- aucune table `p_*` ;
- aucune entite persistante `PlanningLine` ;
- aucune entite persistante `PlanningCell` ;
- aucune entite persistante `PlanningAnimation` ;
- aucune entite persistante `AnimationEntry` ;
- aucune table miroir des celebrations ;
- aucune table miroir des cellules de planning.

La responsabilite de `app_planning` est de construire, afficher, modifier sous
permission et valider une vue de planning a partir des tables possedees par
`app_group` et `app_celebration`.

---

# 2. Proprietaires reels des donnees

## 2.1 Ligne de planning

Une ligne de planning correspond a une celebration.

Table proprietaire :

- app : `app_celebration`
- schema PostgreSQL : `am`
- table physique : `am.c_celebration`
- alias Django cible : `Celebration`
- PK : `cc_id`

`app_planning` ne cree pas de ligne autonome.

## 2.2 Groupe affiche dans le planning

Le rattachement d'une celebration a un groupe est porte par :

- app : `app_celebration`
- schema PostgreSQL : `am`
- table physique : `am.c_celebration_group`
- alias Django cible : `CelebrationGroup`
- PK : `ccg_id`
- FK principale : `cc_id -> am.c_celebration.cc_id`
- FK principale : `gg_id -> am.g_group.gg_id`

## 2.3 Cellule de planning

Une cellule de planning correspond a la participation d'un membre ou Membre AM a
une celebration pour un groupe donne.

Table proprietaire :

- app : `app_celebration`
- schema PostgreSQL : `am`
- table physique : `am.c_celebration_member`
- alias Django cible : `CelebrationMember`
- PK : `ccm_id`

Champs contractuels utiles a `app_planning` :

- `ccg_id` : FK vers `am.c_celebration_group.ccg_id`, suppression `CASCADE` ;
- `ggm_id` : FK vers `am.g_group_member.ggm_id`, suppression `CASCADE` ;
- `gps_id` : FK vers `am.g_planning_state.gps_id`, suppression protegee par
  desactivation fonctionnelle cote `app_group` ;
- `can_edit` : booleen de controle fin cote planning ;
- `created_at` ;
- `updated_at`.

La suppression RGPD d'un `g_group_member` supprime donc ses cellules de celebration.

## 2.4 Fonction selectionnee dans une cellule

Les fonctions choisies pour une cellule sont portees par :

- app : `app_celebration`
- schema PostgreSQL : `am`
- table physique : `am.c_celebration_member_function`
- alias Django cible : `CelebrationMemberFunction`
- PK : `ccmf_id`
- FK principale : `ccm_id -> am.c_celebration_member.ccm_id`, suppression `CASCADE` ;
- FK principale : `gf_id -> am.g_function.gf_id`, suppression protegee par
  desactivation fonctionnelle cote `app_group`.

## 2.5 Etats de planning

Les etats de cellule sont parametrables par groupe.

Table proprietaire :

- app : `app_group`
- schema PostgreSQL : `am`
- table physique : `am.g_planning_state`
- alias Django cible : `PlanningState`
- PK : `gps_id`

`app_planning` lit ces etats et applique leur role fonctionnel :

- `state_kind = selection` : personne retenue lors de la validation planning ;
- `state_kind = default` : etat attribue aux nouvelles cellules ;
- autres etats : information sans effet automatique.

## 2.6 Regles de generation

Les parametres durables de generation appartiennent a `app_group`.

Tables proprietaires :

- `am.g_celebration_rule` : regles regulieres ;
- `am.g_special_date_rule` : dates particulieres ;
- `am.g_special_date_celebration` : celebrations creees par une date
  particuliere ;
- `am.g_location` : lieux.

`app_planning` consomme ces tables pour creer des `am.c_celebration` et `am.c_celebration_group`.

---

# 3. Services attendus cote app_planning

## 3.1 Generation des celebrations futures

Le service de generation :

- recoit un groupe et une periode ;
- lit `g_celebration_rule`, `g_special_date_rule`, `g_special_date_celebration` et `g_location` ;
- cree les celebrations manquantes dans `app_celebration` ;
- respecte l'identification fonctionnelle groupe + date reelle + heure + lieu ;
- reste incremental et idempotent ;
- ne modifie pas retroactivement les celebrations deja generees lorsqu'une regle est modifiee, supprimee ou desactivee.

Pour les dates particulieres, `collision_mode` est explicite :

- `add` : les celebrations de la date particuliere s'ajoutent aux occurrences
  regulieres ;
- `replace` : les celebrations de la date particuliere remplacent les
  occurrences regulieres du meme groupe sur la date concernee.

## 3.2 Construction du tableau planning

Le selector de tableau :

- lit les lignes depuis `c_celebration` ;
- filtre par groupe via `c_celebration_group` ;
- lit les colonnes depuis `g_group_member` ;
- lit les cellules depuis `c_celebration_member` ;
- lit les fonctions selectionnees depuis `c_celebration_member_function` ;
- lit les etats et couleurs depuis `g_planning_state`.

## 3.3 Construction du calendrier

Le selector calendrier lit les celebrations depuis `app_celebration`.

Il peut enrichir l'affichage avec les informations de groupe, lieu, etat de
validation planning et presence de cellules incompletes.

## 3.4 Creation des cellules manquantes

Le service cree les cellules manquantes pour les membres actifs du groupe
lorsque la celebration n'est pas validee cote planning.

Les valeurs par defaut viennent de `app_group` :

- etat `default` du groupe ;
- premiere fonction possible selon l'ordre du groupe ;
- `can_edit` selon les droits applicables.

## 3.5 Modification autorisee des cellules

Une cellule peut etre modifiee si :

- la celebration n'est pas validee cote planning ;
- la celebration n'est pas passee ;
- l'utilisateur dispose du droit sur cette cellule ;
- `can_edit` ne bloque pas la modification.

Un Responsable peut modifier toutes les cellules ouvertes de son groupe.

Un membre avec compte peut modifier sa cellule et les cellules des Membres AM selon les regles fonctionnelles de `SFD-02`.

## 3.6 Arrivee d'un nouveau membre

Lorsqu'un Membre ou Membre AM devient actif dans un groupe, le service cree ses
cellules manquantes uniquement pour les celebrations :

- futures ;
- rattachees au groupe ;
- non validees cote planning.

Il ne cree rien sur les celebrations passees ni sur les celebrations deja
validees cote planning.

Cette operation est idempotente.

## 3.7 Validation et devalidation planning

La validation planning vit dans `app_celebration`.

Champs contractuels :

- `c_celebration.planning_validated_at` ;
- `c_celebration.planning_validated_by_ggm_id`.

La validation :

- verrouille les cellules courantes de la celebration ;
- considere les cellules en etat `selection` comme les participations retenues ;
- ne cree pas de seconde equipe separee ;
- ne copie pas les cellules vers une table distincte ;
- ne modifie pas la validation de celebration (`validated_at`).

La devalidation :

- efface les champs de validation planning ;
- rouvre les memes cellules ;
- ne supprime aucune donnee dans une equipe separee, puisqu'aucune equipe separee n'existe en V1.

La revalidation valide l'etat courant des memes cellules. Elle ne fait ni
fusion, ni resynchronisation avec une deuxieme source.

---

# 4. Contraintes transactionnelles

Les operations suivantes doivent etre atomiques :

- generation d'une periode ;
- creation des cellules manquantes d'une celebration ;
- creation des cellules d'un nouveau membre ;
- modification d'une cellule et de ses fonctions ;
- validation planning ;
- devalidation planning.

Les protections contre les doublons vivent dans les contraintes de `app_celebration` et dans les validations service de `app_planning`.

---

# 5. Ce que app_planning ne doit pas faire

`app_planning` ne doit pas :

- creer une table `p_planning` ;
- creer une table de lignes ou cellules paralleles ;
- dupliquer les membres, fonctions, etats ou lieux ;
- posseder les regles durables de generation ;
- posseder les celebrations ;
- posseder une equipe separee des cellules de celebration ;
- introduire un champ `status` de celebration ;
- synchroniser deux representations concurrentes d'une meme participation.

---

# 6. Tests cibles

Les tests de `app_planning` devront verifier :

- generation idempotente ;
- application de `collision_mode add` ;
- application de `collision_mode replace` ;
- absence d'effet retroactif apres modification d'une regle ;
- creation des cellules manquantes ;
- creation idempotente des cellules lors de l'arrivee d'un nouveau membre ;
- permissions de modification cellule par cellule ;
- verrouillage apres validation planning ;
- reouverture apres devalidation ;
- impossibilite de devalider une celebration passee ;
- purge RGPD d'un `g_group_member` et suppression en cascade de ses cellules ;
- passage a `NULL` de `planning_validated_by_ggm_id` si le validateur disparait ;
- absence de creation de tables `p_*`.
