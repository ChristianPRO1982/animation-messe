# Directive Codex — `app_planning`

## 1. Objectif

Mettre en place la structure nécessaire au fonctionnement du planning d’Animation Messe.

Attention : la conception a été simplifiée par rapport à certaines versions actuelles des SFD.

Le principe directeur désormais fixé est :

> **Le planning n’est pas une entité métier autonome.**

> **La célébration est la source unique des données affichées dans le planning.**

Le planning est :

* une vue des célébrations ;
* un outil de génération de célébrations futures ;
* un outil de modification des participations ;
* un outil de verrouillage des participations via une validation de planning.

Il ne doit pas dupliquer les données des célébrations.

---

# 2. Terminologie

Le terme métier canonique est désormais :

```text
célébration
```

Ne pas utiliser `animation` pour désigner une entité métier.

Le mot animation reste acceptable uniquement dans des expressions telles que :

```text
fonction d'animation
équipe d'animation
animation liturgique
```

Ne créer aucune table ou modèle métier nommé :

```text
Animation
PlanningAnimation
AnimationEntry
```

Une ligne de planning correspond toujours à une célébration.

---

# 3. Répartition des responsabilités

La frontière doit être :

```text
app_group
    paramètres durables du groupe
    règles de génération
    états du planning
    fonctions
    lieux
    dates particulières

app_celebration
    célébration réelle
    personnes de la célébration
    état de planning de chaque personne
    fonctions choisies pour cette célébration
    validation du planning
    validation de la célébration

app_planning
    vues
    services
    génération
    calendrier
    tableau de planning
    règles de permissions liées au planning
```

Cette répartition est volontaire.

`app_planning` ne doit pas créer un second stockage parallèle aux célébrations.

---

# 4. Conséquence importante : pas de tables `p_*` en V1

Ne créer aucune table PostgreSQL `p_*` simplement parce qu'une application Django `app_planning` existe.

En particulier, ne pas créer :

```text
p_planning
p_planning_line
p_planning_cell
p_planning_member
p_planning_validation
p_animation
```

Ces concepts seraient des duplications.

`app_planning` peut parfaitement être une application Django sans modèle persistant propre.

Elle utilisera :

* les modèles de `app_group` ;
* les modèles de `app_celebration`.

Si un besoin futur justifie réellement une donnée exclusivement propre au planning, une table `p_*` pourra être ajoutée plus tard.

Ne pas anticiper ce besoin.

---

# 5. Paramètres du planning : `app_group`

Les paramètres durables servant au planning appartiennent à `app_group`.

Ils nécessitent donc une migration additive de `app_group` si les premières migrations de cette application ont déjà été créées.

Ne pas réécrire une migration déjà appliquée.

---

# 6. États du planning

Créer dans `app_group` :

```text
am.g_planning_state
```

Alias :

```text
gps
```

PK :

```text
gps_id
```

Champs minimum :

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

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

`kind` accepte :

```text
selection
default
custom
```

## État `selection`

Chaque groupe possède exactement un état :

```text
kind = selection
```

Il correspond à l'ancien « état 1 ».

Exemple de libellé :

```text
Disponible
```

Son nom est libre.

Sa signification métier ne dépend jamais du nom.

Lorsqu'une ligne de planning est validée, une personne dans cet état constitue un membre retenu pour cette célébration.

## État `default`

Chaque groupe possède exactement un état :

```text
kind = default
```

Il correspond à l'ancien « état 2 ».

C'est l'état attribué aux nouvelles cellules/personnes lors de leur création.

Exemple de libellé :

```text
Indisponible
```

Son nom est également libre.

## États `custom`

Le groupe peut créer autant d'états supplémentaires qu'il le souhaite.

Ils n'ont aucune conséquence métier automatique.

## Contraintes

Un groupe doit toujours avoir :

* exactement un état `selection` actif ;
* exactement un état `default` actif.

Utiliser des contraintes/index partiels PostgreSQL lorsque pertinent et compléter par des contrôles métier Django.

Une modification de nom ou de couleur ne change jamais le comportement de l'état.

Une couleur n'a aucune signification métier.

---

# 7. Suppression des états

Un état déjà utilisé dans une célébration ne doit pas être supprimé physiquement tant qu'il est référencé.

La suppression fonctionnelle d'un état devient donc :

```text
is_active = FALSE
```

Il n'est alors plus proposé pour les nouvelles utilisations.

Les anciennes célébrations continuent à pouvoir afficher cet état.

Exception :

