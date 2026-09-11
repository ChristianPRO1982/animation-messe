# SFD-02-planning

## Partie Planning

> **Format pour la conception technique**
> Les règles stables de ce document sont identifiées avec le préfixe `PLAN-*`.
> Ces identifiants servent de points d’ancrage pour les modèles, permissions, workflows et tests techniques.

## 0. Objet du document

Ce document décrit les spécifications fonctionnelles détaillées de la partie **Planning** d’Animation Messe.

Il couvre :

- le calendrier du groupe ;
- le paramétrage des célébrations régulières ;
- les dates particulières ;
- la génération automatique du planning ;
- la structure du tableau de planning ;
- les états de disponibilité ;
- les fonctions d’animation ;
- la validation du planning ;
- les participations validées côté planning ;
- le lien entre célébrations principales et célébrations liées ;
- les règles d’historisation associées.

Ce document ne décrit pas en détail :

- la préparation liturgique complète ;
- le choix détaillé des chants ;
- les textes AELF ;
- la feuille de messe ;
- les notifications ;
- l’implémentation technique Django/PostgreSQL.

---

# 1. Terminologie

## 1.1 Célébration

Le terme métier canonique de l’application est **célébration**.

Une célébration représente une messe ou un événement que le groupe doit organiser ou animer.

Il peut notamment s’agir :

- d’une messe ;
- d’une messe anticipée du dimanche ;
- d’une veillée de louange ;
- d’une célébration particulière ;
- d’un autre événement paroissial.

Le produit reste principalement orienté vers l’organisation des messes, mais le modèle métier ne doit pas imposer qu’une animation soit nécessairement une messe.

Dans cette SFD, le mot **animation** peut encore apparaître comme terme d’usage lié au planning ou aux fonctions exercées.

Il ne désigne pas une entité métier distincte de la célébration.

La règle transversale est :

> **une ligne de planning correspond à une célébration.**

---

## 1.2 Rôle de groupe

Le rôle de groupe concerne les droits dans Animation Messe.

Exemples :

- Membre ;
- Responsable.

Le rôle de groupe ne doit pas être confondu avec la fonction tenue pendant une animation.

---

## 1.3 Fonction d’animation

Une **fonction d’animation** désigne la responsabilité assurée par une personne pendant une animation.

Exemples recommandés :

1. Chantre ;
2. Organiste ;
3. Maître de chœur ;
4. Responsable de groupe musical.

Animation Messe n’a pas vocation à gérer individuellement toutes les personnes présentes musicalement.

Ne sont notamment pas destinés à être modélisés comme fonctions de planning :

- soprano ;
- ténor ;
- guitariste ;
- trompettiste ;
- batteur ;
- bassiste ;
- autres instruments ou types de voix sans responsabilité globale dans l’animation liturgique.

L’objectif du planning est de gérer principalement les personnes qui prennent une responsabilité directe dans la conduite de l’animation.

---

# 2. Principe général du planning

Le planning d’un groupe est construit à partir :

1. d’un calendrier ;
2. des animations régulières définies dans les paramètres du groupe ;
3. des dates particulières définies par le groupe.

Le Responsable ne crée donc normalement pas manuellement chaque animation future.

Il demande au système de **générer un planning pour une période donnée**.

Le système calcule alors toutes les animations attendues et ajoute uniquement celles qui n’existent pas déjà.

---

# 3. Calendrier

## 3.1 Affichage par défaut

Le calendrier utilise par défaut la convention européenne :

- semaine commençant le lundi ;
- samedi et dimanche en fin de semaine.

---

## 3.2 Préférence personnelle d’affichage

Chaque membre peut disposer d’une préférence personnelle permettant d’afficher le calendrier avec une semaine commençant :

- le lundi ;
- ou le dimanche.

Cette préférence :

- est propre au membre ;
- ne modifie pas le planning ;
- ne modifie pas les dates ;
- ne modifie pas les paramètres du groupe ;
- n’a aucun effet métier.

---

# 4. Paramétrage des célébrations dominicales

## 4.1 Principe

Dans une paroisse, un même dimanche liturgique peut correspondre à plusieurs célébrations physiques.

Exemple :

- samedi soir ;
- dimanche matin ;
- dimanche soir.

Ces célébrations ont chacune :

