# SFD-04-celebrations

## 1. Objet du document

Cette spécification décrit les règles fonctionnelles actuellement définies pour la partie **Célébrations** d’Animation Messe.

La célébration est un objet central de l’application. Elle représente principalement une messe, mais le modèle n’est pas limité à la messe.

Le présent document couvre à ce stade :

- l’identité et le cycle de vie d’une célébration ;
- son lien avec le planning ;
- les droits de modification et de validation ;
- les célébrations partagées entre plusieurs groupes ;
- l’archivage et la purge ;
- la visibilité dans le planning et le calendrier ;
- les métadonnées générales ;
- les gabarits de célébration, dans leur principe ;
- les gabarits d’impression ;
- les feuilles de messe.

Les règles détaillées concernant le **déroulé**, les **blocs chants**, les **blocs textes**, l’intégration AELF et la génération automatique avancée restent à préciser.

---

# 2. Philosophie générale

## 2.1. La célébration est la source de vérité du planning

Le planning n’est pas une entité métier autonome.

Chaque ligne du planning correspond à une célébration existante.

Une célébration possède obligatoirement :

- une date ;
- une heure ;
- un lieu ;
- au moins un groupe auquel elle est rattachée.

Le planning du groupe est reconstruit à partir des célébrations.

Il n’existe donc pas de duplication entre :

- une entrée de planning ;
- une célébration.

Créer, déplacer ou supprimer une célébration produit directement l’effet correspondant dans le planning.

## 2.2. Identifiant technique et unicité métier

Une célébration possède un identifiant technique immuable.

La date, l’heure et le lieu ne constituent pas cet identifiant technique car ils peuvent être modifiés.

En revanche, pour un groupe donné, il ne peut pas exister deux célébrations ayant simultanément :

- la même date ;
- la même heure ;
- le même lieu.

La règle fonctionnelle d’unicité est donc :

> **groupe + date + heure + lieu**

Dans le cas d’une célébration partagée entre plusieurs groupes, cette règle doit rester vraie pour chacun des groupes participants.

## 2.3. Nature d’une célébration

Il n’existe pas nécessairement de champ métier imposant un type tel que :

- messe ;
- baptême ;
- mariage ;
- funérailles ;
- adoration ;
- vêpres.

La nature réelle de la célébration est principalement portée par son **déroulé**.

Une messe sera notamment reconnaissable par la succession de blocs qui la composent.

À ce stade, le déroulé ne connaît que deux grandes familles de blocs :

- **bloc chant** ;
- **bloc texte**.

---

# 3. Gabarits de célébration

## 3.1. Principe

Une célébration peut être créée sans gabarit.

Dans ce cas, son déroulé démarre vide.

Pour accélérer la préparation, les groupes peuvent définir des **gabarits de célébration**.

Un gabarit ressemble structurellement à une célébration, mais sert uniquement de structure de départ.

Il permet notamment de prédéfinir :

- l’ordre des blocs ;
- les blocs chants attendus ;
- les blocs textes attendus ;
- la structure habituelle d’une messe ou d’une autre célébration.

Exemple de structure :

1. chant d’entrée ;
2. Kyrie ;
3. Gloria ;
4. première lecture ;
5. etc.

## 3.2. Variantes de gabarits

Un groupe peut disposer de plusieurs gabarits selon ses usages, par exemple :

- messe du temps ordinaire ;
- Avent ;
- Carême ;
- temps pascal ;
- célébration particulière ;
- vigile ;
- solennité ;
- autre besoin local.

Les gabarits ne constituent pas une classification rigide des célébrations.

Ils sont des accélérateurs de préparation.

## 3.3. Niveaux de gabarits

Deux niveaux sont prévus :

- **gabarits globaux**, gérés par les Administrateurs du site ;
- **gabarits propres à un groupe**.

Le partage direct d’un gabarit entre deux groupes n’est pas encore défini.

## 3.4. Utilisation

Un gabarit pourra notamment être utilisé :

- lors de la création manuelle d’une célébration ;
- pendant la modification d’une célébration ;
- lors de la génération automatique de célébrations futures.

