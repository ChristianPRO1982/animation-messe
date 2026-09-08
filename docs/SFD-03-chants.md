# SFD-03-chants

## 1. Objet

Cette spécification décrit la gestion fonctionnelle des **chants dans Animation Messe (AM)**.

Le principe général repose sur une séparation claire entre :

- **Lyrics Slide Show (LSS)**, qui porte le référentiel officiel des chants ;
- **Animation Messe (AM)**, qui enrichit ces chants pour les besoins propres d'un groupe et de la préparation liturgique.

La règle structurante est :

> **LSS possède le contenu du chant.  
> AM possède la manière dont un groupe utilise ce chant.**

AM ne devient jamais propriétaire du titre, de la description ou du texte d'un chant.

---

## 2. Périmètre

Cette SFD couvre :

- la consultation des chants provenant de LSS ;
- la gestion du recueil d'un groupe ;
- l'accès aux chants hors recueil via l'espace d'échange ;
- l'utilisation des tags communs ;
- l'utilisation des tags propres au groupe ;
- la copie structurelle d'un chant dans AM lors de son ajout au recueil ;
- la qualification d'un chant et de ses blocs par les tags du groupe ;
- la sélection par défaut des blocs d'un chant selon un tag ;
- la surcharge de cette sélection dans une messe ;
- la synchronisation fonctionnelle entre LSS et AM ;
- les règles de suppression.

Cette SFD ne décrit pas :

- l'édition des textes des chants ;
- l'éditeur LSS ;
- la projection des chants ;
- les partitions, audios ou liens associés ;
- le planning des animateurs et musiciens ;
- les permissions générales d'édition d'une animation ;
- le mécanisme technique de synchronisation entre les applications.

---

# 3. Responsabilités de LSS

LSS est la source de vérité des données intrinsèques d'un chant.

LSS porte notamment :

- l'identifiant du chant ;
- le titre ;
- la description ;
- la structure officielle du chant ;
- les identifiants des blocs ;
- le type de chaque bloc :
  - refrain ;
  - couplet ;
  - pont ;
  - pré-refrain ;
  - refrain final ;
  - autres types supportés par LSS ;
- l'ordre des blocs ;
- le texte de chaque bloc ;
- les métadonnées générales du chant ;
- les **tags communs**.

Les textes restent toujours lus depuis LSS.

**R-LSS-001** — AM ne copie jamais le texte d'un chant.

**R-LSS-002** — AM ne copie jamais comme donnée métier officielle le titre ou la description d'un chant.

**R-LSS-003** — Toute modification d'un texte dans LSS est automatiquement visible dans AM lors de la lecture du chant.

---

# 4. Tags communs

Les tags communs appartiennent au référentiel général de LSS.

Ils sont utilisables indépendamment d'AM et d'un groupe particulier.

Ils correspondent à des classifications suffisamment génériques pour être pertinentes pour différents recueils, groupes, associations ou confessions.

Ils peuvent par exemple qualifier :

- un style ;
- un type de chant ;
- une période ;
- un usage musical général ;
- toute autre classification commune.

Ils ne sont pas destinés à représenter finement le déroulement d'une messe catholique.

**R-TAG-COM-001** — Un tag commun n'appartient à aucun groupe.

**R-TAG-COM-002** — Tous les groupes voient le même référentiel de tags communs.

**R-TAG-COM-003** — Les tags communs restent visibles même pour les utilisateurs qui ne travaillent pas dans AM.

---

# 5. Tags de groupe

AM ajoute un second niveau de classification : les **tags de groupe**.

Ils servent à exprimer la manière dont un groupe donné utilise un chant.

Ils sont particulièrement adaptés aux moments liturgiques.

Exemples :

- Entrée ;
- Kyrie ;
- Gloria ;
- Psaume ;
- Alléluia ;
- Offertoire ;
- Sanctus ;
- Anamnèse ;
- Agnus ;
- Communion ;
- Action de grâce ;
- Envoi.

Ces tags sont propres au groupe.

**R-TAG-GRP-001** — Les tags de groupe sont créés et administrés dans le contexte AM.

**R-TAG-GRP-002** — Un tag de groupe appartient à un seul groupe.

**R-TAG-GRP-003** — Deux groupes peuvent posséder chacun un tag ayant exactement le même nom sans qu'il s'agisse du même objet fonctionnel.

---

# 6. Présentation commune des tags entre LSS et AM