- leur propre horaire ;
- leur propre lieu ;
- leur propre équipe ;
- leur propre ligne dans le planning.

Cependant, elles partagent très souvent une même préparation liturgique et une même feuille de messe.

Le système doit donc permettre de relier plusieurs célébrations entre elles.

---

# 5. Célébration principale

Pour un ensemble dominical habituel, le groupe configure d’abord une **animation principale**.

Cette animation principale est une célébration utilisée comme référence de préparation.

Elle possède au minimum :

- un jour ;
- une heure ;
- un lieu.

Exemple :

> Dimanche — 10 h 30 — Église Saint-Pierre

L’animation principale sert de référence pour la préparation commune.

Le terme « principale » ne signifie pas :

- qu’elle est liturgiquement plus importante ;
- qu’elle doit être la première chronologiquement ;
- qu’elle possède davantage de participants.

Elle constitue uniquement la **référence de préparation** pour les célébrations liées.

---

# 6. Célébrations liées

Le groupe peut ajouter à une animation principale autant d’animations liées que nécessaire.

Chaque animation liée est une célébration à part entière et possède également :

- un jour ;
- une heure ;
- un lieu.

Exemple :

### Animation principale

> Dimanche — 10 h 30 — Saint-Pierre

### Animations liées

> Samedi — 18 h 30 — Saint-Paul  
> Dimanche — 18 h 00 — Saint-Pierre

Chaque célébration liée reste une célébration à part entière.

Elle possède notamment :

- sa propre ligne de planning ;
- ses propres états par membre ;
- sa propre équipe ;
- ses propres informations d’organisation.

Le lien avec l’animation principale concerne principalement la préparation commune.

---

# 7. Unicité des célébrations régulières

Dans le paramétrage du groupe, deux célébrations régulières ne peuvent pas posséder simultanément le même triplet :

> **jour + heure + lieu**

Ce triplet constitue une information essentielle d’identification.

Exemple interdit :

- dimanche — 10 h 30 — Saint-Pierre ;
- dimanche — 10 h 30 — Saint-Pierre.

Exemples autorisés :

- dimanche — 10 h 30 — Saint-Pierre ;
- dimanche — 10 h 30 — Saint-Paul.

ou :

- dimanche — 10 h 30 — Saint-Pierre ;
- dimanche — 18 h 00 — Saint-Pierre.

Cette règle participe ensuite au mécanisme anti-doublon lors de la génération.

---

# 8. Héritage de la préparation entre célébrations

## 8.1 Principe

Toutes les célébrations restent indépendantes.

Cependant, une célébration liée suit **par défaut** la préparation de sa célébration principale.

Il ne s’agit pas d’une copie figée.

Il s’agit d’un héritage dynamique pouvant être remplacé localement.

---

## 8.2 Exemple sur le choix d’un chant

Pour une célébration principale, un sélecteur de chant peut proposer :

1. Non défini ;
2. Chant A ;
3. Chant B ;
4. Chant C ;
5. etc.

Pour une célébration liée, il propose par défaut :

1. Reprendre l’animation principale ;
2. Non défini ;
3. Chant A ;
4. Chant B ;
5. Chant C ;
6. etc.

Le libellé exact pourra être ajusté dans l’interface, mais il doit exprimer clairement la notion d’héritage.

---

## 8.3 Comportement de l’héritage

Si la célébration principale utilise :

> Chant A

et que la célébration liée reste sur :

> Reprendre l’animation principale

alors la célébration liée utilise également Chant A.

Si le chant de la célébration principale est ensuite remplacé par Chant B, la célébration liée suit automatiquement ce changement.

---

## 8.4 Dérogation locale

Une célébration liée peut s’écarter de la célébration principale pour un élément donné.

Exemple :

### Animation principale

> Chant d’entrée : Chant A

### Animation liée

> Chant d’entrée : Chant B

Seul ce choix devient propre à la célébration liée.

Les autres éléments qui restent configurés sur « Reprendre l’animation principale » continuent de suivre la préparation principale.

---

## 8.5 Principe fonctionnel

Le modèle recherché est donc :

> chaque animation est indépendante, mais une animation liée hérite par défaut des éléments de préparation de l’animation principale.

La définition exhaustive des champs concernés par cet héritage relève du SFD consacré à la préparation des animations.

---

# 9. Dates particulières

Le groupe peut ajouter au calendrier des règles correspondant à des dates particulières.

