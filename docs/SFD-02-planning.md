# SFD-02-planning

## Partie Planning

## 0. Objet du document

Ce document décrit les spécifications fonctionnelles détaillées de la partie **Planning** d’Animation Messe.

Il couvre :

- le calendrier du groupe ;
- le paramétrage des animations régulières ;
- les dates particulières ;
- la génération automatique du planning ;
- la structure du tableau de planning ;
- les états de disponibilité ;
- les fonctions d’animation ;
- la validation du planning ;
- la création de l’équipe réelle d’une animation ;
- le lien entre animations principales et animations liées ;
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

## 1.1 Animation

Le terme métier générique utilisé dans Animation Messe est **animation**.

Une animation représente une célébration ou un événement que le groupe doit organiser ou animer.

Il peut notamment s’agir :

- d’une messe ;
- d’une messe anticipée du dimanche ;
- d’une veillée de louange ;
- d’une célébration particulière ;
- d’un autre événement paroissial.

Le produit reste principalement orienté vers l’organisation des messes, mais le modèle métier ne doit pas imposer qu’une animation soit nécessairement une messe.

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

# 4. Paramétrage des animations dominicales

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

Le système doit donc permettre de relier plusieurs animations entre elles.

---

# 5. Animation principale

Pour un ensemble dominical habituel, le groupe configure d’abord une **animation principale**.

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

Elle constitue uniquement la **référence de préparation** pour les animations liées.

---

# 6. Animations liées

Le groupe peut ajouter à une animation principale autant d’animations liées que nécessaire.

Chaque animation liée possède également :

- un jour ;
- une heure ;
- un lieu.

Exemple :

### Animation principale

> Dimanche — 10 h 30 — Saint-Pierre

### Animations liées

> Samedi — 18 h 30 — Saint-Paul  
> Dimanche — 18 h 00 — Saint-Pierre

Chaque animation liée reste une animation à part entière.

Elle possède notamment :

- sa propre ligne de planning ;
- ses propres états par membre ;
- sa propre équipe ;
- ses propres informations d’organisation.

Le lien avec l’animation principale concerne principalement la préparation commune.

---

# 7. Unicité des animations régulières

Dans le paramétrage du groupe, deux animations régulières ne peuvent pas posséder simultanément le même triplet :

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

# 8. Héritage de la préparation entre animations

## 8.1 Principe

Toutes les animations restent indépendantes.

Cependant, une animation liée suit **par défaut** la préparation de son animation principale.

Il ne s’agit pas d’une copie figée.

Il s’agit d’un héritage dynamique pouvant être remplacé localement.

---

## 8.2 Exemple sur le choix d’un chant

Pour une animation principale, un sélecteur de chant peut proposer :

1. Non défini ;
2. Chant A ;
3. Chant B ;
4. Chant C ;
5. etc.

Pour une animation liée, il propose par défaut :

1. Reprendre l’animation principale ;
2. Non défini ;
3. Chant A ;
4. Chant B ;
5. Chant C ;
6. etc.

Le libellé exact pourra être ajusté dans l’interface, mais il doit exprimer clairement la notion d’héritage.

---

## 8.3 Comportement de l’héritage

Si l’animation principale utilise :

> Chant A

et que l’animation liée reste sur :

> Reprendre l’animation principale

alors l’animation liée utilise également Chant A.

Si le chant de l’animation principale est ensuite remplacé par Chant B, l’animation liée suit automatiquement ce changement.

---

## 8.4 Dérogation locale

Une animation liée peut s’écarter de l’animation principale pour un élément donné.

Exemple :

### Animation principale

> Chant d’entrée : Chant A

### Animation liée

> Chant d’entrée : Chant B

Seul ce choix devient propre à l’animation liée.

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

## 10.3 Calcul des animations

Le système calcule toutes les animations comprises dans la période demandée à partir :

- des animations dominicales principales ;
- des animations dominicales liées ;
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

Après validation, elle peut également afficher un indicateur montrant si la personne appartient actuellement à l’équipe réelle de l’animation.

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

> lors de la validation du planning, cette personne doit être ajoutée à l’équipe de l’animation.

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

## 19.5 Fonction différente selon les animations

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