Les tags communs et les tags de groupe appartiennent à deux niveaux de responsabilité différents, mais ils doivent rester utilisables dans un fonctionnement cohérent entre LSS et AM.

L'objectif est que les recherches et filtres fonctionnent de manière similaire dans les deux applications.

La différence principale porte sur :

- le contexte ;
- la priorité d'affichage.

---

## 6.1 Affichage dans LSS

Dans LSS, les tags communs sont prioritaires.

Ordre d'affichage :

1. tags communs ;
2. tags du groupe actuellement sélectionné.

Un utilisateur non connecté ou sans groupe sélectionné voit uniquement les tags communs.

Un utilisateur connecté peut sélectionner un groupe auquel il appartient afin d'accéder en complément aux tags propres à ce groupe.

**R-LSS-TAG-001** — LSS ne mélange jamais simultanément les tags de plusieurs groupes.

Si un utilisateur appartient à plusieurs groupes, il doit choisir le groupe actif.

Cela évite :

- les doublons ;
- les homonymes ;
- les listes trop longues ;
- les ambiguïtés sur l'origine du tag.

---

## 6.2 Affichage dans AM

Dans AM, le contexte du groupe est central.

L'ordre est donc inversé :

1. tags du groupe ;
2. tags communs.

**R-AM-TAG-001** — Toutes les fonctions de recherche et de filtrage dans AM travaillent dans le contexte d'un groupe actif.

**R-AM-TAG-002** — Les tags des autres groupes de l'utilisateur ne doivent pas apparaître simultanément.

La différence d'ordre entre LSS et AM reflète simplement leur usage principal :

- LSS est d'abord un catalogue musical général ;
- AM est d'abord un outil d'organisation propre au groupe.

---

# 7. Recueil d'un groupe

Tous les chants présents dans LSS ne font pas nécessairement partie du recueil d'un groupe.

Le recueil représente le sous-ensemble de chants réellement utilisés ou sélectionnés par le groupe.

Il permet :

- de limiter la taille du catalogue courant ;
- de rendre les recherches plus pertinentes ;
- d'associer les chants aux tags propres au groupe ;
- de préparer plus rapidement une messe.

Le fonctionnement normal privilégie le recueil du groupe.

---

# 8. Espace d'échange

Les chants disponibles dans LSS mais absents du recueil du groupe restent accessibles via un **espace d'échange**.

Cet espace permet de découvrir des chants supplémentaires et de compléter le recueil du groupe.

La distinction entre recueil et espace d'échange ne crée pas deux chants différents.

Il s'agit toujours du même chant LSS.

**R-REC-001** — Un chant ne doit jamais être dupliqué fonctionnellement entre le recueil et l'espace d'échange.

---

# 9. Ajout d'un chant au recueil

Lorsqu'un chant LSS est ajouté au recueil d'un groupe, AM crée une représentation structurelle de ce chant.

Cette représentation ne contient jamais le contenu éditorial du chant.

AM conserve notamment :

- l'identifiant LSS du chant ;
- la liste des identifiants de tous les blocs du chant ;
- l'ordre de ces blocs ;
- les informations structurelles nécessaires pour maintenir le parallèle avec LSS ;
- les données spécifiques au groupe associées à ces références.

Exemple :

## LSS

```text
Chant 123
 ├── bloc 451
 ├── bloc 452
 ├── bloc 453
 └── bloc 454
```

## AM

```text
Recueil du groupe
└── référence chant 123
    ├── référence bloc 451
    ├── référence bloc 452
    ├── référence bloc 453
    └── référence bloc 454
```

AM ne copie pas :

- le titre ;
- la description ;
- le texte des blocs.

---

# 10. Pourquoi copier la structure

Un simple lien vers le chant LSS ne suffit pas.

AM doit pouvoir enrichir chaque bloc avec des informations propres au groupe.

En particulier :

- les tags du groupe ;
- la sélection par défaut d'un bloc pour chacun de ces tags ;
- d'autres paramètres éventuels propres à AM.

La structure AM reste donc un parallèle des identifiants LSS, jamais une copie du contenu.

---

# 11. Ordre des blocs

L'ordre officiel du chant est porté par LSS.

AM conserve cet ordre dans sa représentation structurelle.

**R-STRUCT-001** — La structure fondamentale du chant reste celle de LSS.

Si, dans une messe particulière, l'utilisateur choisit certains blocs ou les utilise dans un ordre spécifique, cela relève de l'occurrence de la messe et non d'une modification du chant dans le recueil.