Ces règles peuvent être récurrentes ou ciblées.

---

## 9.1 Date annuelle fixe

Exemple :

> 25 décembre — Noël

La règle se reproduit chaque année.

---

## 9.2 Date ponctuelle

Exemple :

> Pâques 2027

ou :

> événement particulier à une date donnée

La date ne concerne qu’une occurrence précise.

---

## 9.3 Date récurrente calculée

Exemple :

> troisième dimanche de septembre — rentrée paroissiale

La date est recalculée chaque année.

---

# 10. Génération du planning

## 10.1 Droits

Seul un Responsable du groupe peut générer le planning.

---

## 10.2 Période de génération

Le Responsable peut demander une génération :

- pour un nombre de semaines ;
- ou jusqu’à une date donnée.

---

## 10.3 Calcul des célébrations

Le système calcule toutes les célébrations comprises dans la période demandée à partir :

- des célébrations dominicales principales ;
- des célébrations dominicales liées ;
- des dates particulières configurées.

---

# 11. Génération incrémentale

La génération ne remplace jamais le planning existant.

Elle le complète.

Exemple :

Le planning est déjà généré jusqu’au :

> 31 juillet 2027

Le Responsable demande ensuite :

> Générer jusqu’au 31 août 2027

Le système conserve toutes les animations existantes et ajoute uniquement celles qui manquent.

La génération doit donc être **idempotente** :

> relancer plusieurs fois une génération couvrant la même période ne doit pas créer de doublons.

---

# 12. Identification des occurrences générées

Une date seule ne suffit pas à identifier une animation car plusieurs animations peuvent avoir lieu le même jour.

Pour une occurrence générée, l’identification repose notamment sur :

> **date réelle + heure + lieu**

dans le contexte du groupe.

Le lien avec la règle d’origine peut également être conservé, mais la logique fonctionnelle de non-doublon doit empêcher la création répétée d’une même occurrence.

Exemple :

Le dimanche 12 septembre :

- 10 h 30 — Saint-Pierre ;
- 18 h 00 — Saint-Pierre.

Il s’agit de deux animations différentes.

---

# 13. Structure du tableau de planning

Le planning principal prend la forme d’un tableau à deux dimensions.

---

## 13.1 Lignes

Chaque ligne représente une **animation**.

Les lignes sont ordonnées chronologiquement.

Plusieurs lignes peuvent correspondre au même dimanche liturgique.

Exemple :

| Animation |
|---|
| Samedi 11 septembre — 18 h 30 — Saint-Paul |
| Dimanche 12 septembre — 10 h 30 — Saint-Pierre |
| Dimanche 12 septembre — 18 h 00 — Saint-Pierre |

Les animations liées peuvent être regroupées visuellement afin de montrer qu’elles appartiennent au même ensemble dominical.

---

## 13.2 Colonnes

Chaque colonne représente une personne du groupe :

- membre avec compte CARThographie ;
- Membre AM.

Chaque cellule représente les informations de cette personne pour l’animation de la ligne.

---

# 14. Contenu d’une cellule

Une cellule contient au minimum deux informations distinctes :

1. un **état de planning** ;
2. une ou plusieurs **fonctions d’animation**.

Après validation, la cellule reste la donnée courante verrouillée côté planning. Il n’existe pas de seconde équipe séparée à synchroniser.

---

# 15. Paramétrage des états du planning

Les états sont configurables par groupe.

Le groupe doit disposer d’au moins deux états.

Deux états ont une signification métier obligatoire.

---

## 15.1 État 1 — état de sélection

L’état 1 est obligatoire.

Son nom est libre.

Exemple courant :

> Disponible

Cet état signifie fonctionnellement :

> lors de la validation du planning, cette personne est retenue dans l’état courant de la célébration côté planning.

Le comportement ne doit jamais dépendre du texte « Disponible ».

Le groupe peut appeler cet état autrement.

---

## 15.2 État 2 — état par défaut

L’état 2 est obligatoire.

Son nom est libre.

Exemple courant :

> Indisponible

Il constitue l’état attribué par défaut à toutes les nouvelles cellules créées lors de la génération du planning.

---

## 15.3 États supplémentaires

Le groupe peut créer autant d’états supplémentaires qu’il le souhaite.

Exemples :