Les règles détaillées de remplacement ou de fusion avec un déroulé existant restent à définir.

---

# 4. Membres attachés et droits de modification

## 4.1. Membres attachés

Une célébration peut avoir :

- aucun membre attaché ;
- un ou plusieurs membres attachés.

Le fait d’être attaché à une célébration ne donne pas nécessairement le droit de la modifier.

## 4.2. Attribution automatique du droit de modification

Chaque groupe définit quels rôles de membres obtiennent automatiquement le droit de modifier une célébration lorsqu’ils y sont attachés.

Le cas principal sera souvent celui des chantres, mais le choix appartient au groupe.

Exemple :

- un groupe peut donner automatiquement ce droit aux chantres ;
- un autre groupe peut le donner aux chantres et aux organistes.

## 4.3. Attribution manuelle

Les personnes disposant déjà du droit de modifier la célébration peuvent :

- modifier la liste des membres attachés ;
- attribuer ou retirer le droit de modification aux membres concernés.

## 4.4. Responsables

Les Responsables du groupe disposent toujours des mêmes droits de modification que les membres autorisés à modifier la célébration.

Ils constituent notamment un secours lorsqu’aucun membre attaché n’a de droit de modification.

Cas valides :

- aucun membre attaché ;
- des membres attachés mais aucun membre avec droit de modification.

Dans ces cas, les Responsables peuvent toujours intervenir.

## 4.5. Membres AM

Les Membres AM peuvent être affectés à une célébration.

Ils ne disposent cependant jamais de droit d’accès ou de modification dans l’application.

---

# 5. Validation, verrouillage et fin de modification

## 5.1. Principe

La validation d’une célébration est équivalente à son verrouillage.

Les notions suivantes représentent la même action fonctionnelle :

- valider ;
- figer ;
- bloquer.

La philosophie est la suivante :

> les membres préparent ; les Responsables garantissent et valident.

## 5.2. Qui peut valider

Seuls les **Responsables du groupe responsable de la célébration** peuvent valider ou dévalider une célébration.

Pour une célébration appartenant à un seul groupe, il s’agit naturellement des Responsables de ce groupe.

Pour une célébration partagée, il s’agit uniquement des Responsables du groupe créateur.

## 5.3. Effet de la validation

Une fois validée :

- le déroulé est figé ;
- aucune modification du déroulé n’est possible ;
- les membres avec droit de modification ne peuvent plus modifier ;
- les Responsables eux-mêmes ne peuvent plus modifier le déroulé.

La validation est avant tout un garde-fou contre les modifications accidentelles.

Elle ne constitue pas un mécanisme d’archivage juridique ou de conservation d’états officiels successifs.

## 5.4. Dévalidation

Un Responsable autorisé peut dévalider puis revalider une célébration autant de fois que nécessaire tant que la date de la célébration n’est pas passée.

Il n’existe pas de limite au nombre de cycles :

- validation ;
- dévalidation ;
- modification ;
- nouvelle validation.

## 5.5. Date passée

La règle est fondée uniquement sur la **date**, pas sur l’heure.

Dès que la date de la célébration est passée :

- le déroulé devient définitivement non modifiable ;
- une célébration validée ne peut plus être dévalidée ;
- une célébration jamais validée devient elle aussi définitivement non modifiable.

Exemple :

Une célébration prévue aujourd’hui à 10 h peut encore être modifiée ou dévalidée aujourd’hui à 18 h.

Elle devient définitivement en lecture seule à partir du lendemain.

---

# 6. Modification des informations structurantes

Tant que la célébration reste modifiable, les personnes ayant le droit de modification ainsi que les Responsables peuvent modifier :

- la date ;
- l’heure ;
- le lieu.

Une modification de ces informations déplace naturellement la célébration dans le planning.

## 6.1. Conflit d’unicité

Si une création ou une modification aboutit à une combinaison :

- groupe ;
- date ;
- heure ;
- lieu ;

déjà utilisée par une autre célébration du groupe, l’opération est refusée.

