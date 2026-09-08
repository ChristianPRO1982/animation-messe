# SFD-04-celebrations

# 1. Objet du document

Cette spécification décrit les règles fonctionnelles actuellement définies pour la partie **Célébrations** d’Animation Messe.

> **Format pour la conception technique**
> Les règles stables de ce document sont identifiées avec le préfixe `CELEB-*`.
> Ces identifiants servent de points d’ancrage pour les modèles, permissions, workflows et tests techniques.

La célébration est un objet central de l’application. Elle représente principalement une messe, mais le modèle n’est pas limité à la messe.

Le présent document couvre à ce stade :

- l’identité et le cycle de vie d’une célébration ;
- son lien avec le planning ;
- les droits de modification et de validation ;
- les célébrations partagées entre plusieurs groupes ;
- l’archivage et la purge ;
- la visibilité dans le planning et le calendrier ;
- les métadonnées générales ;
- les gabarits de célébration ;
- la structure du déroulé ;
- les balises de section ;
- les propriétés communes des blocs ;
- les blocs chants ;
- les tags et la sélection des chants ;
- les refrains et couplets ;
- les blocs textes ;
- l’intégration AELF ;
- le cache AELF ;
- l’autocomplétion ;
- les contrôles de validation ;
- les règles de déplacement, suppression et réinitialisation ;
- les gabarits d’impression ;
- les feuilles de messe.

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

Le changement de gabarit appliqué à une célébration existante est défini plus loin comme une réinitialisation totale explicite du déroulé.

---

# 4. Structure générale du déroulé

## 4.1. Principe

Le déroulé d’une célébration est une **liste plate ordonnée**.

Il n’existe pas de hiérarchie technique de type :

- section contenant des blocs ;
- sous-section ;
- relation parent/enfant entre blocs.

Trois formes d’éléments peuvent apparaître dans cette liste :

- **bloc chant** ;
- **bloc texte** ;
- **balise de section**.

Les blocs chant et texte portent du contenu.

La balise de section est uniquement un élément structurel destiné à améliorer la lecture du déroulé.

## 4.2. Ordre

Chaque élément possède une position dans le déroulé.

L’ordre est recalculé lorsqu’un élément est :

- ajouté ;
- déplacé ;
- supprimé.

La numérotation ne porte aucune autre signification métier que l’ordre des blocs.

---

# 5. Balises de section

## 5.1. Principe

Une balise de section sert à structurer visuellement un déroulé.

Exemples :

- Rites d’ouverture ;
- Liturgie de la Parole ;
- Liturgie eucharistique ;
- Communion ;
- Envoi.

La balise n’est **pas un conteneur**.

Les blocs situés après elle ne lui appartiennent pas techniquement.

## 5.2. Déplacement

Une balise se déplace **seule**.

Déplacer une balise n’entraîne jamais les blocs qui la suivent.

## 5.3. Suppression

Supprimer une balise n’a aucun effet sur les blocs chants ou textes.

Seule la balise disparaît.

L’affichage du déroulé est ensuite recalculé pour tenir compte des balises restantes.

## 5.4. Propriétés d’une balise

Une balise possède au minimum :

- **titre interface** ;
- **titre feuille de messe** ;
- **sous-titre feuille de messe** ;
- **ligne au-dessus** ;
- **ligne au-dessous** ;
- **afficher sur la feuille de messe** ;
- les informations techniques nécessaires à son positionnement.

### 5.4.1. Titre interface

Le titre interface est obligatoire.

Il sert uniquement à structurer clairement le déroulé dans Animation Messe.

### 5.4.2. Titre feuille de messe

Le titre destiné à la feuille de messe est distinct du titre interface.

Il peut être différent.

### 5.4.3. Sous-titre feuille de messe

Le sous-titre est facultatif.

### 5.4.4. Lignes

Deux booléens permettent de demander :

- une ligne au-dessus ;
- une ligne au-dessous.

### 5.4.5. Affichage sur la feuille de messe

Le booléen `afficher sur la feuille de messe` vaut **FALSE par défaut**.

Il ne peut pas être activé si le titre feuille de messe est vide après nettoyage des espaces.

Le contrôle fonctionnel correspond donc à un `trim()` avant validation.

---

# 6. Propriétés communes aux blocs chants et textes

Tous les blocs chants et textes possèdent :

- un **titre interface obligatoire** ;
- un **titre feuille de messe** ;
- un **sous-titre feuille de messe** ;
- un booléen **afficher sur la feuille de messe**.

## 6.1. Titre interface

Le titre visible dans Animation Messe est obligatoire.

Exemples :

- Entrée ;
- Kyrie ;
- Première lecture ;
- Psaume ;
- Évangile ;
- Communion.

## 6.2. Titre feuille de messe

Le titre feuille de messe peut être différent du titre interface.

## 6.3. Sous-titre feuille de messe

Le sous-titre est facultatif.

## 6.4. Affichage sur la feuille de messe

Pour un bloc chant ou texte, `afficher sur la feuille de messe` vaut **TRUE par défaut**.

Si cette option est active, le titre feuille de messe ne peut pas être vide après suppression des espaces inutiles.

---

# 7. Ajout, déplacement, suppression et duplication

## 7.1. Ajout

Des boutons `+` sont présents entre les blocs du déroulé.

Ils permettent d’ajouter directement un nouvel élément à la position voulue.

L’utilisateur peut ajouter :

- un bloc chant ;
- un bloc texte ;
- une balise.

## 7.2. Déplacement

Déplacer un bloc ne modifie que sa position.

Toutes ses données restent inchangées.

Pour un bloc chant, cela inclut notamment :

- le chant choisi ;
- le type principal ;
- le type secondaire ;
- les couplets cochés ;
- les métadonnées du bloc.

Pour un bloc texte, cela inclut notamment :

- le texte final ;
- la source libre ou AELF ;
- la cible AELF ;
- les métadonnées du bloc.

## 7.3. Suppression

Un bloc peut être supprimé tant que la célébration est modifiable.

La suppression est locale :

- aucun autre bloc n’est supprimé ;
- aucun autre bloc n’est modifié ;
- seul l’ordre des blocs restants est recalculé.

## 7.4. Duplication

En V1, il n’existe **pas de fonction de duplication de bloc**.

Un nouveau bloc est toujours créé explicitement.

---

# 8. Blocs chants — source des chants

## 8.1. Répertoire du groupe

Dans une célébration réelle, un bloc chant référence obligatoirement un chant existant.

Dans le sélecteur normal, seuls les chants déjà présents dans le **répertoire du groupe Animation Messe** sont proposés.