si les données relatives à une personne doivent être supprimées pour raison RGPD, les données personnelles de cette personne peuvent disparaître même si elles faisaient partie d'un ancien planning.

La RGPD est prioritaire sur la conservation historique nominative.

---

# 8. Fonctions

Les fonctions ont déjà été déplacées vers `app_group`.

Ne pas recréer de fonction dans `app_planning`.

Réutiliser :

```text
g_function
g_group_member_function
```

Une fonction décrit ce que la personne peut assurer habituellement :

```text
Chantre
Organiste
Maître de chœur
Responsable de groupe musical
```

Une personne peut posséder plusieurs fonctions possibles.

Les fonctions restent configurables par groupe.

---

# 9. Lieux

Les lieux habituels sont également portés par `app_group`.

Réutiliser :

```text
g_location
```

Une règle de génération peut référencer un lieu habituel.

Une célébration générée doit toutefois recevoir ses propres données de lieu.

Après génération, la célébration devient autonome.

La modification ultérieure du lieu paramétré ne doit jamais déplacer automatiquement les célébrations déjà générées.

---

# 10. Règles régulières de célébration

Les règles de génération constituent des paramètres durables du groupe.

Créer dans `app_group` :

```text
am.g_celebration_rule
```

Alias :

```text
gcr
```

PK :

```text
gcr_id
```

Champs minimum :

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

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

FK facultative :

```text
parent_gcr_id
    -> am.g_celebration_rule.gcr_id
    ON DELETE CASCADE
```

FK vers lieu :

```text
gl_id
    -> am.g_location.gl_id
```

La stratégie exacte de suppression du lieu doit empêcher la destruction de la règle par accident.

Préférer :

```text
PROTECT
```

ou désactivation du lieu.

---

# 11. Célébration régulière principale et liée

Une règle principale possède :

```text
parent_gcr_id = NULL
```

Une règle liée possède :

```text
parent_gcr_id = gcr_id de la règle principale
```

Une règle liée appartient obligatoirement au même groupe que sa règle principale.

Le lien signifie :

> les célébrations générées à partir de ces règles appartiennent au même ensemble de préparation.

Il ne signifie pas qu'une célébration liée est moins importante.

---

# 12. Unicité des règles régulières

Dans un même groupe, deux règles régulières actives ne doivent pas utiliser simultanément :

```text
weekday + time + location
```

Créer la contrainte correspondante.

L'objectif est d'éviter deux règles générant systématiquement la même célébration.

---

# 13. Vie autonome après génération

Règle désormais figée :

> Une règle sert uniquement à créer une célébration.

Une fois la célébration créée :

> elle vit de manière totalement autonome.

Modifier une règle ne modifie jamais rétroactivement les célébrations déjà générées.

Supprimer ou désactiver une règle ne supprime jamais les célébrations déjà générées.

Cela vaut notamment pour :

* jour ;
* heure ;
* lieu ;
* relation principale/liée ;
* futurs paramètres ajoutés aux règles.

Cette règle est volontaire afin d'éviter :

* les recalculs complexes ;
* les modifications involontaires ;
* les effets de bord sur les membres.

---

# 14. Dates particulières

Créer dans `app_group` :

```text
am.g_special_date_rule
```

Alias :

```text
gsdr
```

PK :

```text
gsdr_id
```

Champs minimum :

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

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

---

# 15. Types de dates particulières

`rule_type` doit permettre au minimum :

```text
annual_fixed
one_off
nth_weekday
```

## `annual_fixed`

Exemple :

```text
25 décembre
```

Utilise :

```text
month
day
```

## `one_off`

Exemple :

```text
Pâques 2027
```

ou un événement paroissial exceptionnel.

Utilise :

```text
exact_date
```

## `nth_weekday`

Exemple :

```text
troisième dimanche de septembre
```

Utilise au minimum :

```text
month
weekday
occurrence
```

La validation métier doit empêcher les combinaisons incohérentes de colonnes.

---

# 16. Collision date particulière / règles régulières

La règle est désormais fixée.

Chaque date particulière choisit explicitement un mode :

```text
add
replace
```

## `add`

Les célébrations particulières sont ajoutées aux célébrations régulières calculées pour cette date.

## `replace`

Les célébrations particulières remplacent pour cette date les célébrations régulières qui auraient normalement été générées.

Aucune déduction implicite ne doit être faite à partir du nom de la fête ou de la date.

Exemple :

```text
Noël tombe un dimanche
```