Le message doit :

- expliquer clairement le conflit ;
- proposer un lien direct vers la célébration existante lorsque l’utilisateur a le droit de la voir.

---

# 7. Lieux

Le lieu est un champ texte.

Le groupe peut paramétrer une liste de lieux habituels.

Lors de la saisie d’un lieu :

- les lieux du groupe sont proposés comme suggestions ;
- l’utilisateur peut néanmoins saisir librement un autre lieu.

Le système ne force donc pas l’utilisateur à sélectionner uniquement un lieu préenregistré.

---

# 8. Célébrations partagées entre plusieurs groupes

## 8.1. Principe

Une même célébration réelle ne doit pas être dupliquée pour chaque groupe.

Une célébration peut être rattachée à :

- un groupe ;
- plusieurs groupes.

Les groupes peuvent être jumelés ou non.

Le fonctionnement de la célébration partagée est identique dans les deux cas.

Le jumelage simplifie principalement la recherche et la mise en relation des groupes.

## 8.2. Groupe créateur

Une célébration partagée possède un **groupe créateur**.

Ce groupe est aussi le **groupe responsable** de la célébration.

En V1 :

- le groupe créateur ne peut pas être transféré ;
- aucun mécanisme de transfert de responsabilité n’est prévu.

## 8.3. Ajout d’un autre groupe

En V1, seul le groupe créateur peut ajouter un autre groupe à la célébration.

Un groupe extérieur ne peut pas demander directement à rejoindre une célébration existante.

## 8.4. Retrait d’un groupe

Le groupe créateur peut retirer un groupe participant tant que la célébration n’est pas passée.

Un groupe participant non créateur peut également quitter lui-même une célébration partagée tant qu’elle n’est pas passée.

## 8.5. Effet du retrait

Lorsqu’un groupe quitte ou est retiré :

- tous ses membres attachés à la célébration sont retirés ;
- tous les droits de modification associés à ces membres sont retirés.

## 8.6. Souveraineté sur les membres

Chaque groupe reste souverain sur ses propres membres.

Une personne autorisée à modifier la célébration peut :

- ajouter ou retirer des membres de son propre groupe ;
- gérer les droits de modification des membres de son propre groupe.

Elle ne peut pas :

- ajouter ou retirer les membres d’un autre groupe participant ;
- attribuer ou retirer des droits aux membres d’un autre groupe.

## 8.7. Attribution automatique des droits

Chaque groupe applique ses propres règles de rôles pour attribuer automatiquement les droits de modification à ses membres attachés.

Le partage d’une célébration ne crée pas de règle commune de permissions.

## 8.8. Validation

Pour une célébration partagée :

- tous les groupes participants peuvent contribuer selon leurs droits ;
- seul le groupe créateur porte la responsabilité de la validation ;
- seuls les Responsables du groupe créateur peuvent valider ou dévalider.

## 8.9. Suppression

Seuls les Responsables du groupe créateur peuvent supprimer une célébration partagée.

Les Responsables des autres groupes participants ne peuvent pas supprimer la célébration.

## 8.10. Conflit lors de l’ajout d’un groupe

Si le groupe que l’on tente d’ajouter possède déjà une célébration avec les mêmes :

- date ;
- heure ;
- lieu ;

l’ajout est refusé.

Un message explicite informe l’utilisateur du conflit.

Un lien vers la célébration en conflit n’est proposé que lorsque les groupes sont jumelés et que la visibilité existe déjà.

Dans les autres cas, aucune information supplémentaire sur la célébration du groupe tiers n’est exposée.

---

# 9. Planning et calendrier

## 9.1. Planning

Le planning est une liste de célébrations triées selon :

1. la date ;
2. l’heure.

Une célébration peut apparaître selon trois états visuels :

1. **normale** ;
2. **partagée — mon groupe est responsable** ;
3. **partagée — mon groupe n’est pas responsable**.

Les couleurs correspondant à ces trois états sont paramétrables au niveau du groupe.

Lorsque la place le permet, le planning peut afficher les groupes participant à une célébration partagée.