## 8.2. Chant présent dans LSS mais absent du répertoire AM

Un chant existant dans Lyrics Slide Show mais absent du répertoire du groupe peut être rapatrié.

Cette opération est volontairement plus longue et explicite.

Le sélecteur courant d’un bloc chant ne doit donc pas afficher tout le catalogue LSS.

## 8.3. Retrait du répertoire du groupe

Si un chant déjà utilisé dans une célébration est retiré du répertoire du groupe :

- le bloc chant existant reste intact ;
- la référence au chant est conservée ;
- les couplets cochés restent conservés ;
- le chant n’est simplement plus proposé normalement pour de nouveaux blocs.

Cette règle permet de préserver les célébrations anciennes et archivées.

## 8.4. Suppression du chant dans LSS

Si le chant est supprimé de LSS :

- les blocs existants ne sont pas supprimés ;
- la référence devient cassée ;
- l’interface doit signaler que le chant source n’existe plus.

Une feuille de messe déjà générée reste exploitable, car elle contient son propre texte final.

---

# 9. Types / tags des chants

## 9.1. Principe

Les types utilisés dans les blocs chants correspondent aux **tags des chants**.

Exemples fréquents :

- Entrée ;
- Kyrie ;
- Gloria ;
- Psaume ;
- Alléluia ;
- Prière universelle ;
- Offertoire ;
- Sanctus ;
- Anamnèse ;
- Agnus Dei ;
- Chant à l’Esprit ;
- Chant à Marie ;
- Ite Missa Est ;
- Chant de sortie ;
- autres tags libres du groupe.

Les tags sont ordonnés.

## 9.2. Type principal

Un bloc chant possède un **type principal obligatoire**.

Lors de la création manuelle d’un bloc chant, le type principal prend par défaut le **premier tag de la liste ordonnée**.

L’utilisateur peut ensuite le modifier.

## 9.3. Type secondaire

Un bloc chant peut posséder un **type secondaire facultatif**.

Le type secondaire sert uniquement à améliorer le classement des propositions de chants.

Il n’intervient pas dans la présélection des couplets.

## 9.4. Philosophie des tags

Animation Messe ne doit pas distinguer techniquement les tags permanents des tags de shortlist.

Exemples de tags durables :

- Kyrie ;
- Gloria ;
- Entrée.

Exemples de tags mouvants :

- Kyrie de l’année ;
- Gloria de l’année ;
- Entrée de l’année ;
- chants Carême 2027 ;
- chants enfants ;
- répertoire messe 18 h.

Fonctionnellement, ce sont tous simplement des tags.

Cette souplesse permet aux groupes de faire évoluer leurs shortlists sans modifier leurs gabarits.

Exemple :

- type principal : `Kyrie de l’année` ;
- type secondaire : `Kyrie`.

Le premier niveau propose la shortlist courante.

Le deuxième niveau propose les autres Kyrie du répertoire.

Changer les chants portant le tag `Kyrie de l’année` met donc implicitement à jour les gabarits qui l’utilisent, sans modifier ces gabarits.

---

# 10. Sélecteur de chants

Après validation des types principal et secondaire, le sélecteur de chants est organisé en trois groupes / onglets :

1. **chants correspondant au type principal** ;
2. **chants correspondant au type secondaire** ;
3. **tous les autres chants du répertoire**.

## 10.1. Absence de doublons

Un chant ne doit apparaître qu’une seule fois.

La priorité est :

> **type principal > type secondaire > tous les autres**

Ainsi :

- un chant correspondant au type principal et secondaire apparaît uniquement dans le premier onglet ;
- un chant correspondant seulement au secondaire apparaît dans le deuxième ;
- le troisième onglet contient uniquement les chants absents des deux premiers.

---

# 11. Blocs chants dans les gabarits de célébration

## 11.1. Aucun chant précis dans un gabarit

Un gabarit de célébration ne sélectionne jamais un chant précis du répertoire.

Il mémorise uniquement :

- un type principal ;
- éventuellement un type secondaire.

## 11.2. Création depuis un gabarit

Lorsqu’une célébration est créée depuis un gabarit :

- le type principal est copié dans le bloc réel ;
- le type secondaire éventuel est copié dans le bloc réel.

Après cette initialisation, le bloc réel devient totalement indépendant du gabarit.

Ses types peuvent être modifiés librement.

## 11.3. Lien au gabarit

Le gabarit n’est pas conservé bloc par bloc.

La célébration conserve seulement la référence à son gabarit de célébration afin de permettre une éventuelle réinitialisation totale.

---

# 12. Réinitialisation totale du déroulé

Changer le gabarit d’une célébration entraîne une **réinitialisation totale du déroulé**.

Cette opération est destructive.

Le déroulé est recréé à partir du nouveau gabarit.

Les données saisies spécifiquement dans les blocs existants peuvent donc être perdues.

L’interface doit afficher un avertissement explicite avant l’opération.

Lors d’une réinitialisation totale :

- tous les blocs sont recréés ;
- les types des blocs chants sont réinitialisés ;
- les paramètres des blocs textes sont réinitialisés ;
- **tous les chants présents après réinitialisation voient leurs coches de couplets recalculées selon leur type principal**.

---

# 13. Structure des chants fournie par LSS

Lyrics Slide Show fournit déjà le découpage des chants.

Animation Messe ne redécoupe pas les chants.

LSS distingue deux grandes catégories :

- **refrains** ;
- **autres blocs**, appelés par défaut `couplets`.

## 13.1. Refrains

Les refrains sont obligatoires.

Ils ne sont pas décochables dans Animation Messe.

## 13.2. Couplets

Les autres blocs sont facultatifs.

Chaque couplet possède une case à cocher permettant de l’inclure ou non dans la célébration.

---

# 14. Tags des couplets

Animation Messe redistribue les tags d’un chant au niveau de ses couplets.

## 14.1. Contrainte

Un couplet ne peut recevoir qu’un tag déjà présent au niveau du chant.

Exemple :

Si un chant possède :

- Entrée ;
- Chant à l’Esprit ;

ses couplets peuvent recevoir :

- Entrée ;
- Chant à l’Esprit.

Ils ne peuvent pas recevoir `Chant de sortie` tant que ce tag n’existe pas au niveau du chant.

## 14.2. Usage

Les tags des couplets servent uniquement à déterminer quels couplets doivent être cochés par défaut lors de l’ajout du chant dans une célébration.

---

# 15. Présélection des couplets