---

# 12. Association d'un chant aux tags du groupe

Un chant du recueil peut recevoir plusieurs tags du groupe.

Exemple :

> Chant : Messe de Saint-Paul  
> Tags :
>
> - Kyrie
> - Sanctus
> - Agnus

Cette qualification permet de retrouver le même chant à plusieurs moments de la messe.

**R-TAG-CHANT-001** — Un chant peut posséder zéro, un ou plusieurs tags du groupe.

---

# 13. Association des tags aux blocs du chant

L'association d'un tag au chant ne suffit pas.

Pour chaque bloc du chant, AM doit pouvoir savoir si ce bloc doit être sélectionné par défaut lorsque le chant est utilisé avec un tag donné.

La donnée fonctionnelle est donc :

> **bloc LSS × tag du groupe → booléen**

Exemple :

| Bloc LSS | Kyrie | Sanctus | Agnus |
|---|---:|---:|---:|
| 451 — Kyrie | TRUE | FALSE | FALSE |
| 452 — Sanctus | FALSE | TRUE | FALSE |
| 453 — Agnus 1 | FALSE | FALSE | TRUE |
| 454 — Agnus 2 | FALSE | FALSE | TRUE |

Le même bloc peut donc avoir un comportement différent selon le tag.

**R-TAG-BLOC-001** — Le booléen est porté par le couple `(tag du groupe, bloc du chant)`.

---

# 14. Valeur par défaut

Lorsqu'un tag est ajouté à un chant, les blocs du chant sont par défaut actifs pour ce tag.

Le booléen est donc initialisé à `TRUE`.

Le groupe peut ensuite désactiver les blocs qui ne doivent généralement pas être proposés pour cet usage.

Exemple :

| Bloc | Communion |
|---|---:|
| Refrain | TRUE |
| Couplet 1 | TRUE |
| Couplet 2 | TRUE |
| Couplet 3 | FALSE |
| Couplet 4 | TRUE |
| Couplet 5 | FALSE |
| Couplet 6 | TRUE |
| Couplet 7 | FALSE |
| Couplet 8 | FALSE |

`FALSE` signifie :

> ne pas sélectionner ce bloc par défaut pour ce tag.

Il ne signifie jamais que le bloc est interdit.

---

# 15. Utilisation d'un chant dans une messe

Un bloc chant d'une animation peut correspondre à un moment liturgique donné.

Exemple :

> Bloc : Communion  
> Tag attendu : Communion

AM recherche alors prioritairement les chants du recueil portant ce tag.

Le système doit néanmoins permettre d'élargir la recherche si nécessaire.

Le tag constitue donc une aide à la sélection, pas un verrou.

**R-MESSE-001** — Un chant sans le tag correspondant doit rester sélectionnable manuellement.

---

# 16. Sélection initiale des blocs

Lorsqu'un chant est choisi pour un bloc de messe portant le tag `T`, AM utilise la configuration du groupe pour ce tag.

La sélection initiale contient tous les blocs dont la valeur est `TRUE`.

Exemple :

Configuration du groupe :

- refrain : TRUE ;
- couplet 1 : TRUE ;
- couplet 2 : FALSE ;
- couplet 3 : TRUE.

Sélection initiale :

- refrain ;
- couplet 1 ;
- couplet 3.

---

# 17. Surcharge dans une messe

La configuration du recueil n'est qu'une valeur par défaut.

Pour une messe précise, le préparateur peut :

- ajouter un bloc initialement à `FALSE` ;
- retirer un bloc initialement à `TRUE`.

Exemple :

Configuration du groupe :

- refrain ;
- couplet 1 ;
- couplet 3.

Pour une messe particulière, le préparateur peut finalement choisir :

- refrain ;
- couplet 1 ;
- couplet 2.

Cette surcharge est locale à l'occurrence de la messe.

**R-MESSE-002** — Une surcharge dans une messe ne modifie jamais :

- LSS ;
- le recueil du groupe ;
- la configuration générale des tags ;
- les autres messes.

---

# 18. Chant utilisable à plusieurs moments liturgiques

Le même chant LSS peut être utilisé plusieurs fois dans une même messe.

Exemple :

> Chant 123  
> Tags :
>
> - Kyrie
> - Sanctus
> - Agnus

La messe peut contenir :