- Peut-être ;
- En soutien ;
- Si besoin ;
- À confirmer ;
- Préfère éviter.

Ces états :

- possèdent un nom libre ;
- possèdent une couleur ;
- n’ont aucune règle métier automatique.

---

# 16. Couleurs des états

Chaque état possède une couleur configurable par le groupe.

La couleur sert uniquement à la lisibilité du tableau.

Elle ne porte aucune règle métier.

Modifier :

- le nom ;
- la couleur ;

d’un état ne doit pas modifier sa signification fonctionnelle.

---

# 17. Paramétrage des fonctions d’animation

## 17.1 Principe

Les fonctions d’animation sont configurées par groupe.

Le groupe doit disposer d’au moins une fonction.

---

## 17.2 Fonctions recommandées

Animation Messe peut recommander initialement :

1. Chantre ;
2. Organiste ;
3. Maître de chœur ;
4. Responsable de groupe musical.

Cette liste n’est pas imposée.

Chaque groupe peut :

- conserver ces fonctions ;
- les renommer ;
- en ajouter ;
- en retirer dans le respect des règles d’historique ;
- les ordonner.

---

## 17.3 Ordre des fonctions

Les fonctions possèdent un ordre dans le groupe.

Cet ordre sert notamment à déterminer la fonction sélectionnée par défaut lorsqu’une personne dispose de plusieurs fonctions possibles.

---

# 18. Fonctions possibles d’un membre

Chaque membre ou Membre AM possède une ou plusieurs fonctions qu’il peut assurer.

Exemple :

### Alice

- Chantre

### Paul

- Organiste

### Marie

- Chantre
- Maître de chœur

Ces fonctions représentent les capacités habituelles de la personne.

Elles ne signifient pas qu’elle exercera toutes ces fonctions à chaque animation.

---

# 19. Fonction sélectionnée dans le planning

La ou les fonctions sélectionnées dans une cellule indiquent :

> sous quelle fonction la personne se propose pour cette animation précise.

Cette sélection est propre à chaque animation.

---

## 19.1 Personne possédant une seule fonction

Si une personne ne possède qu’une seule fonction possible :

- cette fonction est automatiquement utilisée ;
- aucun contrôle de sélection n’est nécessaire dans l’interface.

Exemple :

Paul possède uniquement :

> Organiste

Toutes ses cellules utilisent donc automatiquement cette fonction.

---

## 19.2 Personne possédant plusieurs fonctions

Si une personne possède plusieurs fonctions possibles, elle peut sélectionner :

- une fonction ;
- ou plusieurs fonctions simultanément.

Exemple :

Marie possède :

- Chantre ;
- Maître de chœur.

Pour une animation donnée, elle peut choisir :

- Chantre ;
- Maître de chœur ;
- Chantre + Maître de chœur.

---

## 19.3 Valeur par défaut

Lors de la création d’une nouvelle cellule :

- si la personne possède une seule fonction, cette fonction est sélectionnée ;
- si elle en possède plusieurs, la première selon l’ordre des fonctions du groupe parmi celles qui lui sont attribuées est sélectionnée.

Au moins une fonction doit toujours rester sélectionnée.

---

## 19.4 Sélection multiple

Une personne peut venir à plusieurs titres pour une même animation.

Exemple :

Marie dirige une chorale d’enfants et assure également l’animation générale.

Elle peut donc être :

> Chantre + Maître de chœur

sur la même animation.

---

## 19.5 Fonction différente selon les célébrations

Les fonctions sélectionnées peuvent varier d’une animation à l’autre.

Exemple :

### Animation A

Marie :

> Disponible  
> Chantre + Maître de chœur

### Animation B

Marie :

> Disponible  
> Maître de chœur

Dans l’Animation B, il faudra donc éventuellement un autre Chantre.

Ce comportement doit être considéré comme normal et non comme un cas exceptionnel.

---

# 20. Indépendance entre état et fonction

L’état du planning et la fonction sélectionnée sont deux informations indépendantes.

Une cellule peut par exemple contenir :

> Indisponible  
> Chantre

La fonction reste simplement la fonction proposée par défaut si l’état venait ensuite à changer.

La fonction n’a aucune conséquence sur la validation tant que la personne n’est pas dans l’état 1.

---

# 21. Modification du planning par les membres

Tant qu’une ligne n’est pas validée, un membre peut modifier :