Lorsqu’un chant est **ajouté** dans un bloc, seul le **type principal** du bloc sert à déterminer les couplets cochés par défaut.

Le type secondaire n’a aucun effet sur les coches.

Exemple :

Chant tagué :

- Entrée ;
- Chant à l’Esprit.

Couplets :

- C1 : Entrée + Chant à l’Esprit ;
- C2 : Entrée + Chant à l’Esprit ;
- C3 : Chant à l’Esprit ;
- C4 : Chant à l’Esprit.

Utilisation avec type principal `Entrée` :

- refrain : obligatoire ;
- C1 : coché ;
- C2 : coché ;
- C3 : non coché ;
- C4 : non coché.

Utilisation avec type principal `Chant à l’Esprit` :

- refrain : obligatoire ;
- C1 : coché ;
- C2 : coché ;
- C3 : coché ;
- C4 : coché.

---

# 16. Indépendance des coches de couplets

Après l’ajout d’un chant, les coches appartiennent au bloc de la célébration.

L’utilisateur peut librement :

- cocher un couplet ;
- décocher un couplet.

Ces modifications n’ont aucun effet sur le chant source ni sur le répertoire.

Une fois le chant initialisé :

- modifier les tags du chant ne recalcule pas les coches ;
- modifier les tags des couplets ne recalcule pas les coches ;
- modifier le type principal ne recalcule pas automatiquement les coches ;
- modifier le type secondaire n’a aucun effet sur les coches ;
- modifier un gabarit n’a aucun effet sur les coches existantes.

## 16.1. Cas où les coches sont calculées

Les coches sont calculées :

- lors de l’**ajout d’un nouveau chant** dans un bloc ;
- lors d’une **réinitialisation totale du déroulé**.

## 16.2. Autocomplétion

Une autocomplétion ordinaire ne doit pas recalculer les coches d’un chant déjà présent.

Si l’autocomplétion remplace effectivement un chant par un nouveau chant, celui-ci est initialisé comme tout nouveau chant, donc ses coches sont calculées à partir du type principal.

---

# 17. Blocs texte — modes de source

Un bloc texte possède deux modes de source :

- **texte libre** ;
- **texte AELF**.

Les deux utilisent ensuite le même éditeur de texte final.

---

# 18. Date de célébration et date AELF

Une célébration possède deux dates distinctes :

- **date de célébration** ;
- **date AELF**.

## 18.1. Date de célébration

La date de célébration correspond au jour réel où la célébration a lieu.

Elle sert notamment pour :

- le planning ;
- le calendrier ;
- le cycle de vie ;
- l’archivage ;
- la purge.

## 18.2. Date AELF

La date AELF correspond au jour liturgique utilisé pour récupérer les données auprès d’AELF.

## 18.3. Création manuelle classique

Lors d’une création manuelle ordinaire :

- date de célébration = date choisie ;
- date AELF = même date.

## 18.4. Cas particuliers

Les deux dates peuvent diverger.

Cas typique :

- messe anticipée célébrée le samedi ;
- date de célébration = samedi ;
- date AELF = dimanche.

Dans les créations automatiques, cette différence peut être connue dès l’initialisation.

---

# 19. Cache AELF au niveau de la célébration

## 19.1. Principe

Les données AELF doivent être récupérées puis conservées localement.

Le système ne doit pas refaire un appel API :

- à chaque ouverture de la célébration ;
- pour chaque bloc texte ;
- à chaque affichage.

## 19.2. Premier chargement

Lorsque les données AELF sont nécessaires et qu’aucun cache n’existe :

1. Animation Messe effectue un appel à l’API AELF ;
2. la réponse utile est sauvegardée au niveau de la célébration ;
3. tous les blocs AELF utilisent ensuite cette même source locale.

## 19.3. Donnée source en lecture seule

Le cache AELF représente une copie locale de la réponse API.

Il ne peut jamais être modifié par l’utilisateur.

## 19.4. Stockage

La conception technique peut conserver notamment :

- le payload AELF complet ou la partie utile ;
- la date AELF concernée ;
- la date/heure du dernier refresh ;
- les métadonnées utiles à l’exploitation ou au diagnostic.

Le choix précis du schéma relève de la conception technique.

---

# 20. Refresh AELF

## 20.1. Déclenchement

L’utilisateur peut demander explicitement un **refresh AELF**.

Le refresh met uniquement à jour le cache source de la célébration.

## 20.2. Changement de date AELF

Si la date AELF change, le système propose à l’utilisateur de faire un refresh.

Le changement de date ne déclenche pas automatiquement un appel API.

## 20.3. Aucun impact automatique sur les blocs

Un refresh AELF ne modifie jamais les textes finaux existants.

Après le refresh, une popup indique clairement que les textes des blocs n’ont pas été mis à jour.

Elle explique que l’utilisateur peut :

- lancer une autocomplétion avec écrasement ;
- revenir manuellement sur les blocs texte concernés et les réimporter un par un.

---

# 21. Cibles AELF dans les gabarits

## 21.1. Principe

Un gabarit de célébration peut contenir des blocs texte configurés pour viser un texte AELF précis.

Exemple pour une messe ordinaire :

- Première lecture ;
- Psaume ;
- Deuxième lecture ;
- Évangile.

## 21.2. Cas particuliers

Le système doit pouvoir gérer les structures réellement proposées dans le JSON AELF, notamment :

- plusieurs messes pour une même date ;
- messe de la veille ;
- messe de la nuit ;
- messe de l’aurore ;
- messe du jour ;
- lectures optionnelles ;
- séquences ;
- cantiques ;
- épîtres ;
- entrées messianiques ;
- variantes ;
- autres textes spécifiques proposés par AELF.

Le modèle ne doit donc pas être limité à quatre types de textes codés en dur.

---

# 22. Référence AELF

L’ancien site PHP utilisait principalement une référence positionnelle du type :

- `1-1` ;
- `1-2` ;
- `2-4`.

Cette référence signifiait :

> numéro de messe dans le JSON + numéro de texte dans cette messe.

Pour la refonte, le besoin fonctionnel reste de pouvoir retrouver précisément un texte AELF.

Cependant, le nouveau modèle doit être plus explicite.

Il peut représenter notamment :

- la messe / célébration AELF ciblée ;
- son libellé ;
- le type de texte ;
- le libellé du texte ;
- les informations permettant de retrouver l’entrée exacte ;
- éventuellement l’index positionnel AELF comme fallback technique.

La logique métier ne doit pas dépendre uniquement d’une chaîne opaque de type `2-4`.

---

# 23. Source AELF et texte final du bloc