```text
Kyrie
→ chant 123
→ blocs configurés pour Kyrie

Sanctus
→ chant 123
→ blocs configurés pour Sanctus

Agnus
→ chant 123
→ blocs configurés pour Agnus
```

Il s'agit toujours du même chant LSS.

Les occurrences sont indépendantes.

**R-MULTI-001** — AM ne doit pas imposer l'unicité d'un chant dans une messe.

**R-MULTI-002** — Chaque occurrence peut utiliser une sélection de blocs différente.

---

# 19. Cas d'un chant avec beaucoup de couplets

Un chant peut comporter de nombreux couplets dont certains sont rarement utilisés ou peu appréciés par le groupe.

Le groupe peut alors les désactiver par défaut pour un tag.

Exemple :

| Bloc | Communion |
|---|---:|
| Refrain | TRUE |
| Couplet 1 | TRUE |
| Couplet 2 | TRUE |
| Couplet 3 | FALSE |
| Couplet 4 | TRUE |
| Couplet 5 | FALSE |
| Couplet 6 | TRUE |

Lors de la préparation d'une messe, seuls les blocs actifs sont proposés par défaut.

Les autres restent accessibles par surcharge.

---

# 20. Synchronisation structurelle entre LSS et AM

La copie structurelle impose de maintenir un parallèle entre les deux applications.

AM peut connaître par exemple :

```text
451
452
453
454
```

alors que le chant évolue ensuite dans LSS.

Trois cas doivent être distingués.

---

## 20.1 Modification du contenu d'un bloc

Exemple :

Le texte du bloc `452` est corrigé dans LSS.

Aucune synchronisation structurelle particulière n'est nécessaire.

AM conserve la référence au bloc `452` et lit simplement son contenu actuel.

**R-SYNC-001** — Une modification de texte dans LSS est automatiquement visible dans AM.

---

## 20.2 Suppression d'un bloc

Exemple :

LSS passe de :

```text
451
452
453
454
```

à :

```text
451
452
454
```

Le bloc `453` a été supprimé.

AM n'a aucune raison de conserver une référence vers un objet inexistant puisque son texte n'est pas copié.

La référence au bloc supprimé ainsi que les données AM qui en dépendent doivent disparaître.

**R-SYNC-002** — La suppression d'un bloc LSS entraîne la suppression de sa référence dans AM et des associations qui dépendent directement de ce bloc.

Cette perte est assumée.

---

## 20.3 Ajout d'un bloc

C'est le cas le plus délicat.

Exemple :

LSS passe de :

```text
451
452
453
454
```

à :

```text
451
452
455
453
454
```

AM doit :

1. détecter l'apparition du nouveau bloc `455` ;
2. l'ajouter à sa représentation structurelle ;
3. respecter son ordre dans le chant ;
4. déterminer son comportement vis-à-vis des tags du groupe existants.

Les trois premiers points sont déterministes.

Le quatrième ne l'est pas toujours.

AM sait qu'un nouveau bloc existe, mais ne sait pas forcément à quels usages liturgiques du groupe il correspond.

**R-SYNC-003** — La politique exacte de qualification d'un nouveau bloc vis-à-vis des tags existants reste un point fonctionnel à préciser lors de l'implémentation.

Il ne faut pas supposer automatiquement que le nouveau bloc doit être actif pour tous les tags existants.

---

# 21. Détection d'une désynchronisation

AM doit pouvoir déterminer si sa copie structurelle correspond encore à la structure actuelle de LSS.

La comparaison peut conceptuellement porter sur :

- l'identifiant du chant ;
- la liste ordonnée des identifiants de blocs.

Exemple :

### LSS

```text
451, 452, 455, 453, 454
```

### AM

```text
451, 452, 453, 454
```

La différence indique qu'un rafraîchissement est nécessaire.

Les textes n'ont pas besoin d'être comparés.

---

# 22. Rafraîchissement structurel

Un mécanisme de rafraîchissement devra permettre de remettre AM en adéquation avec LSS.

Il devra au minimum pouvoir :

- ajouter les nouvelles références ;
- supprimer les références devenues inexistantes ;
- prendre en compte les changements d'ordre ;
- conserver les tags et paramètres déjà réalisés pour les blocs qui existent toujours.

**R-SYNC-004** — Une resynchronisation ne doit pas reconstruire inutilement la configuration du groupe lorsque les identifiants LSS permettent de conserver les associations existantes.

Le mécanisme technique exact n'est pas défini dans cette SFD.

---

# 23. Identité d'un bloc