> les réponses du tableau sont désormais figées et les personnes sélectionnées sont reportées dans l’équipe de l’animation.

La validation ne rend donc pas l’équipe de l’animation immuable.

---

# 24. Effet de la validation

Lorsqu’un Responsable valide une ligne :

1. les cellules de la ligne deviennent non modifiables depuis le planning ;
2. toutes les personnes actuellement dans l’état 1 sont ajoutées à l’équipe de l’animation ;
3. elles sont ajoutées avec toutes les fonctions sélectionnées dans leur cellule ;
4. le planning affiche quelles personnes appartiennent actuellement à l’équipe de l’animation.

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

### Équipe de l’animation

- Marie — Chantre + Maître de chœur ;
- Paul — Organiste.

Alice n’est pas ajoutée.

---

# 26. Coche de participation dans le planning

Après validation, le planning peut afficher une coche à côté d’une personne.

Cette coche signifie uniquement :

> cette personne appartient actuellement à l’équipe de l’animation.

La coche ne signifie pas :

- que son état est nécessairement l’état 1 ;
- que ses fonctions actuelles sont identiques à celles figées dans le planning.

---

# 27. Modification de l’équipe après validation

Une fois le planning validé, le Responsable peut toujours modifier directement l’équipe depuis l’animation.

Il peut notamment :

- ajouter une personne ;
- retirer une personne ;
- ajouter une fonction à une personne ;
- retirer une fonction ;
- remplacer une fonction par une autre.

Ces modifications ne rouvrent pas le planning.

---

# 28. Synchronisation des coches

Les coches du planning reflètent en temps réel l’équipe actuelle de l’animation.

Exemple après validation :

| Personne | État planning | Équipe |
|---|---|---|
| Alice | Disponible | ✓ |
| Paul | Indisponible | |
| Marie | Disponible | ✓ |

Le Responsable modifie ensuite directement l’équipe :

- retire Alice ;
- ajoute Paul.

Le planning devient :

| Personne | État planning | Équipe |
|---|---|---|
| Alice | Disponible | |
| Paul | Indisponible | ✓ |
| Marie | Disponible | ✓ |

Les états restent figés.

Seules les coches reflètent la nouvelle équipe.

---

# 29. Écart entre planning figé et équipe réelle

Le système doit accepter qu’un écart existe entre le planning validé et l’équipe réelle.

Exemple :

### Planning figé

> Marie — Disponible — Chantre + Maître de chœur — ✓

### Équipe actuelle

> Marie — Maître de chœur

Marie participe toujours, donc la coche reste présente.

Mais sa fonction réelle a changé.

Autre exemple :

### Planning figé

> Jean — Indisponible — Chantre — ✓

Cela peut arriver si Jean a finalement été ajouté directement à l’animation après validation.

Ce n’est pas une incohérence.

Le planning conserve ce qui avait été déclaré ou arbitré.

L’animation conserve ce qui est réellement prévu.

---

# 30. Absence de synchronisation permanente état 1 → équipe

Après validation, l’état 1 ne pilote plus automatiquement l’équipe.

Le planning ne doit pas continuellement imposer :

> état 1 = membre de l’équipe

L’état 1 est utilisé au moment de la validation pour alimenter l’équipe.

Ensuite :

> l’animation devient la référence opérationnelle pour son équipe.

---

# 31. Dévalidation

## 31.1 Droits

Seul un Responsable peut dévalider une ligne.

---

## 31.2 Effet

La dévalidation :

- rouvre la ligne du planning ;
- permet à nouveau les modifications normales des états et fonctions.

Elle ne supprime pas automatiquement l’équipe déjà enregistrée dans l’animation.

Les deux informations ont désormais une existence propre.

---

## 31.3 Nouvelle validation

Après modification du planning, le Responsable peut valider à nouveau la ligne.

Les personnes en état 1 sont alors de nouveau reportées vers l’animation conformément aux règles de validation.

Le comportement précis d’une nouvelle validation vis-à-vis des membres déjà présents dans l’équipe doit rester non destructif.

Une nouvelle validation ne doit pas supprimer implicitement une personne ajoutée manuellement dans l’animation.