Un bloc texte AELF distingue clairement deux niveaux.

## 23.1. Source AELF

La source vient du cache de la célébration.

Elle est en lecture seule.

Elle ne peut pas être modifiée par l’utilisateur.

## 23.2. Texte final

Le bloc possède un texte final indépendant.

Ce texte peut être initialisé à partir de la source AELF.

Après import, il devient totalement libre.

L’utilisateur peut :

- le modifier ;
- le raccourcir ;
- le compléter ;
- le reformater ;
- supprimer certaines parties ;
- l’effacer ;
- le remplacer entièrement.

Aucune vérification de conformité avec le texte AELF n’est effectuée.

La référence AELF sert uniquement de **source de départ**.

---

# 24. Construction du texte final AELF

Les données AELF peuvent fournir différentes composantes :

- type ;
- titre ;
- référence biblique ;
- introduction ;
- contenu ;
- refrain psalmique ;
- référence du refrain ;
- verset d’évangile ;
- référence du verset ;
- formule finale ;
- autres champs présents dans la réponse AELF.

Le groupe peut définir comment ces éléments sont utilisés pour construire le texte final d’un bloc.

La construction repose sur la même mécanique légère de template que le reste de l’application.

Exemple conceptuel :

```text
# {{ titre }}

{{ reference }}

{{ texte }}

{{ formule_finale }}
```

La liste exacte des variables sera définie séparément.

---

# 25. Éditeur des blocs texte

## 25.1. Éditeur unique

Les textes libres et les textes AELF utilisent exactement le même éditeur.

## 25.2. Mini-Markdown

L’éditeur reste volontairement simple.

Il permet au minimum :

- gras ;
- italique ;
- souligné ;
- listes à puces ;
- titre niveau 1 ;
- titre niveau 2 ;
- titre niveau 3.

## 25.3. Variables

Les variables utilisent une syntaxe inspirée de Jinja :

```text
{{ ma_variable }}
```

## 25.4. Variables générales

Même un texte libre peut utiliser des variables générales, par exemple :

- date ;
- heure ;
- lieu ;
- titre ;
- autres informations de célébration ;
- variables ou paramètres définis au niveau du groupe.

## 25.5. Variables AELF

Un bloc AELF dispose en plus des variables correspondant aux données AELF ciblées.

Un assistant de variables doit permettre leur insertion facilement.

---

# 26. Autocomplétion du déroulé

## 26.1. Principe

Une action globale **Autocompléter** permet de renseigner automatiquement les blocs selon les règles déjà définies.

Il ne s’agit pas d’un système intelligent ou d’un LLM.

Le comportement est déterministe.

## 26.2. Blocs chants

Pour les blocs chants, l’autocomplétion utilise notamment :

- le type principal ;
- le type secondaire ;
- les tags des chants ;
- l’ordre de préférence du sélecteur.

## 26.3. Blocs textes

Pour les blocs AELF, l’autocomplétion utilise :

- la date AELF ;
- le cache AELF ;
- la cible AELF du bloc ;
- le template de construction du texte final.

## 26.4. Choix utilisateur

Si des données existent déjà, l’utilisateur doit choisir explicitement entre :

- **Compléter uniquement les champs vides** ;
- **Écraser et recalculer les données existantes** ;
- **Annuler**.

### 26.4.1. Compléter

Le mode Compléter :

- remplit uniquement les blocs vides ;
- ne touche pas à un chant déjà choisi ;
- ne touche pas à un texte final déjà renseigné.

### 26.4.2. Écraser

Le mode Écraser :

- réapplique les règles d’autocomplétion ;
- peut remplacer les chants existants ;
- peut remplacer les textes finaux existants.

Il s’agit d’une action destructive qui doit être annoncée clairement.

### 26.4.3. Couplets

L’autocomplétion ne recalcule pas les coches d’un chant déjà présent uniquement parce qu’elle est lancée.

Si elle remplace un chant par un nouveau chant, ce nouveau chant reçoit naturellement sa présélection initiale selon le type principal.

La réinitialisation générale de toutes les coches reste réservée à la **réinitialisation totale du déroulé**.

---

# 27. Validation du déroulé

La validation d’une célébration effectue des contrôles simples et déterministes.

## 27.1. Blocs chants

Tous les blocs chants doivent avoir un chant choisi.

Un bloc chant peut rester sans chant pendant la préparation.

Il empêche simplement la validation tant qu’il reste vide.

## 27.2. Blocs textes

Tous les blocs textes doivent avoir un texte final renseigné.

## 27.3. Contrôle du vide

Le contrôle porte uniquement sur le fait qu’un champ soit vide ou non après nettoyage des espaces.

Le système ne réalise pas :

- de contrôle de longueur ;
- d’analyse syntaxique ;
- d’analyse sémantique ;
- de contrôle liturgique intelligent ;
- d’analyse LLM.

L’objectif est uniquement d’empêcher la validation d’un déroulé manifestement incomplet.

---

# 28. Membres attachés et droits de modification

## 28.1. Membres attachés

Une célébration peut avoir :

- aucun membre attaché ;
- un ou plusieurs membres attachés.

Le fait d’être attaché à une célébration ne donne pas nécessairement le droit de la modifier.

## 28.2. Attribution automatique du droit de modification

Chaque groupe définit quels rôles de membres obtiennent automatiquement le droit de modifier une célébration lorsqu’ils y sont attachés.

Le cas principal sera souvent celui des chantres, mais le choix appartient au groupe.

Exemple :

- un groupe peut donner automatiquement ce droit aux chantres ;
- un autre groupe peut le donner aux chantres et aux organistes.

## 28.3. Attribution manuelle

Les personnes disposant déjà du droit de modifier la célébration peuvent :

- modifier la liste des membres attachés ;
- attribuer ou retirer le droit de modification aux membres concernés.

## 28.4. Responsables

Les Responsables du groupe disposent toujours des mêmes droits de modification que les membres autorisés à modifier la célébration.

Ils constituent notamment un secours lorsqu’aucun membre attaché n’a de droit de modification.

Cas valides :

- aucun membre attaché ;
- des membres attachés mais aucun membre avec droit de modification.

Dans ces cas, les Responsables peuvent toujours intervenir.

## 28.5. Membres AM

Les Membres AM peuvent être affectés à une célébration.

Ils ne disposent cependant jamais de droit d’accès ou de modification dans l’application.

---

# 29. Validation, verrouillage et fin de modification

## 29.1. Principe

La validation d’une célébration est équivalente à son verrouillage.