- l’état de sa propre cellule ;
- sa ou ses fonctions sélectionnées ;
- les cellules des Membres AM.

Un membre ne peut pas modifier les cellules d’un autre membre disposant de son propre compte.

---

# 22. Modification du planning par les Responsables

Tant qu’une ligne n’est pas validée, un Responsable peut modifier toutes les cellules de la ligne.

Il peut donc modifier pour n’importe quel membre ou Membre AM :

- l’état ;
- la ou les fonctions sélectionnées.

Pour les fonctions, la sélection reste limitée aux fonctions possibles attribuées à cette personne.

---

# 23. Validation du planning

## 23.1 Droits

Seul un Responsable peut valider une ligne du planning.

---

## 23.2 Nature de la validation

La validation concerne **le planning**, et non l’animation elle-même.

Elle signifie fonctionnellement :

> les réponses du tableau sont désormais figées dans les cellules de la célébration.

La validation ne verrouille pas le déroulé liturgique de la célébration.

---

# 24. Effet de la validation

Lorsqu’un Responsable valide une ligne :

1. les cellules de la ligne deviennent non modifiables depuis le planning ;
2. les personnes actuellement dans l’état 1 sont retenues dans l’état courant validé de la célébration côté planning ;
3. les fonctions sélectionnées dans leur cellule sont conservées comme fonctions validées côté planning ;
4. aucune copie n’est réalisée vers une seconde équipe séparée.

Si plusieurs personnes sont dans l’état 1, elles sont toutes ajoutées.

Il n’existe pas de limite implicite au nombre de personnes ajoutées.

---

# 25. Exemple de validation

Avant validation :

| Personne | État | Fonctions |
|---|---|---|
| Marie | Disponible | Chantre + Maître de chœur |
| Paul | Disponible | Organiste |
| Alice | Indisponible | Chantre |

Après validation :

### Données de célébration validées côté planning

- Marie — Chantre + Maître de chœur ;
- Paul — Organiste.

Alice reste présente dans sa cellule, mais n’est pas retenue par l’état de sélection.

---

# 26. Indicateur de participation dans le planning

Après validation, le planning peut afficher un indicateur à côté d’une personne.

Cet indicateur signifie uniquement :

> cette personne est retenue dans les cellules validées de la célébration côté planning.

L’indicateur ne signifie pas :

- qu’il existe une seconde équipe synchronisée ;
- que la validation du déroulé de célébration est faite.

---

# 27. Modification après validation planning

Une fois le planning validé, les cellules de la ligne ne sont plus modifiables depuis le planning.

Pour modifier les personnes, états ou fonctions de cette ligne, le Responsable doit :

1. dévalider la ligne ;
2. modifier les cellules ;
3. valider à nouveau si nécessaire.

La validation du planning ne bloque pas la préparation liturgique de la célébration.

---

# 28. Absence de synchronisation parallèle

Le planning et la célébration lisent les mêmes cellules de participation.

Il n’existe donc pas de synchronisation entre :

- des cellules de planning validées ;
- et une équipe séparée.

Exemple après validation :

| Personne | État planning | Retenue côté planning |
|---|---|---|
| Alice | Disponible | Oui |
| Paul | Indisponible | Non |
| Marie | Disponible | Oui |

Ces informations restent verrouillées jusqu’à dévalidation.

---

# 29. Absence d’écart entre planning validé et équipe séparée

En V1, le système ne maintient pas deux sources concurrentes pour les participations.

Exemple :

### Planning validé

> Marie — Disponible — Chantre + Maître de chœur

Cette donnée est la participation courante côté planning pour la célébration.

Toute correction fonctionnelle passe par une dévalidation, une modification des mêmes cellules, puis une revalidation.

---

# 30. Absence de synchronisation permanente état 1 vers une autre source

Après validation, l’état 1 ne pilote aucune équipe séparée.

Le planning ne doit pas continuellement imposer :

> état 1 = copie vers une table d’équipe distincte

L’état 1 est utilisé au moment de la validation pour identifier les cellules retenues.

Ensuite, les mêmes cellules restent la référence côté planning jusqu’à dévalidation ou archivage historique.

---

# 31. Dévalidation

## 31.1 Droits

Seul un Responsable peut dévalider une ligne.

---

## 31.2 Effet

La dévalidation :

