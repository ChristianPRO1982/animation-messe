# app_planning — Functional Requirements

`app_planning` porte la vue planning, les règles de génération et le suivi des disponibilités autour des célébrations.

Sources fonctionnelles principales :

- `docs/SFD-02-planning.md`
- `docs/SFD-04-celebrations.md`
- `docs/SFD-01-groupes_et_membres.md`

---

# 1. Rôle fonctionnel

`app_planning` est responsable :

- du calendrier visible par un groupe ;
- des règles de génération de planning ;
- des célébrations régulières principales et liées ;
- des dates particulières ;
- des lignes de planning ;
- des cellules membre/célébration ;
- des états de disponibilité ;
- des fonctions d’animation ;
- de la validation du planning ;
- de la distinction entre planning figé et équipe réelle.

`app_planning` ne possède pas :

- la célébration comme objet métier central ;
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

- les célébrations régulières principales ;
- les célébrations régulières liées ;
- les dates particulières du groupe.

La génération est incrémentale et idempotente.

Elle ne remplace pas les célébrations existantes et ne doit pas créer de doublons.

L’identification fonctionnelle d’une occurrence générée repose sur :

> groupe + date réelle + heure + lieu.

---

# 4. Tableau de planning

Le planning principal est un tableau :

- une ligne = une célébration ;
- une colonne = un Membre ou Membre AM ;
- une cellule = un état de disponibilité et une ou plusieurs fonctions d’animation.

Le groupe configure :

- au moins deux états ;
- les couleurs des états ;
- les fonctions d’animation disponibles ;
- l’ordre des fonctions ;
- les fonctions possibles pour chaque personne.

L’état 1 est l’état de sélection reporté dans l’équipe réelle lors de la validation du planning.

L’état 2 est l’état par défaut des nouvelles cellules.

Les noms et couleurs sont configurables, mais ne changent pas le sens fonctionnel des états.

---

# 5. Validation du planning

La validation du planning est distincte de la validation de célébration.

Elle signifie :

- les cellules de la ligne deviennent non modifiables depuis le planning ;
- les personnes en état 1 sont ajoutées à l’équipe réelle de la célébration ;
- elles sont ajoutées avec les fonctions sélectionnées dans leur cellule.

Après validation :

- l’équipe réelle peut encore être modifiée depuis la célébration ;
- ces modifications ne rouvrent pas le planning ;
- la coche de participation reflète l’équipe réelle actuelle ;
- les états et fonctions figés restent historiques.

La dévalidation rouvre le planning, mais ne supprime pas automatiquement l’équipe réelle.

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

**PLANNING-TAB-01** — Une cellule associe une personne, une célébration, un état et une ou plusieurs fonctions.

**PLANNING-STATE-01** — Le groupe doit disposer d’au moins deux états.

**PLANNING-STATE-02** — L’état 1 sélectionne les personnes à reporter dans l’équipe réelle lors de la validation.

**PLANNING-STATE-03** — L’état 2 est l’état par défaut.

**PLANNING-FUNC-01** — Une personne possède au moins une fonction possible.

**PLANNING-FUNC-02** — Une cellule possède au moins une fonction sélectionnée.

**PLANNING-VAL-01** — La validation du planning verrouille les cellules, pas le déroulé de célébration.

**PLANNING-VAL-02** — La validation ajoute les personnes en état 1 à l’équipe réelle de la célébration.

**PLANNING-VAL-03** — L’équipe réelle peut diverger du planning figé.

**PLANNING-VAL-04** — La dévalidation ne supprime pas automatiquement l’équipe réelle.

**PLANNING-HIST-01** — Les états et fonctions figés constituent l’historique du planning.

---

# 7. Points encore à spécifier

1. collision entre dates particulières et célébrations dominicales régulières ;
2. effet de la modification ou suppression d’une règle après génération ;
3. règles exactes de fusion lors d’une revalidation du planning ;
4. affichage détaillé des divergences entre fonctions planifiées et fonctions réelles ;
5. interface entre `app_planning` et `app_celebration` pour la création de célébrations générées.
