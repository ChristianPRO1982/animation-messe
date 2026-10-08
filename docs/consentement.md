# Gestion de l'information RGPD et de l'acceptation des règles d'Animation Messe

> **Statut du document : brouillon fonctionnel**
>
> Ce document décrit les règles d'accès à Animation Messe (AM), l'information des internautes et des utilisateurs connectés, ainsi que les mécanismes que l'application Django doit appliquer.
>
> Il ne constitue pas à lui seul la politique de confidentialité ni les mentions légales du site.

---

# 1. Principes généraux

Animation Messe distingue deux situations :

1. l'internaute qui utilise les parties publiques du site sans être connecté ;
2. l'utilisateur connecté qui souhaite accéder aux fonctionnalités privées d'Animation Messe.

L'accès aux fonctionnalités privées d'AM suppose :

- que l'utilisateur soit authentifié ;
- qu'il dispose d'un accès à au moins un groupe AM ;
- qu'il ait pris connaissance des conditions applicables à l'utilisation d'AM ;
- qu'il ait explicitement accepté les règles d'utilisation en vigueur.

L'acceptation des règles d'utilisation ne doit pas être confondue avec le **consentement RGPD** constituant une base légale pour un traitement de données.

Les traitements strictement nécessaires au fonctionnement d'AM doivent disposer de leur propre base légale.

Lorsqu'un traitement facultatif nécessite réellement le consentement de l'utilisateur, celui-ci doit être recueilli séparément.

---

# 2. Cas n°1 — Internaute non connecté

## 2.1 Accès

Un internaute non connecté peut accéder uniquement aux fonctionnalités et pages prévues comme publiques.

Il ne peut pas accéder :

- aux groupes ;
- au planning interne d'un groupe ;
- aux listes de membres ;
- aux préparations privées des célébrations ;
- aux paramètres du groupe ;
- aux fonctionnalités nécessitant une identification personnelle.

Les éventuelles fonctionnalités publiques prévues par AM restent accessibles selon leurs propres règles.

---

## 2.2 Information de l'internaute

Lors de son utilisation du site, une fenêtre d'information propre au site peut être affichée.

Cette fenêtre doit expliquer de manière synthétique :

- quelles données techniques sont utilisées ;
- pourquoi elles sont utilisées ;
- si des cookies ou stockages locaux sont employés ;
- si certains traitements sont strictement nécessaires au fonctionnement du site ;
- où consulter la politique de confidentialité complète ;
- comment exercer les droits relatifs aux données personnelles.

La popup doit rester courte.

Elle doit renvoyer vers une page permanente contenant l'information détaillée.

---

## 2.3 Mémorisation de l'affichage

AM mémorise localement la date à laquelle l'information a été affichée ou validée.

Pour un internaute non authentifié, cette information ne doit pas nécessiter la création d'un compte ni l'identification de la personne.

Elle peut être conservée dans un cookie fonctionnel ou un stockage équivalent lorsque cela est juridiquement et techniquement approprié.

### Règle AM

La fenêtre est réaffichée :

- après une absence de navigation sur le site pendant au moins **1 mois** ;
- dans tous les cas au plus tard **6 mois** après le dernier affichage nécessitant une nouvelle information.

La règle des six mois est une règle fonctionnelle retenue par AM et ne doit pas être présentée comme une durée universellement imposée par le RGPD.

---

# 3. Cas n°2 — Utilisateur connecté

## 3.1 Conditions permettant l'accès aux fonctions privées

Être authentifié ne suffit pas à donner accès aux fonctions privées d'Animation Messe.

Un utilisateur doit remplir simultanément les conditions suivantes :

1. être authentifié ;
2. avoir accès à au moins un groupe AM ;
3. avoir validé la version actuellement applicable des conditions d'utilisation d'AM.

À défaut, l'utilisateur reste limité aux fonctionnalités équivalentes à celles accessibles à un internaute non connecté.

---

# 4. Première entrée dans Animation Messe

Lorsqu'un utilisateur :

- est connecté ;
- possède au moins un groupe accessible ;
- accède pour la première fois à une partie privée d'AM ;

Django doit vérifier s'il existe une acceptation valide des conditions actuellement applicables.

Si aucune acceptation valide n'existe, la fenêtre d'information et d'acceptation est affichée avant l'accès aux données du groupe.