Les notions suivantes représentent la même action fonctionnelle :

- valider ;
- figer ;
- bloquer.

La philosophie est la suivante :

> les membres préparent ; les Responsables garantissent et valident.

## 29.2. Qui peut valider

Seuls les **Responsables du groupe responsable de la célébration** peuvent valider ou dévalider une célébration.

Pour une célébration appartenant à un seul groupe, il s’agit naturellement des Responsables de ce groupe.

Pour une célébration partagée, il s’agit uniquement des Responsables du groupe créateur.

## 29.3. Effet de la validation

Une fois validée :

- le déroulé est figé ;
- aucune modification du déroulé n’est possible ;
- les membres avec droit de modification ne peuvent plus modifier ;
- les Responsables eux-mêmes ne peuvent plus modifier le déroulé.

La validation est avant tout un garde-fou contre les modifications accidentelles.

Elle ne constitue pas un mécanisme d’archivage juridique ou de conservation d’états officiels successifs.

## 29.4. Dévalidation

Un Responsable autorisé peut dévalider puis revalider une célébration autant de fois que nécessaire tant que la date de la célébration n’est pas passée.

Il n’existe pas de limite au nombre de cycles :

- validation ;
- dévalidation ;
- modification ;
- nouvelle validation.

## 29.5. Date passée

La règle est fondée uniquement sur la **date**, pas sur l’heure.

Dès que la date de la célébration est passée :

- le déroulé devient définitivement non modifiable ;
- une célébration validée ne peut plus être dévalidée ;
- une célébration jamais validée devient elle aussi définitivement non modifiable.

Exemple :

Une célébration prévue aujourd’hui à 10 h peut encore être modifiée ou dévalidée aujourd’hui à 18 h.

Elle devient définitivement en lecture seule à partir du lendemain.

---

# 30. Modification des informations structurantes

Tant que la célébration reste modifiable, les personnes ayant le droit de modification ainsi que les Responsables peuvent modifier :

- la date ;
- l’heure ;
- le lieu.

Une modification de ces informations déplace naturellement la célébration dans le planning.

## 30.1. Conflit d’unicité

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

# 31. Lieux

Le lieu est un champ texte.

Le groupe peut paramétrer une liste de lieux habituels.

Lors de la saisie d’un lieu :

- les lieux du groupe sont proposés comme suggestions ;
- l’utilisateur peut néanmoins saisir librement un autre lieu.

Le système ne force donc pas l’utilisateur à sélectionner uniquement un lieu préenregistré.

---

# 32. Célébrations partagées entre plusieurs groupes

## 32.1. Principe

Une même célébration réelle ne doit pas être dupliquée pour chaque groupe.

Une célébration peut être rattachée à :

- un groupe ;
- plusieurs groupes.

Les groupes peuvent être jumelés ou non.

Le fonctionnement de la célébration partagée est identique dans les deux cas.

Le jumelage simplifie principalement la recherche et la mise en relation des groupes.

## 32.2. Groupe créateur

Une célébration partagée possède un **groupe créateur**.

Ce groupe est aussi le **groupe responsable** de la célébration.

En V1 :

- le groupe créateur ne peut pas être transféré ;
- aucun mécanisme de transfert de responsabilité n’est prévu.

## 32.3. Ajout d’un autre groupe

En V1, seul le groupe créateur peut ajouter un autre groupe à la célébration.

Un groupe extérieur ne peut pas demander directement à rejoindre une célébration existante.

## 32.4. Retrait d’un groupe

Le groupe créateur peut retirer un groupe participant tant que la célébration n’est pas passée.

Un groupe participant non créateur peut également quitter lui-même une célébration partagée tant qu’elle n’est pas passée.

## 32.5. Effet du retrait

Lorsqu’un groupe quitte ou est retiré :

- tous ses membres attachés à la célébration sont retirés ;
- tous les droits de modification associés à ces membres sont retirés.

## 32.6. Souveraineté sur les membres

Chaque groupe reste souverain sur ses propres membres.

Une personne autorisée à modifier la célébration peut :

- ajouter ou retirer des membres de son propre groupe ;
- gérer les droits de modification des membres de son propre groupe.

Elle ne peut pas :

- ajouter ou retirer les membres d’un autre groupe participant ;
- attribuer ou retirer des droits aux membres d’un autre groupe.

## 32.7. Attribution automatique des droits

Chaque groupe applique ses propres règles de rôles pour attribuer automatiquement les droits de modification à ses membres attachés.

Le partage d’une célébration ne crée pas de règle commune de permissions.

## 32.8. Validation

Pour une célébration partagée :

- tous les groupes participants peuvent contribuer selon leurs droits ;
- seul le groupe créateur porte la responsabilité de la validation ;
- seuls les Responsables du groupe créateur peuvent valider ou dévalider.

## 32.9. Suppression

Seuls les Responsables du groupe créateur peuvent supprimer une célébration partagée.

Les Responsables des autres groupes participants ne peuvent pas supprimer la célébration.

## 32.10. Conflit lors de l’ajout d’un groupe

Si le groupe que l’on tente d’ajouter possède déjà une célébration avec les mêmes :

- date ;
- heure ;
- lieu ;

l’ajout est refusé.

Un message explicite informe l’utilisateur du conflit.

Un lien vers la célébration en conflit n’est proposé que lorsque les groupes sont jumelés et que la visibilité existe déjà.

Dans les autres cas, aucune information supplémentaire sur la célébration du groupe tiers n’est exposée.

---

# 33. Planning et calendrier

## 33.1. Planning

Le planning est une liste de célébrations triées selon :

1. la date ;
2. l’heure.

Une célébration peut apparaître selon trois états visuels :

1. **normale** ;
2. **partagée — mon groupe est responsable** ;
3. **partagée — mon groupe n’est pas responsable**.

Les couleurs correspondant à ces trois états sont paramétrables au niveau du groupe.

Lorsque la place le permet, le planning peut afficher les groupes participant à une célébration partagée.

## 33.2. Calendrier

Le calendrier peut afficher :

- les célébrations propres au groupe ;
- les célébrations partagées auxquelles le groupe participe ;
- les célébrations des groupes jumelés.

Pour une célébration partagée, la liste complète des groupes participants n’a pas vocation à être affichée directement dans la case du calendrier.

Elle peut être accessible :

- au clic ;
- au survol ;
- dans une vue détaillée.

## 33.3. Célébrations d’un groupe jumelé non partagées

Lorsqu’un groupe consulte dans son calendrier une célébration appartenant à un groupe jumelé mais non partagée avec lui, seules les informations minimales suivantes sont accessibles :