## 9.2. Calendrier

Le calendrier peut afficher :

- les célébrations propres au groupe ;
- les célébrations partagées auxquelles le groupe participe ;
- les célébrations des groupes jumelés.

Pour une célébration partagée, la liste complète des groupes participants n’a pas vocation à être affichée directement dans la case du calendrier.

Elle peut être accessible :

- au clic ;
- au survol ;
- dans une vue détaillée.

## 9.3. Célébrations d’un groupe jumelé non partagées

Lorsqu’un groupe consulte dans son calendrier une célébration appartenant à un groupe jumelé mais non partagée avec lui, seules les informations minimales suivantes sont accessibles :

- date ;
- heure ;
- lieu ;
- titre ;
- sous-titre ;
- description.

Le déroulé, les chants, les textes, les affectations et les informations internes ne sont pas exposés.

---

# 10. Métadonnées générales de la célébration

## 10.1. Titre

Le titre est obligatoire.

Lors de la création d’une célébration, le système propose automatiquement un titre à partir du contexte liturgique.

Exemple :

> Dimanche 25 août du temps ordinaire

Le titre est ensuite librement modifiable.

Le titre de la célébration est un champ texte stocké.

Il n’est pas automatiquement recalculé lors d’un changement ultérieur de date.

## 10.2. Sous-titre

Le sous-titre est :

- facultatif ;
- librement saisi.

## 10.3. Description

La description est :

- facultative ;
- librement saisie.

---

# 11. Archivage et conservation

## 11.1. Archivage

Une célébration future ou passée peut être marquée comme **archivée**.

L’archivage signifie uniquement :

> cette célébration doit rester dans les annales du groupe.

L’archivage n’a aucun effet sur :

- les droits de modification ;
- la validation ;
- le verrouillage ;
- l’état fonctionnel de la célébration.

Une célébration peut donc être :

- future et archivée ;
- en préparation et archivée ;
- validée et archivée ;
- passée et archivée.

## 11.2. Qui peut archiver

Tous les membres disposant d’un accès à la célébration peuvent :

- archiver ;
- désarchiver.

Cette action peut être réalisée sur une célébration future ou passée.

## 11.3. Effet de l’archive

Tant qu’une célébration est archivée :

- elle ne peut pas être supprimée manuellement ;
- elle ne peut pas être supprimée par la purge automatique.

Pour supprimer une célébration archivée, il faut obligatoirement :

1. la désarchiver ;
2. demander sa suppression.

## 11.4. Désarchivage

Le désarchivage ne réinitialise pas la durée de conservation.

Une célébration désarchivée retrouve immédiatement la règle normale de conservation du groupe.

Si son ancienneté dépasse déjà le délai configuré, elle peut être supprimée dès le prochain passage de la purge automatique, potentiellement le jour même.

---

# 12. Purge automatique

## 12.1. Durée de conservation

Chaque groupe définit une durée de conservation des célébrations exprimée en mois.

Cette durée peut aller jusqu’à **24 mois**.

Le délai est calculé à partir de la date de la célébration.

Exemple :

- célébration : 10 janvier 2026 ;
- conservation du groupe : 12 mois ;
- fin de conservation : 10 janvier 2027.

## 12.2. Suppression automatique

Une célébration :

- non archivée ;
- ayant dépassé la durée de conservation ;

est supprimée automatiquement.

La purge est effectuée par un traitement planifié.

## 12.3. Suppression manuelle

Un Responsable peut supprimer manuellement une célébration non archivée, y compris si elle est future.

Dans le cas d’une célébration partagée, seule l’autorité du groupe créateur peut effectuer cette suppression.

---

# 13. Purge RGPD des affectations

La conservation des affectations nominatives suit une règle différente de celle de la célébration.

Après un délai défini globalement dans la configuration de l’application :

- les affectations des membres sont supprimées.

Ce délai :

- n’est pas configurable par les groupes ;
- est indépendant de la durée de conservation des célébrations ;
- s’applique même à une célébration archivée.