- rouvre la ligne du planning ;
- efface les champs de validation planning ;
- permet à nouveau les modifications normales des états et fonctions.

Elle ne supprime pas une équipe séparée, puisqu’aucune équipe séparée n’est créée en V1.

---

## 31.3 Nouvelle validation

Après modification du planning, le Responsable peut valider à nouveau la ligne.

La nouvelle validation valide l’état courant des mêmes cellules.

Il n’y a pas de fusion ni de resynchronisation avec une autre source.

---

# 32. Célébrations passées

Une célébration passée ne peut plus être dévalidée côté planning.

Le planning devient alors une donnée historique.

Les états du planning permettent de conserver ce qui avait été déclaré et figé.

Les cellules validées restent l’historique consultable, sous réserve des règles RGPD.

---

# 33. Historique des fonctions

## 33.1 Modification des fonctions possibles d’un membre

Modifier ultérieurement les fonctions possibles d’un membre ne doit jamais réécrire l’historique.

Exemple :

Marie possédait :

- Chantre ;
- Maître de chœur.

Elle a participé à plusieurs animations comme Chantre.

Le Responsable retire ensuite « Chantre » de ses fonctions possibles.

Ses anciennes participations restent enregistrées comme Chantre.

Pour les nouvelles animations, cette fonction ne lui est simplement plus proposée.

---

## 33.2 Suppression d’une fonction du groupe

Une fonction ayant déjà été utilisée ne doit pas disparaître de l’historique.

Une suppression fonctionnelle doit donc être comprise comme :

> ne plus proposer cette fonction pour de nouvelles utilisations

et non comme :

> supprimer toute trace historique de cette fonction.

---

# 34. Workflow nominal complet

## Étape 1 — Paramétrage du groupe

Le Responsable configure :

- les lieux ;
- les animations dominicales principales ;
- les animations liées ;
- les dates particulières ;
- les états du planning ;
- les fonctions d’animation ;
- les fonctions possibles de chaque membre et Membre AM.

---

## Étape 2 — Génération

Le Responsable demande par exemple :

> Générer le planning jusqu’au 31 décembre.

Le système calcule toutes les animations attendues et ajoute celles qui manquent.

---

## Étape 3 — Remplissage par les membres

Chaque membre renseigne pour chaque animation non validée :

- son état ;
- éventuellement ses fonctions s’il en possède plusieurs.

Les membres peuvent également renseigner les Membres AM.

---

## Étape 4 — Arbitrage

Le Responsable consulte le planning.

Il peut modifier :

- tous les états ;
- toutes les fonctions sélectionnées ;

sur les lignes non validées.

---

## Étape 5 — Validation

Le Responsable valide une ligne.

Le système :

- fige le planning ;
- retient les personnes en état 1 dans les cellules validées ;
- conserve leurs fonctions sélectionnées.

---

## Étape 6 — Organisation validée côté planning

Après validation, le Responsable ne modifie plus les cellules validées sans dévalidation.

Le planning reste figé.

Les indicateurs de participation reflètent les cellules validées.

---

## Étape 7 — Correction éventuelle du planning

Tant que l’animation n’est pas passée, le Responsable peut :

- dévalider ;
- modifier le planning ;
- valider à nouveau.

Les mêmes cellules sont rouvertes lors de la dévalidation.

---

## Étape 8 — Historique

Une fois l’animation passée :

- elle ne peut plus être dévalidée ;
- les états du planning restent consultables ;
- les fonctions planifiées restent consultables ;
- les cellules validées restent identifiables.

---

# 35. Règles métier synthétiques

## Calendrier

**PLAN-CAL-01** — Le calendrier commence par défaut le lundi.

**PLAN-CAL-02** — Le premier jour de semaine peut être une préférence personnelle d’affichage.

**PLAN-CAL-03** — Cette préférence n’a aucun effet métier.

---

## Célébrations

**PLAN-CELEB-01** — Le terme métier canonique est « célébration ».

**PLAN-CELEB-02** — Le terme « animation » ne désigne pas une entité métier distincte de la célébration.

**PLAN-CELEB-03** — Une célébration peut représenter une messe ou un autre événement paroissial.

**PLAN-CELEB-04** — Chaque ligne de planning correspond à une célébration.

**PLAN-CELEB-05** — Chaque célébration possède sa propre organisation humaine.

