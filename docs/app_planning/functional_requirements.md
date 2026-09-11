# app_planning — Functional Requirements

`app_planning` porte la vue planning, les règles de génération et le suivi des disponibilités autour des célébrations.

Sources fonctionnelles principales :

- `docs/SFD-02-planning.md`
- `docs/SFD-04-celebrations.md`
- `docs/SFD-01-groupes_et_membres.md`
- `docs/app_planning/models.md`
- `docs/app_group/models.md`
- `docs/app_celebration/models.md`

---

# Note de consolidation V1

Les paramètres durables du planning appartiennent à `app_group`.

Les cellules réelles et la validation du planning sont portées par `app_celebration`, car une ligne de planning est une célébration.

`app_planning` ne crée pas de tables `p_*` en V1. Il orchestre, génère et affiche les données des groupes et des célébrations.

---

# 1. Rôle fonctionnel

`app_planning` est responsable :

- du calendrier visible par un groupe ;
- des services de génération de célébrations futures ;
- de l’application des règles régulières et dates particulières définies par `app_group` ;
- de l’affichage des lignes de planning dérivées des célébrations ;
- de l’affichage et de la modification autorisée des cellules membre/célébration ;
- de la validation du planning ;
- des règles de permission propres au planning.

`app_planning` ne possède pas :

- la célébration comme objet métier central ;
- les règles régulières, dates particulières, lieux, fonctions et états de planning ;
- les cellules persistantes membre/célébration ;
- le déroulé liturgique ;
- les chants et textes ;
- les feuilles de messe ;
- les rôles de groupe ;
- les Membres AM.

---

# 2. Relation avec les célébrations

Le planning est dérivé des célébrations.

Une ligne de planning correspond à une célébration.

`app_planning` peut créer des célébrations lors d’une génération, mais ne doit pas créer une entité métier concurrente appelée `animation`.

Le terme `animation` peut rester utilisé pour :

- les fonctions d’animation ;
- certains libellés utilisateur ;
- l’idée d’une équipe qui anime une célébration.

Il ne doit pas devenir une table métier autonome distincte de la célébration.

---

# 3. Génération

Un Responsable peut générer le planning :

- pour un nombre de semaines ;
- ou jusqu’à une date donnée.

La génération utilise :

- les règles régulières principales de `app_group` ;
- les règles régulières liées de `app_group` ;
- les dates particulières du groupe, avec `collision_mode = add` ou `replace`.

La génération est incrémentale et idempotente.

Elle ne remplace pas les célébrations existantes et ne doit pas créer de doublons.

Modifier, supprimer ou désactiver une règle après génération n’a pas d’effet rétroactif sur les célébrations déjà créées.

L’identification fonctionnelle d’une occurrence générée repose sur :

> groupe + date réelle + heure + lieu.

---

# 4. Tableau de planning

Le planning principal est un tableau :

- une ligne = une célébration ;
- une colonne = un Membre ou Membre AM ;
- une cellule = un état de disponibilité et une ou plusieurs fonctions d’animation.

Le groupe configure dans `app_group` :

- les états de planning ;
- les couleurs des états ;
- les fonctions d’animation disponibles ;
- l’ordre des fonctions ;
- les fonctions possibles pour chaque personne.

L’état `selection` sélectionne les personnes retenues lors de la validation du planning.

L’état `default` est l’état des nouvelles cellules.

Les noms et couleurs sont configurables, mais ne changent pas le sens fonctionnel des états.

Les cellules persistantes appartiennent à `app_celebration`.

---

# 5. Validation du planning

La validation du planning est distincte de la validation de célébration.

Elle signifie :

- les cellules de la ligne deviennent non modifiables depuis le planning ;
- les personnes, états et fonctions sélectionnés constituent l’état courant validé de la célébration côté planning.

Après validation, il n’existe pas de seconde équipe séparée à synchroniser ou fusionner.

Une modification des personnes ou fonctions attachées à la célébration nécessite d’abord une dévalidation du planning.

La dévalidation rouvre les cellules de la célébration.

La revalidation valide l’état courant des mêmes cellules. Elle ne réalise ni fusion, ni resynchronisation avec une équipe séparée.

Une célébration passée ne peut plus être dévalidée côté planning.

---

# 6. Règles fonctionnelles

**PLANNING-CELEB-01** — Le planning est dérivé des célébrations.

**PLANNING-CELEB-02** — Une ligne de planning correspond à une célébration.

**PLANNING-CELEB-03** — `app_planning` ne crée pas d’entité métier concurrente à la célébration.

**PLANNING-GEN-01** — Seul un Responsable peut générer le planning.

**PLANNING-GEN-02** — La génération est incrémentale.

**PLANNING-GEN-03** — La génération est idempotente.

**PLANNING-GEN-04** — Une occurrence générée est identifiée par groupe + date réelle + heure + lieu.

**PLANNING-GEN-05** — Une date particulière utilise explicitement `collision_mode = add` ou `replace`.

**PLANNING-GEN-06** — Modifier ou supprimer une règle après génération ne modifie pas rétroactivement les célébrations déjà créées.

**PLANNING-TAB-01** — Une cellule associe une personne, une célébration, un état et une ou plusieurs fonctions.

**PLANNING-STATE-01** — Le groupe doit disposer d’au moins deux états.

**PLANNING-STATE-02** — L’état `selection` identifie les personnes retenues lors de la validation.

**PLANNING-STATE-03** — L’état `default` est l’état par défaut.

**PLANNING-FUNC-01** — Une personne possède au moins une fonction possible.

**PLANNING-FUNC-02** — Une cellule possède au moins une fonction sélectionnée.

**PLANNING-VAL-01** — La validation du planning verrouille les cellules, pas le déroulé de célébration.

**PLANNING-VAL-02** — La validation du planning verrouille l’état courant des personnes et fonctions de la célébration.

**PLANNING-VAL-03** — Il n’existe pas de deuxième équipe séparée des cellules de célébration.

**PLANNING-VAL-04** — La dévalidation rend les cellules à nouveau modifiables selon les permissions normales.

**PLANNING-VAL-05** — La revalidation valide l’état courant des cellules sans fusion avec une autre source.

**PLANNING-HIST-01** — Les états et fonctions figés constituent l’historique du planning.

---

# 7. Points encore à spécifier

1. UX détaillée du tableau et du calendrier ;
2. contrats Python exacts des services et selectors ;
3. comportement exact des permissions de modification cellule par cellule.