L'identifiant LSS du bloc constitue le lien stable entre les deux applications.

La synchronisation ne doit pas dépendre principalement :

- du numéro du couplet ;
- du texte ;
- d'un titre local ;
- de sa position seule.

Ces éléments peuvent évoluer.

**R-STRUCT-002** — L'identifiant LSS du bloc constitue la référence principale utilisée par AM.

---

# 24. Suppression d'un chant de LSS

La suppression d'un chant dans LSS est une suppression réelle de la donnée source.

Le chant n'existe alors plus fonctionnellement pour AM.

Comme AM ne copie jamais son contenu, conserver des références orphelines ne présente pas d'intérêt fonctionnel.

La suppression peut donc être propagée en cascade.

**R-DEL-001** — La suppression d'un chant dans LSS entraîne la suppression de ses références dans AM.

Cela peut notamment supprimer :

- sa présence dans les recueils ;
- sa structure copiée ;
- les références à ses blocs ;
- les tags de groupe associés ;
- les configurations TRUE/FALSE ;
- les utilisations dépendantes dans les animations.

La perte de données historiques résultante est assumée.

AM ne garantit donc pas qu'une ancienne animation reste intégralement exploitable si le chant source a été supprimé de LSS.

---

# 25. Retrait d'un chant du recueil d'un groupe

Le retrait d'un chant du recueil d'un groupe est différent de sa suppression dans LSS.

Le chant continue d'exister dans LSS.

Il reste donc potentiellement disponible dans l'espace d'échange.

En revanche, sa représentation propre au groupe dans le recueil n'a plus vocation à être conservée.

**R-DEL-002** — Retirer un chant du recueil supprime les enrichissements propres à ce recueil, sans supprimer le chant source dans LSS.

---

# 26. Suppression d'un tag de groupe

La suppression d'un tag de groupe ne supprime jamais les chants qui le portaient.

Elle supprime uniquement ce qui dépend directement du tag.

Cela comprend notamment :

- les associations entre le tag et les chants ;
- les associations entre le tag et les blocs ;
- les booléens TRUE/FALSE correspondants ;
- les autres réglages AM directement attachés à ce tag.

Le chant reste dans le recueil.

Exemple :

Un chant possède uniquement le tag `Communion`.

Si `Communion` est supprimé :

- le chant reste dans le recueil ;
- il n'est plus qualifié comme chant de communion ;
- AM ne sait plus pour quel usage liturgique le groupe l'avait classé.

Cette perte de qualification est définitive et assumée.

**R-DEL-003** — La suppression d'un tag de groupe supprime en cascade toutes les associations et configurations dépendant de ce tag, mais jamais les chants eux-mêmes.

---

# 27. Distinction entre les niveaux de suppression

Les règles de suppression doivent rester simples et cohérentes.

## Suppression d'un chant dans LSS

> disparition de l'objet source et suppression en cascade de ses dépendances AM.

## Retrait d'un chant du recueil

> disparition de l'enrichissement propre au groupe, mais conservation du chant LSS.

## Suppression d'un bloc dans LSS

> disparition de la référence structurelle AM correspondante et de ses dépendances.

## Suppression d'un tag de groupe

> disparition de la qualification et de ses paramètres, mais conservation du chant.

---

# 28. Provenance des tags dans l'interface

Comme les tags communs et les tags de groupe peuvent apparaître dans les mêmes écrans de recherche, leur provenance doit rester compréhensible pour l'utilisateur.

L'interface devra permettre de distinguer clairement :

- les tags communs ;
- les tags propres au groupe actif.

La forme visuelle exacte n'est pas définie à ce stade.

---

# 29. Principe architectural fonctionnel

Le modèle général peut être résumé ainsi :

```text
LSS
│
├── Chant
│   ├── titre
│   ├── description
│   ├── tags communs
│   └── structure officielle
│       ├── bloc ID 1 → texte
│       ├── bloc ID 2 → texte
│       └── bloc ID 3 → texte
│
└──────────── références ──────────────┐
                                       │
AM                                     │
│                                      │
└── Groupe                             │
    └── Recueil                        │
        └── Chant LSS ─────────────────┘
            ├── référence bloc ID 1
            │   └── tags du groupe + paramètres
            ├── référence bloc ID 2
            │   └── tags du groupe + paramètres
            └── référence bloc ID 3
                └── tags du groupe + paramètres
```

La frontière fonctionnelle doit rester stricte :