---

# 32. Animations passées

Une animation passée ne peut plus être dévalidée.

Le planning devient alors une donnée historique.

Les états du planning permettent de conserver ce qui avait été déclaré et figé.

Les coches peuvent refléter les personnes enregistrées dans l’équipe de l’animation.

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
- ajoute à l’animation toutes les personnes en état 1 ;
- leur attribue les fonctions sélectionnées.

---

## Étape 6 — Organisation réelle de l’animation

Après validation, le Responsable peut encore modifier directement l’équipe de l’animation.

Le planning reste figé.

Les coches suivent l’équipe réelle.

---

## Étape 7 — Correction éventuelle du planning

Tant que l’animation n’est pas passée, le Responsable peut :

- dévalider ;
- modifier le planning ;
- valider à nouveau.

L’équipe de l’animation n’est pas automatiquement effacée lors de la dévalidation.

---

## Étape 8 — Historique

Une fois l’animation passée :

- elle ne peut plus être dévalidée ;
- les états du planning restent consultables ;
- les fonctions planifiées restent consultables ;
- l’équipe réelle reste identifiable.

---

# 35. Règles métier synthétiques

## Calendrier

**PLAN-CAL-01** — Le calendrier commence par défaut le lundi.

**PLAN-CAL-02** — Le premier jour de semaine peut être une préférence personnelle d’affichage.

**PLAN-CAL-03** — Cette préférence n’a aucun effet métier.

---

## Animations

**PLAN-ANI-01** — Le terme métier générique est « animation ».

**PLAN-ANI-02** — Une animation peut représenter une messe ou un autre type de célébration.

**PLAN-ANI-03** — Chaque animation possède sa propre organisation humaine.

---

## Ensembles dominicaux

**PLAN-DOM-01** — Un ensemble dominical peut contenir une animation principale et plusieurs animations liées.

**PLAN-DOM-02** — L’animation principale sert de référence de préparation.

**PLAN-DOM-03** — Les animations liées possèdent leur propre ligne de planning et leur propre équipe.

**PLAN-DOM-04** — Les animations liées héritent par défaut des éléments de préparation de l’animation principale.

**PLAN-DOM-05** — Une animation liée peut surcharger localement un élément hérité.

**PLAN-DOM-06** — Le triplet jour + heure + lieu doit être unique dans la configuration des animations régulières du groupe.

---

## Génération

**PLAN-GEN-01** — Seul un Responsable peut générer le planning.

**PLAN-GEN-02** — La génération peut être demandée pour un nombre de semaines ou jusqu’à une date.

**PLAN-GEN-03** — La génération utilise les règles régulières et les dates particulières du groupe.

**PLAN-GEN-04** — La génération complète le planning existant sans le remplacer.

**PLAN-GEN-05** — Une génération répétée ne doit pas créer de doublons.

**PLAN-GEN-06** — Plusieurs animations peuvent exister le même jour.

**PLAN-GEN-07** — Date + heure + lieu constituent une information essentielle d’identification d’une occurrence générée.

---

## Tableau

**PLAN-TAB-01** — Une ligne correspond à une animation.

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

**PLAN-FCT-10** — La sélection des fonctions est propre à chaque animation.

**PLAN-FCT-11** — Une personne ne peut sélectionner que parmi ses fonctions possibles.

**PLAN-FCT-12** — L’état et les fonctions sélectionnées sont indépendants.

**PLAN-FCT-13** — Une personne peut exercer plusieurs fonctions dans une même animation.

---

## Modification

**PLAN-MOD-01** — Un membre peut modifier sa propre cellule tant que la ligne n’est pas validée.

**PLAN-MOD-02** — Un membre peut modifier les cellules des Membres AM tant que la ligne n’est pas validée.

**PLAN-MOD-03** — Un membre ne peut pas modifier la cellule d’un autre membre avec compte.

**PLAN-MOD-04** — Un Responsable peut modifier toutes les cellules d’une ligne non validée.

---

## Validation

**PLAN-VAL-01** — Seul un Responsable peut valider une ligne.

**PLAN-VAL-02** — La validation verrouille le planning, pas l’animation.