L’archivage permet donc de conserver ce qui a été célébré, mais ne permet pas de contourner la purge RGPD des données nominatives.

---

# 14. Gabarits d’impression

## 14.1. Principe

Les **gabarits d’impression** sont distincts des gabarits de célébration.

Un gabarit de célébration prépare :

> la structure du déroulé.

Un gabarit d’impression prépare :

> la structure et la mise en forme d’une sortie documentaire.

Les gabarits d’impression sont paramétrés au niveau du groupe.

## 14.2. Édition

Un gabarit d’impression utilise un éditeur WYSIWYG.

Il peut contenir :

- du texte ;
- de la mise en forme ;
- des variables.

Un assistant permet d’insérer facilement les variables disponibles.

## 14.3. Variables

Les variables peuvent notamment représenter des informations telles que :

- titre ;
- date ;
- heure ;
- lieu ;
- informations du calendrier liturgique ;
- données issues du déroulé ;
- autres métadonnées disponibles.

Les variables détaillées restent à définir.

Lors de la génération d’un texte brut ou d’une sortie finale, les variables sont remplacées par leur valeur réelle.

## 14.4. Nom des gabarits

Chaque gabarit d’impression possède un nom.

Deux gabarits d’impression d’un même groupe ne peuvent pas avoir le même nom.

## 14.5. Gabarit principal

Le groupe peut désigner un seul gabarit d’impression comme **gabarit principal**.

La feuille générée automatiquement depuis ce gabarit devient la feuille principale de la célébration.

Si un seul gabarit existe, il devient naturellement le gabarit principal.

---

# 15. Génération des feuilles de messe

## 15.1. Déclenchement

Les feuilles de messe ne sont générées qu’après validation du déroulé.

Lorsqu’un Responsable valide la célébration :

- le déroulé est figé ;
- les fonctions liées aux feuilles deviennent disponibles ;
- toutes les feuilles correspondant aux gabarits d’impression du groupe créateur sont générées automatiquement.

## 15.2. Aucun gabarit d’impression

Si le groupe ne possède aucun gabarit d’impression :

- une feuille WYSIWYG vide est créée automatiquement ;
- l’assistant de variables reste disponible ;
- cette feuille devient la feuille principale.

## 15.3. Un ou plusieurs gabarits

Si le groupe possède des gabarits d’impression :

- une feuille est générée automatiquement pour chaque gabarit ;
- aucune feuille vide supplémentaire n’est créée automatiquement.

Une personne souhaitant partir d’une feuille vide peut ensuite vider manuellement le contenu d’une feuille ou créer une nouvelle feuille.

## 15.4. Célébration partagée

Pour une célébration partagée, seuls les **gabarits d’impression du groupe créateur** sont utilisés lors de la génération automatique.

Les gabarits des autres groupes participants ne sont pas utilisés.

---

# 16. Autonomie des feuilles

## 16.1. Principe

Une feuille générée à partir d’un gabarit devient ensuite un objet totalement autonome.

Le gabarit est un accélérateur, pas un formulaire officiel immuable.

Après génération, il est possible de :

- modifier librement la feuille ;
- remplacer des variables par du texte en dur ;
- supprimer du contenu ;
- ajouter de nouvelles variables ;
- changer complètement sa mise en forme ;
- changer sa destination ou son usage ;
- renommer la feuille.

## 16.2. Plusieurs feuilles

Une même célébration peut posséder plusieurs feuilles.

Exemples :

- feuille assemblée ;
- feuille musiciens ;
- feuille chorale ;
- version simplifiée ;
- brouillon ;
- plusieurs variantes pour une célébration importante.

Le nombre de feuilles n’est pas limité fonctionnellement.

## 16.3. Feuille principale

Une seule feuille peut être définie comme **principale**.

La feuille principale correspond à la sortie accessible immédiatement en un clic.

Les autres feuilles demandent une sélection explicite.

L’objectif est notamment d’éviter l’impression en grande quantité d’une mauvaise version.

## 16.4. Suppression de la feuille principale

La feuille principale ne peut pas être supprimée directement.