---

# 5. Fenêtre d'acceptation pour un utilisateur connecté

La popup doit expliquer de manière suffisamment claire les conséquences de l'utilisation d'Animation Messe.

Elle doit notamment indiquer que l'utilisation d'AM entraîne le traitement de certaines informations nécessaires au fonctionnement du service.

Elle doit comporter au minimum :

- un résumé des données utilisées ;
- les principales finalités ;
- une indication sur la visibilité de certaines informations auprès des autres membres du groupe ;
- les règles principales concernant le planning ;
- l'existence d'une politique de confidentialité complète ;
- l'existence de conditions d'utilisation complètes ;
- les modalités permettant d'exercer ses droits ;
- la version des conditions actuellement présentées.

---

# 6. Action demandée à l'utilisateur

L'utilisateur doit réaliser une action positive.

La popup comporte notamment une case non précochée du type :

> J'ai lu et compris les informations relatives au fonctionnement d'Animation Messe et au traitement de mes données.

Puis un bouton :

> **J'accepte et j'accède à Animation Messe**

Le bouton d'acceptation doit rester désactivé tant que la case obligatoire n'est pas cochée.

Une case précochée ne doit jamais être utilisée pour recueillir une acceptation ou un consentement.

---

# 7. Refus ou absence d'acceptation

L'utilisateur doit pouvoir fermer ou refuser la popup.

Dans ce cas :

- son compte reste valide ;
- son authentification reste valide ;
- son appartenance éventuelle aux groupes n'est pas supprimée ;
- ses données ne sont pas automatiquement effacées ;
- il ne peut cependant pas accéder aux fonctions privées d'AM.

Il dispose alors du même niveau d'accès qu'un internaute non connecté concernant AM.

Il doit toujours pouvoir accéder aux pages nécessaires pour :

- consulter les conditions d'utilisation ;
- consulter la politique de confidentialité ;
- consulter les mentions légales ;
- exercer ses droits ;
- se déconnecter.

Le refus d'accepter les conditions d'utilisation ne doit donc jamais provoquer une boucle de redirection empêchant l'accès à ces pages.

---

# 8. Acceptation enregistrée

Lorsqu'un utilisateur accepte les conditions, Django doit conserver une preuve minimale de cette acceptation.

Cette preuve peut notamment contenir :

- l'identifiant interne de l'utilisateur ;
- la version du document accepté ;
- la date et l'heure de l'acceptation ;
- éventuellement la langue dans laquelle les conditions ont été présentées ;
- éventuellement le mécanisme ayant servi à l'acceptation.

Il n'est pas nécessaire d'enregistrer plus de données techniques que nécessaire.

En particulier, la conservation systématique d'une adresse IP complète comme preuve ne doit pas être considérée comme obligatoire.

---

# 9. Versionnement des conditions

Les conditions applicables à AM doivent être versionnées.

Exemple :

`2026-10-01-v1`

Une acceptation doit toujours être associée à une version précise.

Il faut distinguer :

- une modification éditoriale sans conséquence pour l'utilisateur ;
- une modification substantielle des règles.

Une simple correction orthographique ou typographique ne doit pas obligatoirement provoquer une nouvelle acceptation.

Une modification substantielle peut rendre nécessaire une nouvelle acceptation.

Exemples :

- nouvelle catégorie importante de données traitées ;
- changement important concernant la visibilité des informations ;
- nouvelle fonctionnalité modifiant substantiellement l'utilisation des données ;
- évolution importante des responsabilités des membres ;
- évolution significative des conditions d'utilisation.

---

# 10. Réaffichage périodique

AM souhaite périodiquement rappeler aux utilisateurs les règles applicables.

La popup pourra donc être réaffichée :

- après une absence d'utilisation d'AM pendant au moins **1 mois** ;
- au maximum **6 mois** après la dernière présentation selon la règle produit retenue ;
- immédiatement lorsqu'une nouvelle version nécessitant une acceptation est publiée.

Il faut toutefois distinguer deux événements.

## 10.1 Rappel d'information

Le texte n'a pas substantiellement changé.

La popup sert principalement à rappeler les règles.

L'acceptation historique reste conservée.

## 10.2 Nouvelle acceptation obligatoire

Une version substantiellement nouvelle des conditions est publiée.

L'ancienne acceptation n'autorise alors plus l'accès privé.