**PLAN-VAL-03** — Lors de la validation, toutes les personnes en état 1 sont ajoutées à l’équipe de l’animation.

**PLAN-VAL-04** — Les fonctions attribuées lors de la validation sont celles sélectionnées dans la cellule.

**PLAN-VAL-05** — Une personne peut être ajoutée avec plusieurs fonctions.

**PLAN-VAL-06** — L’équipe de l’animation peut être modifiée après validation.

**PLAN-VAL-07** — Une coche indique l’appartenance actuelle à l’équipe de l’animation.

**PLAN-VAL-08** — La coche est indépendante de l’état du planning.

**PLAN-VAL-09** — La coche ne garantit pas que les fonctions réelles sont identiques aux fonctions planifiées.

**PLAN-VAL-10** — Modifier l’équipe ne modifie pas rétroactivement les états ou fonctions figés dans le planning.

**PLAN-VAL-11** — Après validation, l’état 1 ne pilote plus automatiquement l’équipe.

**PLAN-VAL-12** — Seul un Responsable peut dévalider une ligne future.

**PLAN-VAL-13** — La dévalidation rouvre le planning sans supprimer automatiquement l’équipe existante.

**PLAN-VAL-14** — Une nouvelle validation doit être non destructive vis-à-vis des ajouts manuels déjà effectués dans l’animation.

**PLAN-VAL-15** — Une animation passée ne peut plus être dévalidée.

---

## Historique

**PLAN-HIST-01** — Les états figés du planning sont conservés comme historique.

**PLAN-HIST-02** — Les fonctions planifiées sont conservées comme historique.

**PLAN-HIST-03** — L’équipe réelle de l’animation reste distincte de l’historique du planning.

**PLAN-HIST-04** — Modifier les fonctions possibles d’un membre ne réécrit pas l’historique.

**PLAN-HIST-05** — Une fonction retirée du paramétrage reste identifiable dans les données historiques qui l’utilisent.

---

# 36. Points restant à spécifier

Les points suivants ont été identifiés mais ne sont pas encore totalement tranchés.

## 36.1 Collision entre date particulière et animations dominicales

Exemple :

> Noël tombe un dimanche.

Il reste à déterminer précisément si une date particulière :

- ajoute de nouvelles animations ;
- remplace les animations dominicales habituelles ;
- ou peut être configurée au cas par cas pour faire l’un ou l’autre.

Aucune règle implicite ne doit considérer que deux animations à la même date constituent forcément un doublon.

---

## 36.2 Suppression ou modification d’une règle ayant déjà généré des animations

Il reste à définir ce qu’il se passe lorsqu’un Responsable modifie ou supprime une règle de calendrier après que des animations ont déjà été générées.

Le principe général devrait éviter toute suppression silencieuse d’animations déjà organisées.

---

## 36.3 Comportement précis d’une revalidation

Le principe est fixé :

- la dévalidation ne supprime pas l’équipe ;
- une nouvelle validation ajoute les personnes en état 1 ;
- les modifications directes réalisées dans l’animation ne doivent pas être écrasées silencieusement.

Il restera à préciser les règles exactes de fusion lors d’une revalidation.

---

## 36.4 Affichage détaillé des fonctions réelles dans le planning

La coche indique seulement la présence dans l’équipe.

Il reste à déterminer si le planning doit également afficher directement :

- les fonctions réellement exercées ;
- un indicateur de divergence entre fonctions planifiées et fonctions réelles ;
- ou uniquement ces informations dans le détail de l’animation.

---

# 37. Principe directeur

Le planning doit conserver une séparation claire entre trois niveaux :

### 1. Les capacités habituelles de la personne

> Ce que cette personne sait habituellement faire.

Exemple :

> Chantre + Maître de chœur

### 2. Sa proposition dans le planning

> Ce qu’elle propose de faire pour cette animation.

Exemple :

> Disponible — Maître de chœur

### 3. L’équipe réelle de l’animation

> Ce qu’elle fera effectivement.

Exemple :

> Chantre + Maître de chœur

Cette séparation permet de conserver un planning souple, compréhensible et historiquement fidèle sans imposer artificiellement que la situation réelle reste identique à la proposition initiale.