> **AM peut enrichir une référence LSS, mais ne devient jamais la source du contenu musical.**

---

# 30. Synthèse des responsabilités

| Donnée | LSS | AM |
|---|:---:|:---:|
| Identité du chant | ✅ | référence |
| Titre | ✅ | lecture |
| Description | ✅ | lecture |
| Texte des blocs | ✅ | lecture |
| Structure officielle | ✅ | copie des références |
| Identifiants des blocs | ✅ | référence |
| Ordre officiel des blocs | ✅ | copie structurelle |
| Tags communs | ✅ | lecture / utilisation |
| Tags du groupe | | ✅ |
| Association tag groupe ↔ chant | | ✅ |
| Association tag groupe ↔ bloc | | ✅ |
| TRUE/FALSE par tag et bloc | | ✅ |
| Sélection propre à une messe | | ✅ |
| Contenu textuel de la feuille de messe | source | exploitation |

---

# 31. Règles fonctionnelles essentielles

**R-01** — LSS est la source de vérité des chants.

**R-02** — AM ne copie jamais les textes, titres ou descriptions comme contenu métier officiel.

**R-03** — AM copie uniquement la structure nécessaire au fonctionnement du recueil.

**R-04** — Cette structure est basée sur les identifiants LSS des blocs.

**R-05** — Les tags communs sont gérés par LSS et visibles pour tous les groupes.

**R-06** — Les tags de groupe sont gérés dans AM.

**R-07** — Dans LSS, les tags communs sont affichés avant les tags du groupe actif.

**R-08** — Dans AM, les tags du groupe actif sont affichés avant les tags communs.

**R-09** — Les tags de plusieurs groupes ne sont jamais mélangés dans un même contexte.

**R-10** — Un chant peut posséder plusieurs tags du groupe.

**R-11** — Un bloc possède un booléen distinct pour chaque tag du groupe appliqué au chant.

**R-12** — Lors de l'ajout d'un tag à un chant, les blocs sont par défaut à TRUE.

**R-13** — FALSE signifie « non sélectionné par défaut », jamais « interdit ».

**R-14** — Un même chant peut être utilisé plusieurs fois dans une messe.

**R-15** — Chaque occurrence dans une messe peut avoir sa propre sélection de blocs.

**R-16** — Les surcharges effectuées dans une messe ne modifient jamais le recueil.

**R-17** — Une modification de texte dans LSS est automatiquement visible dans AM.

**R-18** — La suppression d'un bloc LSS supprime sa référence et ses dépendances AM.

**R-19** — L'ajout d'un bloc LSS doit être détecté et synchronisé.

**R-20** — La qualification automatique d'un nouveau bloc vis-à-vis des tags existants reste un point à préciser.

**R-21** — La suppression d'un chant LSS entraîne la suppression en cascade de ses dépendances AM.

**R-22** — Retirer un chant du recueil ne supprime jamais le chant LSS.

**R-23** — Supprimer un tag de groupe supprime ses associations et paramètres, mais jamais les chants concernés.

**R-24** — La perte historique liée à une suppression réelle de la donnée source est assumée.

---

# 32. Points volontairement laissés ouverts

Le projet étant encore au début et aucune implémentation n'étant figée, certains détails restent volontairement ouverts :

- mécanisme technique de synchronisation entre LSS et AM ;
- fréquence ou déclencheur des rafraîchissements ;
- traitement exact des nouveaux blocs ajoutés dans LSS ;
- éventuel indicateur de « bloc nouvellement ajouté à qualifier » ;
- présentation graphique des tags communs et des tags de groupe ;
- stratégie de recherche précise entre recueil et espace d'échange ;
- comportement détaillé des anciennes animations après suppression d'une donnée source.

Ces points pourront être précisés lorsque les modèles et premiers usages réels du projet existeront.

---

# 33. Principe final

Le fonctionnement global peut être résumé ainsi :

> **LSS définit ce qu'est le chant.  
> AM définit comment un groupe l'utilise.  
> Une messe définit ce qui sera réellement utilisé cette fois-ci.**

Cette séparation permet :

- de conserver une source unique pour les textes ;
- d'éviter les duplications ;
- de permettre à chaque groupe d'avoir son propre classement ;
- de garder des recherches cohérentes entre LSS et AM ;
- de gérer finement les moments liturgiques ;
- de conserver une architecture fonctionnelle suffisamment simple pour rester robuste et maintenable.