L'utilisateur doit accepter la nouvelle version avant de poursuivre.

---

# 11. Droits obtenus après acceptation

Après acceptation, les droits réels de l'utilisateur restent déterminés par ses groupes et par ses rôles.

Le mécanisme d'acceptation ne donne aucun droit métier supplémentaire.

Il autorise seulement l'accès aux fonctionnalités auxquelles l'utilisateur possède déjà des droits.

Exemple :

un utilisateur accepté comme simple membre d'un groupe ne devient pas Responsable parce qu'il a accepté les conditions.

Les règles RBAC d'AM continuent donc à s'appliquer normalement.

---

# 12. Ce qu'un membre connecté doit comprendre

Avant d'utiliser AM, un membre doit notamment comprendre que certaines informations le concernant peuvent être utilisées dans le cadre du fonctionnement collectif du groupe.

Selon les fonctionnalités activées, cela peut concerner notamment :

- son identité ou nom d'affichage ;
- son appartenance au groupe ;
- ses rôles dans le groupe ;
- ses disponibilités ;
- ses indisponibilités ;
- ses affectations aux célébrations ;
- ses participations prévues ou passées ;
- certaines actions effectuées dans le groupe lorsque leur traçabilité est nécessaire.

Ces informations ne doivent être accessibles qu'aux personnes pour lesquelles elles sont nécessaires au fonctionnement du groupe.

---

# 13. Planning

L'utilisation du planning implique nécessairement que certaines informations soient partagées entre les membres concernés.

Par exemple, les membres autorisés peuvent avoir besoin de savoir :

- qu'une personne est disponible ;
- qu'elle est indisponible ;
- qu'elle est affectée à une célébration ;
- quel rôle elle y occupe.

AM doit privilégier le principe de minimisation.

Une personne doit pouvoir indiquer qu'elle est indisponible sans être obligée de fournir la raison personnelle de son indisponibilité.

Les commentaires libres contenant des informations privées doivent être évités sauf lorsqu'ils répondent à un besoin réel du service.

---

# 14. Données des autres membres

L'accès à AM peut donner accès à certaines données concernant d'autres personnes.

L'utilisateur doit être informé que ces informations sont fournies uniquement pour l'organisation du groupe.

Elles ne doivent pas être réutilisées pour une finalité étrangère au fonctionnement du groupe.

Par exemple, l'accès à une information dans AM ne signifie pas que celle-ci devient publiquement diffusable.

---

# 15. Cloisonnement par groupe

Une acceptation des règles d'AM est globale au compte utilisateur.

Il n'est pas nécessaire de faire accepter les mêmes conditions pour chaque groupe rejoint.

En revanche, l'acceptation globale ne doit jamais contourner les autorisations propres à chaque groupe.

L'appartenance à un groupe A ne doit donner aucune visibilité sur les données privées d'un groupe B.

---

# 16. Changement de groupe

Lorsqu'un utilisateur rejoint un nouveau groupe :

- aucune nouvelle acceptation générale n'est nécessaire si les conditions AM n'ont pas changé ;
- les droits sur ce groupe commencent uniquement lorsque les règles métier d'adhésion sont satisfaites ;
- l'utilisateur bénéficie uniquement des permissions correspondant à son statut dans ce groupe.

---

# 17. Perte du dernier groupe

Un utilisateur connecté peut ne plus appartenir à aucun groupe AM.

Dans ce cas :

- son compte n'est pas nécessairement supprimé ;
- son acceptation historique peut être conservée conformément aux règles de conservation ;
- les pages privées nécessitant un groupe deviennent inaccessibles.

Si l'utilisateur rejoint ultérieurement un nouveau groupe, Django vérifie à nouveau que l'acceptation correspondant à la version actuelle existe encore.

---

# 18. Suppression ou anonymisation du compte

L'acceptation des conditions ne doit pas empêcher l'application des mécanismes prévus par AM concernant :

- la suppression du compte ;
- la sortie d'un groupe ;
- la pseudonymisation ;
- l'anonymisation ;
- les durées de conservation.

Les données ne doivent pas être conservées indéfiniment simplement parce qu'elles ont été associées à une acceptation.

Les durées doivent être définies en fonction de la finalité des traitements concernés.

---

# 19. Consentements facultatifs