- date ;
- heure ;
- lieu ;
- titre ;
- sous-titre ;
- description.

Le déroulé, les chants, les textes, les affectations et les informations internes ne sont pas exposés.

---

# 34. Métadonnées générales de la célébration

## 34.1. Titre

Le titre est obligatoire.

Lors de la création d’une célébration, le système propose automatiquement un titre à partir du contexte liturgique.

Exemple :

> Dimanche 25 août du temps ordinaire

Le titre est ensuite librement modifiable.

Le titre de la célébration est un champ texte stocké.

Il n’est pas automatiquement recalculé lors d’un changement ultérieur de date.

## 34.2. Sous-titre

Le sous-titre est :

- facultatif ;
- librement saisi.

## 34.3. Description

La description est :

- facultative ;
- librement saisie.

---

# 35. Archivage et conservation

## 35.1. Archivage

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

## 35.2. Qui peut archiver

Tous les membres disposant d’un accès à la célébration peuvent :

- archiver ;
- désarchiver.

Cette action peut être réalisée sur une célébration future ou passée.

## 35.3. Effet de l’archive

Tant qu’une célébration est archivée :

- elle ne peut pas être supprimée manuellement ;
- elle ne peut pas être supprimée par la purge automatique.

Pour supprimer une célébration archivée, il faut obligatoirement :

1. la désarchiver ;
2. demander sa suppression.

## 35.4. Désarchivage

Le désarchivage ne réinitialise pas la durée de conservation.

Une célébration désarchivée retrouve immédiatement la règle normale de conservation du groupe.

Si son ancienneté dépasse déjà le délai configuré, elle peut être supprimée dès le prochain passage de la purge automatique, potentiellement le jour même.

---

# 36. Purge automatique

## 36.1. Durée de conservation

Chaque groupe définit une durée de conservation des célébrations exprimée en mois.

Cette durée peut aller jusqu’à **24 mois**.

Le délai est calculé à partir de la date de la célébration.

Exemple :

- célébration : 10 janvier 2026 ;
- conservation du groupe : 12 mois ;
- fin de conservation : 10 janvier 2027.

## 36.2. Suppression automatique

Une célébration :

- non archivée ;
- ayant dépassé la durée de conservation ;

est supprimée automatiquement.

La purge est effectuée par un traitement planifié.

## 36.3. Suppression manuelle

Un Responsable peut supprimer manuellement une célébration non archivée, y compris si elle est future.

Dans le cas d’une célébration partagée, seule l’autorité du groupe créateur peut effectuer cette suppression.

---

# 37. Purge RGPD des affectations

La conservation des affectations nominatives suit une règle différente de celle de la célébration.

Après un délai défini globalement dans la configuration de l’application :

- les affectations des membres sont supprimées.

Ce délai :

- n’est pas configurable par les groupes ;
- est indépendant de la durée de conservation des célébrations ;
- s’applique même à une célébration archivée.

L’archivage permet donc de conserver ce qui a été célébré, mais ne permet pas de contourner la purge RGPD des données nominatives.

---

# 38. Gabarits d’impression

## 38.1. Principe

Les **gabarits d’impression** sont distincts des gabarits de célébration.

Un gabarit de célébration prépare :

> la structure du déroulé.

Un gabarit d’impression prépare :

> la structure et la mise en forme d’une sortie documentaire.

Les gabarits d’impression sont paramétrés au niveau du groupe.

## 38.2. Édition

Un gabarit d’impression utilise un éditeur WYSIWYG.

Il peut contenir :

- du texte ;
- de la mise en forme ;
- des variables.

Un assistant permet d’insérer facilement les variables disponibles.

## 38.3. Variables

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

## 38.4. Nom des gabarits

Chaque gabarit d’impression possède un nom.

Deux gabarits d’impression d’un même groupe ne peuvent pas avoir le même nom.

## 38.5. Gabarit principal

Le groupe peut désigner un seul gabarit d’impression comme **gabarit principal**.

La feuille générée automatiquement depuis ce gabarit devient la feuille principale de la célébration.

Si un seul gabarit existe, il devient naturellement le gabarit principal.

---

# 39. Génération des feuilles de messe

## 39.1. Déclenchement

Les feuilles de messe ne sont générées qu’après validation du déroulé.

Lorsqu’un Responsable valide la célébration :

- le déroulé est figé ;
- les fonctions liées aux feuilles deviennent disponibles ;
- toutes les feuilles correspondant aux gabarits d’impression du groupe créateur sont générées automatiquement.

## 39.2. Aucun gabarit d’impression

Si le groupe ne possède aucun gabarit d’impression :

- une feuille WYSIWYG vide est créée automatiquement ;
- l’assistant de variables reste disponible ;
- cette feuille devient la feuille principale.

## 39.3. Un ou plusieurs gabarits

Si le groupe possède des gabarits d’impression :

- une feuille est générée automatiquement pour chaque gabarit ;
- aucune feuille vide supplémentaire n’est créée automatiquement.

Une personne souhaitant partir d’une feuille vide peut ensuite vider manuellement le contenu d’une feuille ou créer une nouvelle feuille.

## 39.4. Célébration partagée

Pour une célébration partagée, seuls les **gabarits d’impression du groupe créateur** sont utilisés lors de la génération automatique.

Les gabarits des autres groupes participants ne sont pas utilisés.

---

# 40. Autonomie des feuilles

## 40.1. Principe

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

## 40.2. Plusieurs feuilles

Une même célébration peut posséder plusieurs feuilles.

Exemples :

- feuille assemblée ;
- feuille musiciens ;
- feuille chorale ;
- version simplifiée ;
- brouillon ;
- plusieurs variantes pour une célébration importante.

Le nombre de feuilles n’est pas limité fonctionnellement.

## 40.3. Feuille principale

Une seule feuille peut être définie comme **principale**.

La feuille principale correspond à la sortie accessible immédiatement en un clic.

Les autres feuilles demandent une sélection explicite.

L’objectif est notamment d’éviter l’impression en grande quantité d’une mauvaise version.

## 40.4. Suppression de la feuille principale

La feuille principale ne peut pas être supprimée directement.

Pour la supprimer, il faut d’abord désigner une autre feuille comme principale.

---

# 41. Nommage des feuilles

## 41.1. Génération automatique

Lors de la génération automatique, chaque feuille prend le nom de son gabarit d’impression.

L’unicité des noms des gabarits garantit qu’aucun doublon de nom n’est produit à ce moment.

## 41.2. Modification du nom