---

## Ensembles dominicaux

**PLAN-DOM-01** — Un ensemble dominical peut contenir une célébration principale et plusieurs célébrations liées.

**PLAN-DOM-02** — La célébration principale sert de référence de préparation.

**PLAN-DOM-03** — Les célébrations liées possèdent leur propre ligne de planning et leur propre équipe.

**PLAN-DOM-04** — Les célébrations liées héritent par défaut des éléments de préparation de la célébration principale.

**PLAN-DOM-05** — Une célébration liée peut surcharger localement un élément hérité.

**PLAN-DOM-06** — Le triplet jour + heure + lieu doit être unique dans la configuration des célébrations régulières du groupe.

---

## Génération

**PLAN-GEN-01** — Seul un Responsable peut générer le planning.

**PLAN-GEN-02** — La génération peut être demandée pour un nombre de semaines ou jusqu’à une date.

**PLAN-GEN-03** — La génération utilise les règles régulières et les dates particulières du groupe.

**PLAN-GEN-04** — La génération complète le planning existant sans le remplacer.

**PLAN-GEN-05** — Une génération répétée ne doit pas créer de doublons.

**PLAN-GEN-06** — Plusieurs célébrations peuvent exister le même jour.

**PLAN-GEN-07** — Date + heure + lieu constituent une information essentielle d’identification d’une occurrence générée.

---

## Tableau

**PLAN-TAB-01** — Une ligne correspond à une célébration.

**PLAN-TAB-02** — Une colonne correspond à un membre ou Membre AM.

**PLAN-TAB-03** — Une cellule contient un état et une ou plusieurs fonctions d’animation.

---

## États

**PLAN-ETAT-01** — Le groupe doit disposer d’au moins deux états.

**PLAN-ETAT-02** — L’état 1 est obligatoire et possède la fonction métier de sélection lors de la validation.

**PLAN-ETAT-03** — L’état 2 est obligatoire et constitue l’état attribué par défaut aux nouvelles cellules.

**PLAN-ETAT-04** — Les noms des états 1 et 2 sont libres.

**PLAN-ETAT-05** — Les états supplémentaires n’ont aucune règle métier automatique.

**PLAN-ETAT-06** — Chaque état possède une couleur configurable.

**PLAN-ETAT-07** — Le nom ou la couleur d’un état ne modifie jamais sa signification fonctionnelle.

---

## Fonctions

**PLAN-FCT-01** — Le groupe doit posséder au moins une fonction d’animation.

**PLAN-FCT-02** — Les fonctions d’animation sont configurables et ordonnées par groupe.

**PLAN-FCT-03** — Chantre, Organiste, Maître de chœur et Responsable de groupe musical sont des valeurs recommandées et non imposées.

**PLAN-FCT-04** — Un membre ou Membre AM possède au moins une fonction possible.

**PLAN-FCT-05** — Une personne peut posséder plusieurs fonctions possibles.

**PLAN-FCT-06** — Une cellule possède au moins une fonction sélectionnée.

**PLAN-FCT-07** — Avec une seule fonction possible, celle-ci est automatiquement utilisée.

**PLAN-FCT-08** — Avec plusieurs fonctions possibles, la première selon l’ordre du groupe est sélectionnée par défaut.

**PLAN-FCT-09** — Plusieurs fonctions peuvent être sélectionnées simultanément.

**PLAN-FCT-10** — La sélection des fonctions est propre à chaque célébration.

**PLAN-FCT-11** — Une personne ne peut sélectionner que parmi ses fonctions possibles.

**PLAN-FCT-12** — L’état et les fonctions sélectionnées sont indépendants.

**PLAN-FCT-13** — Une personne peut exercer plusieurs fonctions dans une même célébration.

---

## Modification

**PLAN-MOD-01** — Un membre peut modifier sa propre cellule tant que la ligne n’est pas validée.

**PLAN-MOD-02** — Un membre peut modifier les cellules des Membres AM tant que la ligne n’est pas validée.

**PLAN-MOD-03** — Un membre ne peut pas modifier la cellule d’un autre membre avec compte.

**PLAN-MOD-04** — Un Responsable peut modifier toutes les cellules d’une ligne non validée.

---

## Validation

**PLAN-VAL-01** — Seul un Responsable peut valider une ligne.