Pour la supprimer, il faut d’abord désigner une autre feuille comme principale.

---

# 17. Nommage des feuilles

## 17.1. Génération automatique

Lors de la génération automatique, chaque feuille prend le nom de son gabarit d’impression.

L’unicité des noms des gabarits garantit qu’aucun doublon de nom n’est produit à ce moment.

## 17.2. Modification du nom

Après génération, le nom de la feuille est totalement indépendant du nom du gabarit.

Il peut être librement modifié.

Exemple :

- gabarit : `Feuille de messe`
- feuille : `Brouillon feuille de messe de Pâques 1`

## 17.3. Création manuelle

Lorsqu’un utilisateur crée manuellement une nouvelle feuille, il doit explicitement lui donner un nom, même s’il choisit un gabarit d’impression comme point de départ.

## 17.4. Unicité

Deux feuilles appartenant à une même célébration ne peuvent pas porter le même nom.

---

# 18. Lien entre une feuille et son gabarit

## 18.1. Référence conservée

Une feuille conserve la référence vers le gabarit d’impression qui l’a générée.

Cette référence permet notamment :

- de connaître son gabarit d’origine ;
- de proposer une réinitialisation depuis ce gabarit.

## 18.2. Modification du gabarit

Une modification du contenu ou de la structure du gabarit ne modifie jamais automatiquement les feuilles existantes.

Une feuille existante ne reçoit la nouvelle structure qu’après une demande explicite de **réinitialisation depuis le gabarit**.

Cette réinitialisation remplace son contenu à partir de la structure actuelle du gabarit.

## 18.3. Dévalidation puis revalidation

Lorsqu’une célébration est dévalidée :

- toutes ses feuilles sont supprimées.

Lorsqu’elle est ensuite revalidée :

- les feuilles sont recréées ;
- les versions actuelles des gabarits d’impression sont utilisées.

## 18.4. Suppression d’un gabarit

Si un gabarit d’impression est supprimé :

- les feuilles déjà générées à partir de lui restent intactes ;
- seule la référence au gabarit est supprimée ;
- elles ne peuvent plus être réinitialisées depuis ce gabarit supprimé.

---

# 19. Création manuelle de feuilles

Après validation de la célébration, les personnes autorisées à gérer les feuilles peuvent créer de nouvelles feuilles qui n’étaient pas prévues par les gabarits initiaux.

Une nouvelle feuille peut notamment être créée :

- à partir d’un gabarit existant ;
- pour créer une variante supplémentaire ;
- pour créer un brouillon ;
- pour répondre à un besoin exceptionnel.

Les gabarits définissent donc uniquement la génération automatique initiale.

Ils ne limitent pas la suite du workflow.

---

# 20. Droits sur les feuilles de messe

## 20.1. Rôle « Éditeur de feuilles »

Un rôle spécifique de groupe est prévu pour les personnes chargées de la mise en forme documentaire.

Le nom fonctionnel retenu provisoirement est :

> **Éditeur de feuilles**

Ce rôle est cumulable avec les autres rôles du groupe.

Il ne donne aucun droit particulier sur :

- le planning ;
- le déroulé ;
- la validation ;
- la gestion des membres.

## 20.2. Périmètre

Les Éditeurs de feuilles peuvent intervenir uniquement sur les célébrations :

- du jour ;
- futures ;
- validées.

Ils n’interviennent pas sur les feuilles des célébrations passées.

## 20.3. Droits de gestion

Seuls :

- les Responsables ;
- les Éditeurs de feuilles ;

peuvent gérer les feuilles.

Les actions de gestion comprennent notamment :

- créer ;
- modifier ;
- renommer ;
- réinitialiser ;
- changer la feuille principale ;
- supprimer une feuille secondaire.

## 20.4. Lecture et génération

Tous les membres disposant d’un compte et ayant accès à la célébration peuvent :

- consulter le texte brut d’une feuille ;
- générer le PDF correspondant.

Ces droits sont également disponibles pour les Responsables et les Éditeurs de feuilles.