Si AM ajoute ultérieurement des traitements réellement facultatifs reposant sur le consentement, ceux-ci doivent être séparés de l'acceptation générale.

Exemples possibles :

- inscription à une newsletter ;
- statistiques facultatives non nécessaires au service ;
- partage de données avec un service tiers facultatif ;
- communication facultative à d'autres groupes.

Chaque finalité doit disposer de son propre choix lorsqu'un consentement distinct est nécessaire.

Le refus d'un traitement facultatif ne doit pas empêcher l'accès aux fonctionnalités principales d'AM lorsque ce traitement n'est pas nécessaire à leur fonctionnement.

---

# 20. Cookies et traceurs

Les cookies ou mécanismes équivalents strictement nécessaires au fonctionnement du site doivent être distingués des traceurs facultatifs.

Par exemple peuvent être nécessaires :

- session Django ;
- sécurité ;
- authentification ;
- protection CSRF ;
- mémorisation de certains paramètres nécessaires au service.

Les éventuels traceurs facultatifs doivent suivre leur propre mécanisme de consentement.

La popup relative aux règles d'utilisation d'AM ne doit donc pas servir à masquer un consentement global à tous les cookies.

---

# 21. Règles Django

Le contrôle doit être effectué côté serveur.

Il ne doit jamais reposer uniquement sur JavaScript ou sur l'affichage de la popup.

L'utilisateur ne doit pas pouvoir contourner le mécanisme en :

- appelant directement une URL ;
- désactivant JavaScript ;
- appelant directement une API ;
- utilisant une ancienne URL enregistrée ;
- modifiant localement un cookie d'interface.

---

# 22. Garde d'accès AM

Les vues privées d'AM doivent passer par un mécanisme commun de contrôle.

Conceptuellement :

`Authentifié → possède un groupe → conditions courantes acceptées → contrôle des permissions métier`

Il faut éviter de reproduire manuellement ce test dans chaque vue.

Le projet devra disposer d'un garde commun, par exemple au niveau :

- d'un middleware spécialisé ;
- d'un mixin ;
- d'un décorateur ;
- ou d'un service centralisé de contrôle d'accès.

Le choix technique pourra être fait lors de l'implémentation, mais la logique doit rester centralisée.

---

# 23. Pages exemptées du garde

Certaines URLs doivent rester accessibles même lorsqu'une acceptation manque.

Au minimum :

- accueil public ;
- authentification ;
- déconnexion ;
- page d'information RGPD ;
- politique de confidentialité ;
- conditions d'utilisation ;
- mentions légales ;
- page permettant l'acceptation ;
- fonctionnalités nécessaires à l'exercice des droits ;
- éventuelles pages publiques d'Animation Messe.

La liste doit être explicite afin d'éviter les boucles de redirection.

---

# 24. API et requêtes AJAX

Les mêmes règles s'appliquent aux endpoints techniques.

Une API privée ne doit pas renvoyer les données d'un groupe si les conditions d'accès ne sont pas remplies.

Elle doit retourner une réponse indiquant clairement que l'accès nécessite une acceptation actualisée.

L'interface JavaScript pourra ensuite transformer cette réponse en popup ou en redirection adaptée.

La sécurité reste néanmoins assurée côté serveur.

---

# 25. Modèle fonctionnel des acceptations

Le système doit permettre de déterminer au minimum :

- quelle version est actuellement active ;
- quelle version un utilisateur a acceptée ;
- quand il l'a acceptée ;
- si cette version permet encore l'accès ;
- si une nouvelle présentation est nécessaire.

Il est préférable de conserver l'historique des acceptations plutôt que d'écraser simplement une date dans la table utilisateur.

Conceptuellement :

**Version des conditions**

- identifiant ;
- version ;
- date d'entrée en vigueur ;
- indicateur `nouvelle_acceptation_obligatoire` ;
- document correspondant.

**Acceptation utilisateur**

- utilisateur ;
- version ;
- date d'acceptation.

Cette séparation permet de conserver une preuve claire de ce qui a été accepté.

---

# 26. Administration

L'administration AM doit permettre de connaître :

- la version actuellement applicable ;
- sa date d'entrée en vigueur ;
- si cette version nécessite ou non une nouvelle acceptation.

La publication d'une nouvelle version ne doit pas automatiquement invalider toutes les acceptations si la modification est seulement éditoriale.

