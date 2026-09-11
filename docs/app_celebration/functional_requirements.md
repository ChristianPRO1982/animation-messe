# app_celebration — Functional Requirements

`app_celebration` porte l’objet métier central d’Animation Messe : la célébration.

Sources fonctionnelles principales :

- `docs/SFD-04-celebrations.md`
- `docs/SFD-03-chants.md`
- `docs/SFD-01-groupes_et_membres.md`
- `docs/app_group/models.md`

---

# Note de consolidation V1

`app_group` fournit les groupes, membres, fonctions, lieux habituels, tags de groupe et paramètres durables.

`app_celebration` possède les célébrations réelles, leurs participants effectifs, leurs fonctions réellement exercées, les cellules persistantes vues par le planning, les validations, les gabarits, le déroulé, les feuilles et les caches AELF.

Les gabarits de célébration et les gabarits d’impression ne doivent pas être déplacés dans `app_group`.

---

# 1. Rôle fonctionnel

`app_celebration` est responsable :

- des célébrations ;
- des gabarits de célébration ;
- du déroulé ;
- des blocs chants ;
- des blocs textes ;
- des balises de section ;
- des dates de célébration et dates AELF ;
- du cache AELF local à une célébration ;
- de la validation/verrouillage du déroulé ;
- de l’archivage ;
- des célébrations partagées entre groupes ;
- des cellules persistantes vues par le planning ;
- des gabarits d’impression ;
- des feuilles de messe.

`app_celebration` ne possède pas :

- les rôles de groupe ;
- le recueil de chants du groupe ;
- les textes sources LSS ;
- les paramètres durables de planning ;
- l’identité externe des utilisateurs.

---

# 2. Célébration

La célébration est l’objet métier canonique.

Une ligne de planning correspond à une célébration existante.

Une célébration possède au minimum :

- une date ;
- une heure ;
- un lieu ;
- un titre ;
- au moins un groupe de rattachement ;
- un groupe créateur lorsque la célébration est partagée.

Pour chaque groupe participant, la combinaison `groupe + date + heure + lieu` doit rester unique.

Le lieu est un champ texte libre, éventuellement aidé par les lieux habituels du groupe.

---

# 3. Déroulé

Le déroulé d’une célébration est une liste plate ordonnée.

Les éléments possibles sont :

- bloc chant ;
- bloc texte ;
- balise de section.

Une balise structure l’affichage, mais n’est jamais un conteneur.

Déplacer ou supprimer une balise ne déplace ni ne supprime les blocs qui la suivent.

Changer le gabarit d’une célébration existante provoque une réinitialisation totale explicite du déroulé.

---

# 4. Blocs chants

Un bloc chant réel référence :

- un chant LSS existant ;
- ou une référence historique cassée si le chant source a été supprimé.

Le sélecteur normal propose uniquement les chants du recueil du groupe.

Un chant LSS absent du recueil peut être rapatrié par une action explicite.

Les blocs chants utilisent :

- un type principal obligatoire ;
- un type secondaire facultatif ;
- les tags de groupe pour classer les propositions ;
- les couplets cochés propres au bloc.

Seul le type principal sert à calculer les couplets cochés par défaut.

Après initialisation, les coches appartiennent au bloc de célébration et ne sont pas recalculées silencieusement.

---

# 5. Blocs textes et AELF

Un bloc texte peut être :

- texte libre ;
- texte AELF.

La date de célébration et la date AELF sont distinctes.

Les données AELF sont récupérées puis stockées dans un cache au niveau de la célébration.

Le cache AELF est une donnée source en lecture seule.

Le texte final du bloc est indépendant :

- il peut être initialisé depuis AELF ;
- il peut ensuite être modifié librement ;
- il n’est pas mis à jour automatiquement par un refresh AELF.

---

# 6. Validation, archivage et feuilles

La validation de célébration verrouille le déroulé.

Elle est distincte de la validation du planning.

Seuls les Responsables du groupe responsable peuvent valider ou dévalider.

Pour une célébration partagée, seuls les Responsables du groupe créateur peuvent valider ou dévalider.

Une célébration dont la date est passée devient définitivement non modifiable.

La validation déclenche la génération des feuilles de messe.

Les feuilles :

- sont générées depuis les gabarits d’impression du groupe créateur ;
- deviennent autonomes après génération ;
- suivent le cycle de vie de leur célébration ;
- sont supprimées lors d’une dévalidation future ;
- sont protégées par l’archivage de la célébration.

---

# 7. Règles fonctionnelles

**CELEBRATION-ID-01** — La célébration est l’objet métier central d’AM.

**CELEBRATION-ID-02** — Une ligne de planning correspond à une célébration.

**CELEBRATION-ID-03** — `groupe + date + heure + lieu` est unique pour chaque groupe participant.

**CELEBRATION-TEMPLATE-01** — Un gabarit de célébration prépare une structure de déroulé.

**CELEBRATION-TEMPLATE-02** — Changer le gabarit d’une célébration réinitialise explicitement tout le déroulé.

**CELEBRATION-FLOW-01** — Le déroulé est une liste plate ordonnée.

**CELEBRATION-FLOW-02** — Une balise de section n’est pas un conteneur.

**CELEBRATION-SONG-01** — Un bloc chant peut conserver une référence historique cassée.

**CELEBRATION-SONG-02** — Les coches de couplets appartiennent au bloc de célébration.

**CELEBRATION-AELF-01** — Les données AELF sont mises en cache au niveau de la célébration.

**CELEBRATION-AELF-02** — Le texte final AELF est indépendant de la source AELF.

**CELEBRATION-VAL-01** — La validation de célébration verrouille le déroulé.

**CELEBRATION-VAL-02** — La validation de célébration déclenche les feuilles de messe.

**CELEBRATION-SHARE-01** — Le groupe créateur porte la responsabilité d’une célébration partagée.

**CELEBRATION-ARCH-01** — Une célébration archivée est protégée de la suppression et de la purge.

**CELEBRATION-RGPD-01** — L’archivage ne bloque pas la purge RGPD des affectations nominatives.

---

# 8. Points encore à spécifier

1. schéma exact du cache AELF ;
2. stratégie technique de résolution d’une cible AELF ;
3. liste finale des variables utilisables dans les blocs textes et feuilles ;
4. rendu PDF détaillé ;
5. UX exacte du sélecteur de chants et des références cassées ;
6. règles de génération automatique des célébrations sur plusieurs mois ;
7. association entre calendrier liturgique et gabarits.