**PLAN-VAL-02** — La validation du planning verrouille les cellules de planning, pas le déroulé de la célébration.

**PLAN-VAL-03** — Lors de la validation du planning, toutes les personnes en état 1 sont retenues dans les cellules validées de la célébration.

**PLAN-VAL-04** — Les fonctions attribuées lors de la validation sont celles sélectionnées dans la cellule.

**PLAN-VAL-05** — Une personne peut être ajoutée avec plusieurs fonctions.

**PLAN-VAL-06** — Les cellules de participation ne peuvent pas être modifiées après validation du planning sans dévalidation préalable.

**PLAN-VAL-07** — Un indicateur peut montrer qu’une personne est retenue dans les cellules validées.

**PLAN-VAL-08** — L’indicateur ne représente pas une seconde équipe synchronisée.

**PLAN-VAL-09** — Les fonctions retenues sont celles sélectionnées dans les cellules au moment de la validation.

**PLAN-VAL-10** — Il n’existe pas de modification parallèle d’une équipe qui réécrirait les cellules figées.

**PLAN-VAL-11** — Après validation, l’état 1 ne pilote pas une source séparée.

**PLAN-VAL-12** — Seul un Responsable peut dévalider une ligne future.

**PLAN-VAL-13** — La dévalidation rouvre les mêmes cellules et efface les champs de validation planning.

**PLAN-VAL-14** — Une nouvelle validation valide l’état courant des cellules sans fusion avec une autre source.

**PLAN-VAL-15** — Une célébration passée ne peut plus être dévalidée côté planning.

**PLAN-VAL-16** — La validation du planning est distincte de la validation de célébration définie dans `SFD-04-celebrations`.

---

## Historique

**PLAN-HIST-01** — Les états figés du planning sont conservés comme historique.

**PLAN-HIST-02** — Les fonctions planifiées sont conservées comme historique.

**PLAN-HIST-03** — Les cellules validées de la célébration constituent l’historique du planning.

**PLAN-HIST-04** — Modifier les fonctions possibles d’un membre ne réécrit pas l’historique.

**PLAN-HIST-05** — Une fonction retirée du paramétrage reste identifiable dans les données historiques qui l’utilisent.

---

# 36. Points restant à spécifier

Les points suivants ont été identifiés mais ne sont pas encore totalement tranchés.

## 36.1 Collision entre date particulière et célébrations dominicales

Exemple :

> Noël tombe un dimanche.

Une date particulière définit explicitement son mode de collision :

- `add` : elle ajoute de nouvelles célébrations ;
- `replace` : elle remplace les célébrations régulières du groupe sur la date concernée.

Aucune règle implicite ne doit considérer que deux célébrations à la même date constituent forcément un doublon.

---

## 36.2 Suppression ou modification d’une règle ayant déjà généré des célébrations

Lorsqu’un Responsable modifie, supprime ou désactive une règle de calendrier après génération, les célébrations déjà créées ne sont pas modifiées rétroactivement.

---

## 36.3 Comportement précis d’une revalidation

La revalidation valide l’état courant des mêmes cellules.

Elle ne réalise ni fusion, ni resynchronisation avec une équipe séparée.

---

## 36.4 Affichage détaillé des fonctions dans le planning

L’indicateur de participation signale les cellules retenues.

Il reste à déterminer si le planning doit également afficher directement :

- les fonctions sélectionnées dans les cellules ;
- un indicateur de modification après dévalidation/revalidation ;
- ou uniquement ces informations dans le détail de la célébration.

---

# 37. Principe directeur

Le planning doit conserver une séparation claire entre trois niveaux :

### 1. Les capacités habituelles de la personne

> Ce que cette personne sait habituellement faire.

Exemple :

> Chantre + Maître de chœur

### 2. Sa proposition dans le planning

> Ce qu’elle propose de faire pour cette célébration.

Exemple :

> Disponible — Maître de chœur

### 3. Sa participation validée côté planning

> Ce qui est retenu dans les cellules validées de la célébration.

Exemple :

> Chantre + Maître de chœur

Cette séparation permet de conserver un planning souple, compréhensible et historiquement fidèle sans créer une seconde représentation concurrente de la participation.

Le planning n’est donc jamais la source autonome d’une célébration.

Il est une vue et un outil de préparation construit à partir des célébrations et de leurs cellules de participation.