Après génération, le nom de la feuille est totalement indépendant du nom du gabarit.

Il peut être librement modifié.

Exemple :

- gabarit : `Feuille de messe`
- feuille : `Brouillon feuille de messe de Pâques 1`

## 41.3. Création manuelle

Lorsqu’un utilisateur crée manuellement une nouvelle feuille, il doit explicitement lui donner un nom, même s’il choisit un gabarit d’impression comme point de départ.

## 41.4. Unicité

Deux feuilles appartenant à une même célébration ne peuvent pas porter le même nom.

---

# 42. Lien entre une feuille et son gabarit

## 42.1. Référence conservée

Une feuille conserve la référence vers le gabarit d’impression qui l’a générée.

Cette référence permet notamment :

- de connaître son gabarit d’origine ;
- de proposer une réinitialisation depuis ce gabarit.

## 42.2. Modification du gabarit

Une modification du contenu ou de la structure du gabarit ne modifie jamais automatiquement les feuilles existantes.

Une feuille existante ne reçoit la nouvelle structure qu’après une demande explicite de **réinitialisation depuis le gabarit**.

Cette réinitialisation remplace son contenu à partir de la structure actuelle du gabarit.

## 42.3. Dévalidation puis revalidation

Lorsqu’une célébration est dévalidée :

- toutes ses feuilles sont supprimées.

Lorsqu’elle est ensuite revalidée :

- les feuilles sont recréées ;
- les versions actuelles des gabarits d’impression sont utilisées.

## 42.4. Suppression d’un gabarit

Si un gabarit d’impression est supprimé :

- les feuilles déjà générées à partir de lui restent intactes ;
- seule la référence au gabarit est supprimée ;
- elles ne peuvent plus être réinitialisées depuis ce gabarit supprimé.

---

# 43. Création manuelle de feuilles

Après validation de la célébration, les personnes autorisées à gérer les feuilles peuvent créer de nouvelles feuilles qui n’étaient pas prévues par les gabarits initiaux.

Une nouvelle feuille peut notamment être créée :

- à partir d’un gabarit existant ;
- pour créer une variante supplémentaire ;
- pour créer un brouillon ;
- pour répondre à un besoin exceptionnel.

Les gabarits définissent donc uniquement la génération automatique initiale.

Ils ne limitent pas la suite du workflow.

---

# 44. Droits sur les feuilles de messe

## 44.1. Rôle « Éditeur de feuilles »

Un rôle spécifique de groupe est prévu pour les personnes chargées de la mise en forme documentaire.

Le nom fonctionnel retenu provisoirement est :

> **Éditeur de feuilles**

Ce rôle est cumulable avec les autres rôles du groupe.

Il ne donne aucun droit particulier sur :

- le planning ;
- le déroulé ;
- la validation ;
- la gestion des membres.

## 44.2. Périmètre

Les Éditeurs de feuilles peuvent intervenir uniquement sur les célébrations :

- du jour ;
- futures ;
- validées.

Ils n’interviennent pas sur les feuilles des célébrations passées.

## 44.3. Droits de gestion

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

## 44.4. Lecture et génération

Tous les membres disposant d’un compte et ayant accès à la célébration peuvent :

- consulter le texte brut d’une feuille ;
- générer le PDF correspondant.

Ces droits sont également disponibles pour les Responsables et les Éditeurs de feuilles.

La génération du PDF n’est donc pas une fonction réservée aux personnes chargées de l’édition.

Cette possibilité fournit notamment un mécanisme de secours si les personnes normalement chargées de la préparation ne sont pas disponibles.

---

# 45. Feuilles et célébrations partagées

## 45.1. Gestion

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

## 45.2. Consultation

Tous les membres des groupes participants peuvent néanmoins :

- consulter le texte brut ;
- générer le PDF.

Les feuilles constituent donc une sortie commune de la célébration partagée, même si leur gestion reste sous la responsabilité du groupe créateur.

---

# 46. Cycle de vie et purge des feuilles

Les feuilles de messe sont intimement liées à leur célébration.

Elles ne possèdent aucune politique de purge autonome.

## 46.1. Suppression de la célébration

La suppression ou la purge d’une célébration entraîne la suppression de toutes les feuilles associées.

## 46.2. Archivage

Si une célébration est archivée :

- elle est protégée de la purge ;
- toutes ses feuilles sont automatiquement protégées avec elle.

Aucun archivage séparé des feuilles n’est nécessaire.

## 46.3. Dévalidation

La dévalidation d’une célébration future entraîne immédiatement la suppression de toutes ses feuilles.

Elles seront régénérées lors de la prochaine validation.

---

# 47. Sorties d’une feuille

À ce stade, deux sorties sont explicitement prévues pour tous les membres autorisés à consulter la célébration :

## 47.1. Texte brut

Le texte brut :

- résout les variables ;
- permet un copier/coller vers un autre outil ;
- constitue une sortie simple et robuste.

## 47.2. PDF

Un PDF peut être généré à partir de la feuille de messe.

La mise en forme détaillée du PDF sera définie séparément.

---

# 48. Règles fonctionnelles essentielles

## 48.1. Identité et planning

**CELEB-ID-01** — La célébration est l’objet métier canonique utilisé par le planning.

**CELEB-ID-02** — Une ligne de planning correspond à une célébration existante.

**CELEB-ID-03** — Une célébration possède un identifiant technique immuable.

**CELEB-ID-04** — Pour un groupe donné, la combinaison groupe + date + heure + lieu doit être unique.

**CELEB-ID-05** — Une célébration partagée doit respecter cette unicité pour chacun des groupes participants.

## 48.2. Déroulé

**CELEB-DER-01** — Le déroulé d’une célébration est une liste plate ordonnée.

**CELEB-DER-02** — Un élément de déroulé est un bloc chant, un bloc texte ou une balise de section.

**CELEB-DER-03** — Une balise de section n’est pas un conteneur.

**CELEB-DER-04** — Déplacer ou supprimer une balise ne déplace ni ne supprime les blocs voisins.

**CELEB-DER-05** — Changer le gabarit d’une célébration provoque une réinitialisation totale explicite du déroulé.

## 48.3. Chants

**CELEB-CHANT-01** — Un bloc chant réel référence un chant existant ou une référence historique cassée.

**CELEB-CHANT-02** — Le sélecteur normal ne propose que les chants présents dans le répertoire du groupe.

**CELEB-CHANT-03** — Retirer un chant du répertoire ne modifie pas les blocs chants existants.