Le comportement dépend uniquement du paramètre `collision_mode`.

---

# 17. Célébrations propres à une date particulière

Une date particulière doit pouvoir définir une ou plusieurs célébrations à générer.

Créer :

```text
am.g_special_date_celebration
```

Alias :

```text
gsdc
```

PK :

```text
gsdc_id
```

Champs minimum :

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

FK :

```text
gsdr_id
    -> am.g_special_date_rule.gsdr_id
    ON DELETE CASCADE
```

FK facultative :

```text
parent_gsdc_id
    -> am.g_special_date_celebration.gsdc_id
    ON DELETE CASCADE
```

`parent_gsdc_id` permet de reproduire le mécanisme :

```text
célébration principale
+
célébrations liées
```

pour une date particulière.

La relation parent/enfant doit rester dans la même règle spéciale.

---

# 18. Génération du planning

Seul un Responsable peut lancer une génération.

La génération peut être demandée :

```text
pour N semaines
```

ou :

```text
jusqu'à une date donnée
```

Le service de génération appartient à :

```text
app_planning
```

Il lit les paramètres de :

```text
app_group
```

et crée directement des objets :

```text
app_celebration.Celebration
```

Il ne crée aucune ligne intermédiaire de planning.

---

# 19. Génération incrémentale

La génération est :

```text
incrémentale
idempotente
non destructive
```

Relancer plusieurs fois la génération pour la même période ne crée pas de doublon.

La génération ne modifie jamais automatiquement une célébration existante.

---

# 20. Anti-doublon

La célébration possède un identifiant technique propre.

L'anti-doublon métier repose sur :

```text
groupe + date + heure + lieu
```

La génération doit toujours rechercher une célébration existante correspondant à cette clé avant d'en créer une nouvelle.

La contrainte d'unicité finale devra être portée par la modélisation de `app_celebration`.

Ne pas utiliser comme PK :

```text
date + heure + lieu
```

Les valeurs peuvent être modifiées après création.

---

# 21. Conservation de la règle d'origine

Il n'est pas nécessaire de conserver une FK obligatoire vers la règle ayant généré une célébration.

L'idempotence repose sur l'unicité métier de la célébration, pas sur la règle source.

Si une traçabilité d'origine est jugée utile lors de l'implémentation de `app_celebration`, elle doit être :

* facultative ;
* informative uniquement ;
* en `SET NULL` si la règle disparaît ;
* incapable de modifier automatiquement la célébration.

Ne pas construire de mécanisme de synchronisation règle → célébration.

---

# 22. Structure du planning

Le planning principal est une vue tabulaire :

```text
ligne    = célébration
colonne  = Membre ou Membre AM
cellule  = données de cette personne pour cette célébration
```

Aucune table `planning_line` n'existe.

L'identifiant de la ligne est :

```text
cc_id
```

de la célébration.

---

# 23. Données d'une cellule

Les données d'une cellule devront être stockées dans `app_celebration`.

Prévoir lors de la migration de `app_celebration` une table conceptuellement équivalente à :

```text
c_celebration_member
```

Alias attendu :

```text
ccm
```

PK :

```text
ccm_id
```

Elle devra contenir au minimum :

```text
ccm_id
cc_id
ggm_id
gps_id
created_at
updated_at
```

avec unicité :

```text
(cc_id, ggm_id)
```

Cette table est la source unique de la cellule affichée dans le planning.

Ne pas créer de copie dans `app_planning`.

---

# 24. Fonctions d'une cellule

Une personne peut sélectionner plusieurs fonctions pour une célébration.

Prévoir côté `app_celebration` une table conceptuellement équivalente à :

```text
c_celebration_member_function
```

Alias :

```text
ccmf
```

PK :

```text
ccmf_id
```

Elle référence :

```text
ccm_id
gf_id
```

Unicité :

```text
(ccm_id, gf_id)
```

La fonction doit obligatoirement faire partie des fonctions possibles de cette personne au moment où elle est choisie.

Après utilisation, la suppression d'une fonction du catalogue du groupe ne doit pas effacer silencieusement les anciennes données.

Utiliser la désactivation fonctionnelle des fonctions plutôt qu'une suppression destructrice lorsqu'elles sont déjà utilisées.

---

# 25. Création des cellules

Lorsqu'une célébration future est générée ou créée :

* créer une cellule pour chaque Membre actif ;
* créer une cellule pour chaque Membre AM actif ;
* utiliser l'état `default` du groupe ;
* sélectionner une fonction par défaut.