Cette décision doit être explicitement indiquée lors de la publication de la nouvelle version.

---

# 27. Traçabilité

La traçabilité doit être proportionnée au besoin.

AM doit pouvoir démontrer :

- quelles conditions étaient applicables ;
- quand elles ont été publiées ;
- quelles conditions ont été acceptées par un utilisateur ;
- quand l'acceptation a eu lieu.

Il n'est pas nécessaire de journaliser toutes les consultations de la politique de confidentialité.

---

# 28. Présentation de la popup

La popup ne doit pas essayer d'afficher l'intégralité de la politique de confidentialité.

Elle doit fonctionner en deux niveaux.

## Niveau 1 — information immédiate

Quelques paragraphes compréhensibles présentant :

- pourquoi certaines données sont nécessaires ;
- comment fonctionne la visibilité dans le groupe ;
- les conséquences de l'utilisation du planning ;
- l'existence des droits de l'utilisateur.

## Niveau 2 — documentation complète

Liens vers :

- politique de confidentialité ;
- conditions d'utilisation ;
- mentions légales ;
- informations relatives aux données personnelles.

Ces liens doivent pouvoir être ouverts sans perdre l'état de la popup.

---

# 29. Terminologie de l'interface

Éviter autant que possible une formulation générique telle que :

> J'accepte le RGPD.

Cette formulation est juridiquement et fonctionnellement imprécise.

Préférer des formulations telles que :

> J'ai pris connaissance des informations relatives à l'utilisation d'Animation Messe et au traitement de mes données.

Puis :

> J'accepte les conditions d'utilisation d'Animation Messe.

Si un véritable consentement RGPD est nécessaire pour une finalité facultative, celui-ci doit être présenté séparément avec la finalité concernée.

---

# 30. Règle fondamentale

L'accès aux données privées d'Animation Messe doit toujours répondre à quatre questions indépendantes :

1. **Qui est cette personne ?**
   → authentification.

2. **À quel groupe peut-elle accéder ?**
   → appartenance.

3. **A-t-elle accepté les règles actuellement applicables ?**
   → acceptation AM.

4. **Que peut-elle faire dans ce groupe ?**
   → permissions et rôles.

Aucune de ces étapes ne doit remplacer les autres.

---

# 31. Résumé du parcours

## Visiteur anonyme

`Page publique`
→ information RGPD/site si nécessaire  
→ navigation publique.

## Utilisateur connecté sans groupe

`Connexion`
→ aucune fonction privée de groupe  
→ accès public ou page expliquant qu'aucun groupe n'est disponible.

## Utilisateur avec groupe mais sans acceptation valable

`Connexion`
→ tentative d'accès AM  
→ popup d'information et d'acceptation  
→ refus : accès public uniquement  
→ acceptation : accès selon ses permissions.

## Utilisateur ayant déjà accepté

`Connexion`
→ vérification de la version  
→ si valide : accès normal  
→ si nouvelle acceptation obligatoire : popup avant accès privé.

---

# 32. Points restant à définir

Les éléments suivants devront faire l'objet de décisions complémentaires :

- contenu précis de la politique de confidentialité ;
- responsable de traitement à mentionner ;
- coordonnées permettant d'exercer les droits ;
- bases légales exactes de chaque traitement AM ;
- durée de conservation de l'historique des acceptations ;
- politique exacte concernant les cookies et statistiques ;
- comportement en cas de modification majeure des traitements ;
- distinction définitive entre simple rappel à 6 mois et nouvelle validation ;
- articulation avec la suppression/pseudonymisation automatique des comptes ;
- éventuelles règles spécifiques applicables aux utilisateurs mineurs.

---

# 33. Principe de conception à retenir pour Codex

Le mécanisme ne doit pas être conçu comme :

`une popup RGPD que l'on affiche de temps en temps`

mais comme un véritable état fonctionnel du compte :

`PUBLIC_ONLY`
ou
`AM_ACCESS_ALLOWED`

Cet état est calculé dynamiquement à partir :

- de l'authentification ;
- de l'appartenance à un groupe ;
- de la version des conditions ;
- de l'acceptation enregistrée ;
- des droits métier.

La popup n'est que l'interface permettant de modifier cet état lorsque l'utilisateur doit prendre connaissance ou accepter une nouvelle version.