La génération du PDF n’est donc pas une fonction réservée aux personnes chargées de l’édition.

Cette possibilité fournit notamment un mécanisme de secours si les personnes normalement chargées de la préparation ne sont pas disponibles.

---

# 21. Feuilles et célébrations partagées

## 21.1. Gestion

Dans une célébration partagée, la gestion des feuilles appartient exclusivement au **groupe créateur**.

Seuls :

- les Responsables du groupe créateur ;
- les Éditeurs de feuilles du groupe créateur ;

peuvent :

- créer ;
- modifier ;
- renommer ;
- réinitialiser ;
- changer la feuille principale ;
- supprimer des feuilles secondaires.

Les Responsables et Éditeurs de feuilles des autres groupes participants ne disposent d’aucun droit d’édition sur ces feuilles.

## 21.2. Consultation

Tous les membres des groupes participants peuvent néanmoins :

- consulter le texte brut ;
- générer le PDF.

Les feuilles constituent donc une sortie commune de la célébration partagée, même si leur gestion reste sous la responsabilité du groupe créateur.

---

# 22. Cycle de vie et purge des feuilles

Les feuilles de messe sont intimement liées à leur célébration.

Elles ne possèdent aucune politique de purge autonome.

## 22.1. Suppression de la célébration

La suppression ou la purge d’une célébration entraîne la suppression de toutes les feuilles associées.

## 22.2. Archivage

Si une célébration est archivée :

- elle est protégée de la purge ;
- toutes ses feuilles sont automatiquement protégées avec elle.

Aucun archivage séparé des feuilles n’est nécessaire.

## 22.3. Dévalidation

La dévalidation d’une célébration future entraîne immédiatement la suppression de toutes ses feuilles.

Elles seront régénérées lors de la prochaine validation.

---

# 23. Sorties d’une feuille

À ce stade, deux sorties sont explicitement prévues pour tous les membres autorisés à consulter la célébration :

## 23.1. Texte brut

Le texte brut :

- résout les variables ;
- permet un copier/coller vers un autre outil ;
- constitue une sortie simple et robuste.

## 23.2. PDF

Un PDF peut être généré à partir de la feuille de messe.

La mise en forme détaillée du PDF sera définie séparément.

---

# 24. Points encore à spécifier

Les sujets suivants restent volontairement ouverts pour la suite de la SFD :

1. structure détaillée du déroulé ;
2. comportement précis des blocs chants ;
3. comportement précis des blocs textes ;
4. ordre, ajout, suppression et déplacement des blocs ;
5. intégration des textes AELF ;
6. choix et remplacement des textes liturgiques ;
7. gestion des chants et de leurs couplets dans une célébration ;
8. comportement détaillé d’un gabarit de célébration appliqué à un déroulé existant ;
9. règles de génération automatique des célébrations sur plusieurs mois ;
10. association entre calendrier liturgique et gabarits ;
11. gestion des vigiles et cas liturgiques ambigus ;
12. liste complète des variables utilisables dans les gabarits d’impression et les feuilles ;
13. rendu et règles avancées de génération PDF ;
14. éventuel partage de gabarits entre groupes ;
15. détail de la gestion des groupes jumelés.

---

# 25. Principes fonctionnels à conserver

Les décisions prises jusqu’ici suivent plusieurs principes structurants :

- **une célébration réelle = un seul objet**, même lorsqu’elle implique plusieurs groupes ;
- **le planning est dérivé des célébrations** ;
- **chaque groupe reste souverain sur ses membres et leurs droits** ;
- **un groupe créateur unique porte les décisions structurantes d’une célébration partagée** ;
- **la validation est un garde-fou, pas un mécanisme juridique** ;
- **l’archive protège la mémoire de la célébration mais ne contourne pas la purge RGPD** ;
- **les gabarits accélèrent le travail mais ne rendent jamais les objets générés rigides** ;
- **les feuilles de messe sont des sorties de célébrations validées et suivent leur cycle de vie** ;
- **la lecture des sorties est largement accessible, leur édition reste restreinte**.