Fonction par défaut :

* si une seule fonction possible : celle-ci ;
* si plusieurs fonctions : la première selon l'ordre du groupe.

Une cellule possède toujours au moins une fonction sélectionnée.

---

# 26. Arrivée d'un nouveau membre

Règle fixée :

Lorsqu'un nouveau Membre ou Membre AM devient actif dans le groupe :

* rechercher toutes les célébrations futures ;
* uniquement celles dont le planning n'est pas validé ;
* créer sa cellule manquante ;
* lui attribuer l'état `default` ;
* lui attribuer sa fonction par défaut.

Ne rien créer rétroactivement :

* sur les célébrations passées ;
* sur les célébrations dont le planning est déjà validé.

Cette opération doit être idempotente.

---

# 27. Départ d'un membre — RGPD

La RGPD prime sur la conservation historique nominative.

Un départ définitif signifie :

> suppression définitive des données personnelles du membre dans le périmètre concerné.

Ne pas conserver :

* de snapshot de nom ;
* de snapshot de prénom ;
* de copie de l'identité ;
* de sauvegarde cachée permettant de reconstruire son historique nominatif.

Si la personne revient plus tard :

> elle revient comme une nouvelle situation fonctionnelle.

Aucun mécanisme de restauration de ses anciennes données nominatives ne doit être prévu.

---

# 28. Effet RGPD sur les cellules

Les futures relations :

```text
g_group_member
    -> c_celebration_member
```

doivent permettre la suppression définitive des données nominatives liées au membre.

Lorsque `g_group_member` est supprimé définitivement :

```text
c_celebration_member
```

et ses fonctions associées doivent être supprimées.

Utiliser :

```text
ON DELETE CASCADE
```

pour cette branche de données personnelles.

Il est accepté que le planning historique perde alors toute trace nominative de cette personne.

C'est une conséquence volontaire de la priorité donnée à la RGPD.

Ne pas remplacer automatiquement la personne par :

```text
Ancien membre
Utilisateur supprimé
Pierre D.
```

si cela permet encore une identification.

---

# 29. Modification d'une cellule

Tant que le planning de la célébration n'est pas validé :

un Membre peut modifier :

* sa propre cellule ;
* les cellules des Membres AM du groupe.

Il ne peut pas modifier la cellule d'un autre Membre avec compte.

Un Responsable peut modifier toutes les cellules de la célébration.

Les fonctions sélectionnées doivent rester dans les fonctions possibles de la personne.

---

# 30. Validation du planning

Il n'existe pas de table de validation du planning.

La validation du planning est un état de la célébration.

Prévoir côté `c_celebration` au minimum :

```text
planning_validated_at
planning_validated_by_ggm_id
```

Une valeur :

```text
planning_validated_at IS NOT NULL
```

signifie :

> la ligne est validée dans le planning.

Cette validation est totalement distincte de :

```text
validation de la célébration
```

qui concerne le déroulé et son propre workflow.

Ne jamais utiliser le même champ pour les deux validations.

---

# 31. Responsable ayant validé le planning

La FK :

```text
planning_validated_by_ggm_id
```

doit pouvoir devenir `NULL` si le Responsable disparaît pour raison RGPD.

Utiliser :

```text
ON DELETE SET NULL
```

La date de validation peut rester, mais aucune identité de l'ancien Responsable ne doit être conservée ailleurs pour contourner sa suppression.

---

# 32. Effet de la validation du planning

Lorsqu'un Responsable valide une ligne :

* les cellules de cette célébration deviennent non modifiables ;
* les fonctions sélectionnées deviennent non modifiables via le planning ;
* les personnes retenues sont celles définies par les données actuelles de la célébration ;
* aucune copie vers une deuxième « équipe réelle » n'est créée.

Il n'existe donc pas :

```text
planning figé
+
copie dans équipe réelle
```

Il n'existe qu'une seule donnée.

La validation change son état :

```text
modifiable -> verrouillée pour le planning
```

---

# 33. Dévalidation du planning

Seul un Responsable peut dévalider.

Une célébration passée ne peut pas être dévalidée côté planning.

Dévalider signifie :

```text
planning_validated_at = NULL
planning_validated_by_ggm_id = NULL
```

La dévalidation permet à nouveau de modifier :

* états ;
* personnes ;
* fonctions ;

selon les permissions normales.

Aucune copie n'a besoin d'être fusionnée ou réconciliée.

---

# 34. Revalidation

La revalidation ne nécessite aucun algorithme de fusion.