**CELEB-CHANT-04** — Supprimer un chant dans LSS ne supprime pas automatiquement les blocs déjà présents dans les célébrations.

**CELEB-CHANT-05** — Les coches de couplets appartiennent au bloc de célébration après initialisation.

**CELEB-CHANT-06** — Seul le type principal sert à présélectionner les couplets.

## 48.4. Textes et AELF

**CELEB-AELF-01** — La date de célébration et la date AELF sont deux informations distinctes.

**CELEB-AELF-02** — Les données AELF sont mises en cache au niveau de la célébration.

**CELEB-AELF-03** — Le cache AELF est une donnée source en lecture seule.

**CELEB-AELF-04** — Le texte final d’un bloc AELF est indépendant et librement modifiable après import.

**CELEB-AELF-05** — Un refresh AELF ne modifie jamais automatiquement les textes finaux existants.

## 48.5. Validations

**CELEB-VAL-01** — La validation de célébration verrouille le déroulé.

**CELEB-VAL-02** — Seuls les Responsables du groupe responsable peuvent valider ou dévalider une célébration.

**CELEB-VAL-03** — Pour une célébration partagée, seuls les Responsables du groupe créateur peuvent valider ou dévalider.

**CELEB-VAL-04** — La validation de célébration est distincte de la validation du planning.

**CELEB-VAL-05** — Une célébration dont la date est passée devient définitivement non modifiable.

## 48.6. Partage, archive et feuilles

**CELEB-PART-01** — Une célébration réelle partagée entre plusieurs groupes reste un seul objet.

**CELEB-PART-02** — Le groupe créateur est le groupe responsable de la célébration partagée.

**CELEB-ARCH-01** — L’archivage protège une célébration de la suppression manuelle et de la purge automatique.

**CELEB-RGPD-01** — L’archivage ne contourne pas la purge RGPD des affectations nominatives.

**CELEB-FEUILLE-01** — Les feuilles de messe sont générées après validation de la célébration.

**CELEB-FEUILLE-02** — Les feuilles suivent le cycle de vie de leur célébration.

**CELEB-FEUILLE-03** — Dans une célébration partagée, les feuilles sont gérées par le groupe créateur.

---

# 49. Principes fonctionnels à conserver

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

# 50. Principes fonctionnels structurants

## 50.1. Liste plate

Le déroulé reste une liste plate.

Les balises structurent l’affichage sans créer de hiérarchie.

## 50.2. Pas de recalcul caché

Une donnée initialisée dans une célébration devient ensuite souveraine.

Exemples :

- une coche de couplet reste telle quelle ;
- un texte final AELF reste inchangé après refresh ;
- un bloc reste inchangé lorsqu’il est déplacé ;
- modifier les tags du répertoire ne modifie pas automatiquement les célébrations existantes ;
- modifier un gabarit ne modifie pas automatiquement les célébrations existantes.

## 50.3. Réinitialisation explicite

Les opérations destructives doivent être explicites.

Changer le gabarit d’une célébration provoque une véritable réinitialisation totale.

## 50.4. Source séparée du contenu édité

Les données AELF sources sont conservées séparément du texte final éditable.

## 50.5. Répertoire comme aide, pas comme dépendance historique

Le répertoire du groupe détermine principalement ce qui est sélectionnable aujourd’hui.

Il ne doit pas casser rétroactivement les célébrations anciennes.

## 50.6. Gabarits par tags

Les gabarits chants utilisent des tags et non des chants précis.

Les shortlists peuvent donc évoluer sans modifier les gabarits.

## 50.7. Validation simple

La validation détecte uniquement les blocs obligatoires laissés vides.

Elle n’essaie pas de juger la qualité du contenu.

---

# 51. Précisions prioritaires intégrées

Les points suivants doivent être considérés comme prioritaires dans cette SFD consolidée.

## 51.1. Balises

La balise de section n’est pas un conteneur.

Elle se déplace seule et sa suppression ne touche aucun autre bloc.

## 51.2. Cache AELF

Le fonctionnement cible n’est pas un appel AELF bloc par bloc.

Le cache AELF est partagé au niveau de la célébration.

## 51.3. Texte AELF

Le texte source AELF est en lecture seule.

Le texte final du bloc est totalement modifiable et indépendant.

## 51.4. Refresh AELF

Un refresh ne met jamais à jour automatiquement les textes finaux déjà importés.

## 51.5. Coches de couplets

Les coches sont calculées :

- lors de l’ajout d’un nouveau chant ;
- lors d’une réinitialisation totale.

Elles ne sont pas recalculées silencieusement lors des modifications ordinaires.

## 51.6. Type secondaire

Le type secondaire sert uniquement à la recherche et au classement des chants.

Seul le type principal influence la présélection des couplets.

## 51.7. Autocomplétion

L’autocomplétion et la réinitialisation totale sont deux opérations différentes.

Une autocomplétion ne signifie pas automatiquement une remise à zéro de toutes les coches des couplets.

---

# 52. Points encore à spécifier

Les sujets suivants restent volontairement ouverts pour la suite de la SFD :

1. règles de génération automatique des célébrations sur plusieurs mois ;
2. association entre calendrier liturgique et gabarits ;
3. gestion des vigiles et cas liturgiques ambigus ;
4. liste complète des variables utilisables dans les gabarits d’impression et les feuilles ;
5. rendu et règles avancées de génération PDF ;
6. éventuel partage de gabarits entre groupes ;
7. détail de la gestion des groupes jumelés ;
8. schéma exact du cache AELF ;
9. stratégie technique de résolution robuste d’une cible AELF ;
10. liste exhaustive des types de textes AELF ;
11. liste exhaustive des variables AELF ;
12. liste exhaustive des variables générales ;
13. syntaxe finale et parser du mini-Markdown ;
14. UX exacte du sélecteur de chants à trois onglets ;
15. UX exacte des alertes de réinitialisation ;
16. représentation visuelle d’une référence LSS cassée ;
17. stratégie exacte utilisée par l’autocomplétion lorsqu’il existe plusieurs chants candidats.

Les sujets suivants étaient volontairement ouverts dans le document initial et sont désormais précisés dans cette SFD consolidée :

1. structure détaillée du déroulé ;
2. comportement précis des blocs chants ;
3. comportement précis des blocs textes ;
4. ordre, ajout, suppression et déplacement des blocs ;
5. intégration des textes AELF ;
6. choix et remplacement des textes liturgiques ;
7. gestion des chants et de leurs couplets dans une célébration ;
8. comportement détaillé d’un gabarit de célébration appliqué à un déroulé existant.