C'est une conséquence directe de la nouvelle architecture.

Workflow :

```text
planning validé
    ↓
dévalidation
    ↓
modification des données de la célébration
    ↓
revalidation
```

Le système valide simplement l'état courant.

Il n'existe aucune ancienne équipe à fusionner.

Il n'existe aucun mécanisme :

```text
union
écrasement
resynchronisation
```

---

# 35. Modification depuis la célébration

Les pages Planning et Célébration utilisent les mêmes données.

Tant que le planning n'est pas validé :

* une modification des membres depuis le planning apparaît dans la célébration ;
* une modification depuis la célébration apparaît immédiatement dans le planning.

Il n'y a rien à synchroniser.

Une requête ultérieure relit simplement la même donnée.

---

# 36. Planning validé et membres attachés

Une fois le planning validé :

> changer les personnes attachées ou leurs fonctions nécessite d'abord une dévalidation du planning.

Cette règle doit être appliquée quel que soit le point d'entrée :

* écran Planning ;
* écran Célébration ;
* API ;
* administration interne ;
* service métier.

Ne jamais permettre de contourner le verrou simplement en passant par une autre vue.

---

# 37. Validation de la célébration

La validation de la célébration est un workflow différent.

Elle concerne notamment :

* son déroulé ;
* ses chants ;
* ses textes ;
* sa préparation ;
* les règles définies par `SFD-04-celebrations`.

Ne pas confondre :

```text
planning_validated_at
```

avec la future validation métier de la célébration.

Un planning peut donc conceptuellement être validé alors que la préparation liturgique de la célébration ne l'est pas encore.

---

# 38. Membres autorisés à modifier la célébration

Un Membre peut disposer du droit de modifier le contenu d'une célébration conformément aux règles de `app_group` et `app_celebration`.

Cela ne lui donne jamais le droit :

* de valider le planning ;
* de dévalider le planning ;
* de valider la célébration.

Seul un Responsable peut valider/dévalider le planning.

Seul un Responsable peut valider/dévalider la célébration.

---

# 39. Calendrier

Le calendrier de `app_planning` est également une vue des célébrations.

Il ne possède aucune table calendrier propre.

Une célébration créée apparaît dans le calendrier.

Une célébration déplacée change de position dans le calendrier.

Une célébration supprimée disparaît du calendrier.

Aucune synchronisation n'est nécessaire.

---

# 40. Groupes jumelés et célébrations partagées

Une célébration partagée reste une seule célébration.

Ne jamais créer une copie de la célébration par groupe pour satisfaire le planning.

Les plannings des groupes concernés voient le même objet célébration selon les règles de visibilité définies dans les SFD.

La contrainte :

```text
groupe + date + heure + lieu
```

doit rester vraie pour chacun des groupes associés.

La gestion détaillée de la table d'association célébration ↔ groupe appartient à `app_celebration`.

---

# 41. Mise à jour nécessaire des SFD

Avant ou pendant l'implémentation, corriger la documentation actuelle afin d'éviter que du code ultérieur ne réintroduise l'ancien modèle.

Sont désormais obsolètes les règles indiquant :

* qu'une validation du planning copie les personnes dans une seconde équipe réelle ;
* qu'après validation l'équipe réelle peut diverger du planning figé ;
* qu'une coche doit resynchroniser une équipe différente ;
* qu'une dévalidation conserve une seconde équipe séparée ;
* qu'une revalidation doit fusionner deux ensembles.

Remplacer cette conception par :

> la célébration porte directement les participations affichées dans le planning.

> la validation du planning verrouille ces participations.

> la dévalidation les rend à nouveau modifiables.

Mettre à jour :

```text
docs/SFD-02-planning.md
docs/app_planning/functional_requirements.md
```

et vérifier la cohérence avec :

```text
docs/SFD-04-celebrations.md
```

La SFD Célébrations contient déjà le principe fondamental :

> la célébration est la source de vérité du planning.

---

# 42. Ce que `app_planning` doit contenir en code

Même sans modèle PostgreSQL propre, `app_planning` reste une application fonctionnelle importante.

Elle contiendra notamment :

```text
services/
    génération des célébrations
    calcul des règles de calendrier
    création des cellules manquantes
    validation/dévalidation du planning

views/
    tableau de planning
    calendrier

permissions/
    droits de modification des cellules
    droits Responsable

selectors/
    récupération optimisée des célébrations
    construction du tableau

tests/
    génération
    permissions
    validation
    affichage
```

Ne pas placer de logique métier importante directement dans les views.

---

# 43. Transactions

Les opérations suivantes doivent être transactionnelles :

* génération d'une période ;
* validation d'une ligne ;
* dévalidation ;
* création des cellules d'un nouveau membre.

Utiliser notamment :

```text
transaction.atomic()
```

et lorsque nécessaire :

```text
select_for_update()
```

pour éviter les générations ou validations concurrentes incohérentes.

---

# 44. Tests de génération

Tester au minimum :

* génération pour N semaines ;
* génération jusqu'à une date ;
* relance identique sans doublon ;
* génération incrémentale ;
* plusieurs célébrations le même jour ;
* même heure dans deux lieux différents ;
* règle principale + plusieurs liées ;
* date particulière `add` ;
* date particulière `replace` ;
* date particulière tombant un dimanche ;
* modification d'une règle après génération sans effet sur l'existant ;
* désactivation d'une règle sans suppression de célébration existante.

---

# 45. Tests des cellules

Tester au minimum :

* création automatique d'une cellule par membre ;
* création pour Membre AM ;
* état `default` utilisé initialement ;
* fonction unique utilisée automatiquement ;
* première fonction utilisée par défaut lorsqu'il y en a plusieurs ;
* plusieurs fonctions sélectionnables ;
* impossibilité de sélectionner une fonction non autorisée ;
* membre modifiant sa propre cellule ;
* membre modifiant un Membre AM ;
* membre incapable de modifier un autre compte ;
* Responsable capable de modifier toutes les cellules.

---

# 46. Tests d'arrivée d'un membre

Lorsqu'un membre rejoint le groupe :

vérifier que les cellules sont créées uniquement pour :

```text
célébrations futures
+
planning non validé
```

Ne pas créer de cellule :

* sur le passé ;
* sur les célébrations au planning déjà validé.

Relancer le service ne doit créer aucun doublon.

---

# 47. Tests de validation

Tester :

* seul Responsable peut valider ;
* seul Responsable peut dévalider ;
* validation verrouille toutes les cellules ;
* modification impossible via planning après validation ;
* modification impossible via célébration après validation pour les membres/fonctions attachés ;
* dévalidation rouvre les modifications ;
* revalidation fonctionne sans fusion ;
* célébration passée non dévalidable ;
* validation planning indépendante de validation célébration.

---

# 48. Tests RGPD

Tester explicitement :

* suppression définitive de `g_group_member` ;
* suppression en cascade de ses cellules de célébration ;
* suppression de ses fonctions par célébration ;
* disparition de son historique nominatif du planning ;
* `planning_validated_by_ggm_id` passant à NULL si nécessaire ;
* absence de snapshot caché du nom/prénom.

La suppression RGPD est prioritaire sur la conservation historique nominative.

---

# 49. Dépendances de migrations

La conception implique l'ordre logique suivant :

```text
app_member
    ↓
app_group
    ↓
app_celebration
```

`app_planning` ne nécessite pas nécessairement de migration initiale propre puisqu'il n'a pas de table `p_*`.

Les nouvelles tables de paramétrage planning sont des migrations de :

```text
app_group
```

Les cellules et la validation seront des migrations de :

```text
app_celebration
```

Ne créer une migration vide `app_planning` que si Django ou l'organisation du projet le nécessite réellement.

Ne pas créer artificiellement une table pour justifier l'existence d'une migration.

---

# 50. Résultat architectural attendu

La lecture finale doit être :

```text
groupe
│
├── paramètres
│   ├── états planning
│   ├── fonctions
│   ├── lieux
│   ├── règles régulières
│   └── dates particulières
│
└── célébrations
    │
    ├── date / heure / lieu
    ├── planning validé ?
    │
    └── personnes
        ├── état
        └── fonctions sélectionnées
```

Et :

```text
app_planning
```

ne fait que présenter et orchestrer ces données.

Il ne les recopie jamais.

---

# 51. Principe final

Préférer systématiquement :

```text
une source de vérité
```

à :

```text
deux représentations synchronisées
```

La règle fondamentale du module est :

> **Le planning est une vue des célébrations.**

> **Une ligne est une célébration.**

> **Une cellule est la relation entre cette célébration et une personne.**

> **La validation du planning verrouille cette relation mais ne crée aucune copie.**

> **Toute règle de génération ne sert qu'à créer ; après création, la célébration vit de manière autonome.**

> **La suppression RGPD d'une personne est définitive et prioritaire sur son historique nominatif.**
