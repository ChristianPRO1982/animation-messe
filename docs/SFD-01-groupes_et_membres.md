# SFD-01-groupes_et_membres

## Groupes, membres, accès et usages publics

> **Périmètre du document**  
> Ce document décrit uniquement les besoins fonctionnels côté utilisateur concernant :
> - les groupes ;
> - les rôles et membres ;
> - les accès à Animation Messe ;
> - les Membres AM ;
> - les règles de consentement et de protection des données associées ;
> - les groupes ouverts et l’usage sans compte ;
> - les animations anonymes et leur persistance.
>
> Il ne décrit ni l’UI, ni le backend, ni les modèles de données, ni l’architecture technique.

> **Format pour la conception technique**
> Les règles stables de ce document sont identifiées avec le préfixe `GRP-*`.
> Ces identifiants servent de points d’ancrage pour les modèles, permissions, workflows et tests techniques.

---

# 1. Principes généraux

Animation Messe (AM) appartient à l’écosystème **CARThographie**.

L’authentification des utilisateurs repose sur un compte CARThographie via Keycloak.

Un utilisateur connecté peut participer à la vie durable d’un groupe.  
Un utilisateur non connecté peut néanmoins utiliser certaines fonctions publiques lorsqu’un groupe les autorise.

Les rôles doivent rester volontairement simples.

Il n’existe **aucun rôle de modérateur**.

Le modèle comporte :

## Au niveau du site
- **Administrateur**

## Au niveau d’un groupe
- **Responsable**
- **Membre**
- **Membre AM**

Le **Membre AM** est un cas particulier : il représente une personne physique réelle qui ne possède pas de compte CARThographie.

---

# 2. Relation entre Animation Messe et Lyrics Slide Show

Les groupes d’Animation Messe et de Lyrics Slide Show (LSS) sont **les mêmes groupes**.

Il n’existe pas :
- un groupe AM ;
- et un groupe LSS séparé.

Il existe une seule entité de groupe commune à l’écosystème CARThographie.

Cependant, les accès sont volontairement asymétriques :

- **avoir accès à AM pour un groupe implique que ce groupe soit également disponible dans LSS** ;
- **faire partie d’un groupe dans LSS ne donne pas automatiquement accès à AM**.

Cette asymétrie est volontaire car AM manipule davantage de données personnelles et organisationnelles :
- identité des membres ;
- fonctions exercées ;
- disponibilités ;
- participations ;
- planning ;
- activité interne du groupe ;
- utilisation fonctionnelle de l’adresse email pour certains rappels.

Un utilisateur appartenant déjà au groupe dans LSS doit donc demander explicitement son accès à AM.

---

# 3. Deux types de groupes

Lors de la création d’un groupe dans AM, le créateur doit choisir son mode :

- **Groupe fermé**
- **Groupe ouvert**

Ce choix est important et doit être présenté comme tel.

## 3.1 Groupe fermé

Le groupe fermé correspond au fonctionnement collaboratif classique.

Pour utiliser les fonctions internes du groupe, il faut :
- posséder un compte CARThographie ;
- être rattaché au groupe ;
- disposer de l’accès AM ;
- être Membre ou Responsable.

Les informations internes du groupe ne sont pas accessibles publiquement.

## 3.2 Groupe ouvert

Un groupe ouvert reste un groupe normalement administré par des Responsables et éventuellement composé de Membres.

La différence est qu’il expose aussi certaines fonctionnalités utilisables **sans compte et sans connexion**.

Une personne anonyme peut notamment utiliser le groupe comme espace de préparation de messe afin de :
- sélectionner les textes ;
- sélectionner les chants ;
- construire un déroulé ;
- générer une feuille de messe.

Cette personne :
- ne devient pas Membre ;
- ne rejoint pas le groupe ;
- ne donne pas son nom ;
- n’est jamais invitée à donner son nom ;
- n’accède à aucune identité de Membre ;
- n’accède à aucune identité de Responsable ;
- n’accède pas au planning interne ;
- n’accède pas aux disponibilités ;
- n’accède pas aux informations d’administration du groupe.

L’ouverture du groupe concerne **des fonctionnalités**, jamais les données privées du groupe.

Toute nouvelle fonctionnalité d’AM doit être considérée comme **privée par défaut**, sauf décision explicite de la rendre utilisable dans l’espace public d’un groupe ouvert.

---

# 4. Création d’un groupe

Un utilisateur CARThographie connecté peut créer un groupe depuis AM.

Lors de la création :

- il choisit si le groupe est **ouvert** ou **fermé** ;
- le groupe commun AM/LSS est créé ;
- le créateur obtient l’accès AM ;
- le créateur devient automatiquement le premier **Responsable** ;
- le groupe devient disponible dans LSS.

Un groupe ne doit jamais naître sans Responsable.

Le mode ouvert/fermé pourra être modifié ultérieurement par un Responsable.

Le passage vers un groupe ouvert doit être accompagné d’un avertissement expliquant que certaines fonctions deviennent utilisables sans compte, tout en rappelant que les données internes du groupe restent privées.

---

# 5. Administrateur du site

L’Administrateur est un rôle global au niveau d’Animation Messe.

Il ne doit pas être confondu avec le Responsable d’un groupe.

Son rôle principal est :
- l’administration globale ;
- le support ;
- la résolution des problèmes ;
- la gestion des groupes abandonnés, moribonds ou mal configurés ;
- la maintenance fonctionnelle de la plateforme.

## 5.1 Pouvoirs de l’Administrateur

Un Administrateur peut notamment :

- créer un groupe ;
- modifier un groupe ;
- supprimer un groupe ;
- consulter l’administration d’un groupe ;
- ajouter ou retirer des Responsables ;
- publier un message destiné à un groupe ;
- publier un message général au niveau du site ;
- intervenir pour résoudre un problème administratif ou technique.

## 5.2 Accès au fonctionnement interne d’un groupe

L’Administrateur n’est pas automatiquement Membre ou Responsable de tous les groupes.

Par défaut, il administre le contenant et ne participe pas à la vie fonctionnelle du groupe.

Il ne doit donc pas automatiquement :
- participer au planning ;
- préparer une messe ;
- agir comme Membre ;
- agir comme Responsable dans le fonctionnement quotidien.

Cependant, l’Administrateur est volontairement très puissant.

Il peut s’ajouter lui-même à n’importe quel groupe et se nommer Responsable.

À partir de ce moment, il dispose des possibilités d’un Responsable normal du groupe.

Ce pouvoir est un risque assumé compte tenu de la très faible volumétrie prévue et du besoin de pouvoir débloquer manuellement des situations difficiles.

## 5.3 Traçabilité

Les interventions sensibles d’un Administrateur doivent être traçables.

Exemples :
- ajout de l’Administrateur comme Responsable ;
- ajout ou retrait d’un Responsable ;
- suppression d’un groupe ;
- fusion ou intervention exceptionnelle sur une identité ;
- modification administrative importante.

L’objectif n’est pas de limiter artificiellement l’Administrateur, mais de pouvoir comprendre a posteriori ce qui a été fait.

---

# 6. Responsable

Le Responsable est un **Membre disposant de pouvoirs administratifs supplémentaires**.

Il participe normalement à la vie du groupe.

Son rôle principal est de :
- garantir l’administration ;
- valider les choix engageants ;
- gérer les entrées et sorties du groupe ;
- protéger la cohérence du groupe.

## 6.1 Pouvoirs sur les groupes et membres

Un Responsable peut notamment :

- accepter une demande d’accès ;
- refuser une demande d’accès ;
- promouvoir un Membre en Responsable ;
- retirer la responsabilité d’un Responsable ;
- retirer un Membre du groupe ;
- créer une demande de création de Membre AM ;
- supprimer un Membre AM ;
- fusionner un Membre AM avec un compte CARThographie ;
- gérer les paramètres administratifs du groupe.

Dans les autres modules d’AM, le Responsable dispose également des pouvoirs de validation prévus par ces modules, notamment pour figer ou valider des décisions collectives.

Ces règles métier détaillées sont hors périmètre du présent document.

---

# 7. Membre

Le Membre est le rôle normal d’utilisation d’Animation Messe.

Il :
- possède un compte CARThographie ;
- possède un accès AM au groupe ;
- participe à la vie quotidienne du groupe.

La philosophie générale est :

> **Les Membres font vivre le groupe ; les Responsables administrent et valident.**

Un Membre standard n’est donc pas un simple lecteur.

Concernant les Membres AM, il peut :
- les voir ;
- gérer les informations courantes nécessaires au fonctionnement ;
- les utiliser dans l’organisation du groupe.

Il ne peut pas :
- créer un Membre AM ;
- supprimer un Membre AM ;
- valider une entrée dans le groupe ;
- exclure un Membre ;
- nommer un Responsable ;
- fusionner un Membre AM avec un compte CARThographie.

---

# 8. Membre AM

Un **Membre AM** représente une personne physique réelle qui participe à la vie de l’équipe mais ne possède pas de compte CARThographie lui permettant d’utiliser Animation Messe.

Exemples :
- organiste ne souhaitant pas créer de compte ;
- musicien occasionnel ;
- personne peu à l’aise avec les outils numériques ;
- intervenant régulier mais non utilisateur du site.

Le Membre AM :
- ne se connecte pas ;
- ne possède aucun droit informatique propre ;
- ne possède pas de compte Keycloak ;
- ne peut pas être Responsable ;
- existe uniquement dans la bulle fonctionnelle AM ;
- est géré par l’équipe pour les besoins du groupe.

Le terme **Membre AM** est le terme produit officiel.

---

# 9. Garde-fous du groupe

## 9.1 Dernier Responsable

Un groupe doit toujours avoir au moins un Responsable.

Il est impossible :
- de retirer la responsabilité au dernier Responsable ;
- d’exclure le dernier Responsable ;
- pour le dernier Responsable de quitter le groupe.

Un autre Responsable doit d’abord être nommé.

Cette règle s’applique également aux Administrateurs du site.

## 9.2 Dernier Membre

Le dernier véritable Membre d’un groupe ne doit pas être supprimé individuellement.

Pour faire disparaître complètement le groupe, il faut utiliser l’action explicite :

**Supprimer le groupe**

Cela évite de laisser un groupe incohérent, vide ou sans responsable humain.

---

# 10. Demander l’accès à un groupe

## 10.1 Utilisateur extérieur au groupe

Un utilisateur CARThographie qui ne fait pas encore partie du groupe peut demander à le rejoindre via AM.

Il doit recevoir les informations nécessaires concernant :
- le fonctionnement du groupe ;
- la visibilité de certaines données au sein de l’équipe ;
- les traitements propres à AM ;
- l’usage fonctionnel éventuel de son email ;
- les règles de consentement applicables.

La demande reste en attente jusqu’à décision d’un Responsable.

Le Responsable peut :
- accepter ;
- refuser.

En cas d’acceptation :
- la personne rejoint le groupe ;
- elle devient **Membre** ;
- elle obtient l’accès AM ;
- le groupe lui devient également disponible dans LSS.

## 10.2 Utilisateur déjà membre dans LSS

Un utilisateur peut appartenir au groupe commun via LSS sans avoir accès à AM.

Dans ce cas, AM doit reconnaître cette appartenance.

L’utilisateur ne « rejoint » pas le groupe une seconde fois.

Il demande :

**l’accès à Animation Messe pour cette équipe**

Cette demande nécessite :
- l’information sur les traitements propres à AM ;
- le consentement requis ;
- la validation d’un Responsable.

L’appartenance LSS seule ne donne jamais automatiquement accès aux informations internes d’AM.

---

# 11. Quitter un groupe

Il faut distinguer deux actions.

## 11.1 Quitter Animation Messe

Le Membre ne souhaite plus utiliser AM pour ce groupe.

Son accès AM est supprimé.

Son appartenance au groupe côté LSS peut être conservée.

## 11.2 Quitter complètement le groupe

La personne quitte le groupe commun.

Elle perd donc son rattachement AM et LSS.

Le dernier Responsable ne peut pas quitter complètement le groupe tant qu’un autre Responsable n’a pas été nommé.

Le dernier Membre ne peut pas être retiré individuellement : la disparition complète doit passer par la suppression du groupe.

---

# 12. Création d’un Membre AM

Seul un Responsable peut initier la création d’un Membre AM.

Comme le profil représente une personne réelle sans compte, sa création nécessite un consentement explicite de cette personne.

## 12.1 Étape 1 — Demande

Le Responsable saisit :
- le nom ;
- le prénom ;
- une adresse email temporaire permettant de contacter la personne.

À ce stade, aucun Membre AM actif n’est créé.

Il existe uniquement une **demande de création de Membre AM**.

## 12.2 Étape 2 — Email d’information et consentement

La personne reçoit un email expliquant clairement :
- quel groupe souhaite la référencer ;
- pourquoi son identité sera utilisée ;
- quelles catégories d’informations pourront être conservées ;
- que son nom pourra apparaître dans l’organisation et les plannings du groupe ;
- que les Membres du groupe pourront manipuler les informations nécessaires ;
- qu’elle ne possède pas de compte CARThographie ;
- qu’elle peut accepter ou refuser ;
- qu’elle pourra ultérieurement revenir sur son accord.

La personne doit réaliser une action positive :

- **Accepter**
- **Refuser**

L’absence de réponse n’est jamais considérée comme une acceptation.

---

# 13. Durée d’une demande de Membre AM

Une demande de création reste valable pendant **14 jours**.

Pendant cette période :
- la personne n’est pas encore Membre AM ;
- elle ne doit pas être utilisable comme Membre AM actif.

Si aucune réponse n’est donnée au terme des 14 jours :

- la demande expire ;
- le nom est supprimé ;
- le prénom est supprimé ;
- l’adresse email est supprimée ;
- les autres données personnelles associées à cette demande sont supprimées.

La demande ne doit pas devenir un historique permanent des personnes sollicitées.

---

# 14. Refus d’un Membre AM

Si la personne refuse :

- aucun Membre AM n’est créé ;
- son adresse email est supprimée ;
- son nom et son prénom complets sont supprimés.

Un indicateur temporaire minimal peut rester visible uniquement aux Responsables afin qu’ils comprennent le résultat de leur demande.

Exemple :

**M**** — demande refusée**

Cet indicateur :
- n’est visible qu’aux Responsables ;
- reste visible pendant **14 jours après le refus** ;
- est ensuite totalement supprimé.

Le refus ne doit pas devenir une liste permanente des personnes ayant dit non.

---

# 15. Acceptation d’un Membre AM

En cas d’acceptation :

- le véritable Membre AM est créé ;
- l’adresse email utilisée pour le consentement n’est plus conservée en clair pour l’usage courant ;
- les informations nécessaires au fonctionnement du Membre AM sont conservées ;
- la preuve du consentement est conservée.

La preuve doit permettre de démontrer au minimum :
- qu’un consentement a été donné ;
- quand il a été donné ;
- pour quel groupe ;
- selon quelle version de l’information ou du consentement.

---

# 16. Vérification de l’adresse ayant consenti

Le consentement par email ne prouve pas parfaitement l’identité physique de la personne.

Il prouve principalement que quelqu’un contrôlant l’adresse utilisée a réalisé l’action de validation.

Animation Messe n’a pas vocation à mettre en place une vérification d’identité forte.

Le système repose sur un modèle de **confiance raisonnable entre personnes de bonne foi**, accompagné de garde-fous permettant d’éviter les abus grossiers et d’auditer un problème.

## 16.1 Empreinte de l’adresse

L’adresse email utilisée pour valider peut être transformée en une empreinte cryptographique protégée avant suppression de l’adresse en clair.

Cette empreinte permet, en cas d’audit :
- de comparer ultérieurement une adresse candidate ;
- de savoir si cette adresse est ou non celle qui a servi au consentement ;
- de détecter qu’une même adresse a servi à valider plusieurs Membres AM.

Cette empreinte reste une donnée personnelle pseudonymisée et doit être protégée comme telle.

## 16.2 Contrôles simples

Au moment de créer une demande, AM peut empêcher les cas les plus évidents :

- si le Responsable utilise sa propre adresse CARThographie pour créer le Membre AM d’une autre personne ;
- si l’adresse correspond déjà clairement à un compte CARThographie connu.

Cela ne permet pas d’empêcher un Responsable volontairement malveillant utilisant une autre adresse dont il a le contrôle.

Cette limite est acceptée.

Le site ne cherche pas à certifier juridiquement l’identité physique de chaque Membre AM.

---

# 17. Secret personnel du Membre AM

Après acceptation, le Membre AM doit disposer d’un moyen autonome de revenir sur son consentement sans créer de compte CARThographie.

Un email de confirmation lui est envoyé.

Cet email contient un lien personnel reposant sur un secret individuel.

Ce secret :
- appartient à la personne ;
- ne doit pas être visible par les Responsables ;
- ne doit pas être utilisable directement par les Administrateurs ou développeurs ;
- permet d’accéder à la gestion de son consentement.

Le système ne doit conserver qu’un moyen technique de vérifier ce secret, pas le secret exploitable en clair.

---

# 18. Retrait du consentement d’un Membre AM

Le lien personnel ne doit jamais provoquer une suppression immédiate par simple ouverture.

Il doit conduire à une étape de confirmation explicite.

La personne peut alors demander à :
- retirer son consentement ;
- demander la fin de son profil Membre AM.

Le système doit expliquer clairement les conséquences avant confirmation.

Les effets détaillés sur l’antériorité, les anciens plannings ou autres contenus historiques relèvent des spécifications métier correspondantes.

Le présent document garantit uniquement qu’un Membre AM possède un moyen autonome de demander la fin de son profil.

---

# 19. Perte du lien personnel

Si le Membre AM perd l’email contenant son lien ou son secret :

- il peut contacter l’équipe ;
- un Responsable peut lancer une nouvelle procédure de vérification ;
- une nouvelle adresse temporaire peut être utilisée ;
- un nouveau secret peut remplacer l’ancien après validation ;
- l’adresse temporaire est ensuite de nouveau supprimée.

Cette procédure reste exceptionnelle.

---

# 20. Gestion quotidienne d’un Membre AM

Une fois le consentement obtenu et le Membre AM créé :

- tous les Membres ;
- tous les Responsables

peuvent manipuler les informations nécessaires à son utilisation quotidienne.

La création et la suppression d’un Membre AM restent réservées aux Responsables.

Le but est de ne pas faire porter toute la gestion opérationnelle des personnes sans compte sur les Responsables.

---

# 21. Modification de l’identité d’un Membre AM

Le consentement est donné pour une personne donnée.

Un Membre ou Responsable ne doit pas pouvoir transformer progressivement un Membre AM en une autre personne.

Une modification substantielle de l’identité, notamment nom/prénom, doit être considérée comme une opération sensible.

Si la modification revient fonctionnellement à représenter une autre personne, une nouvelle procédure de consentement doit être nécessaire.

---

# 22. Transformation d’un Membre AM en Membre CARThographie

Un Membre AM peut ultérieurement décider de créer son propre compte CARThographie.

La transformation suit trois étapes.

## 22.1 Création du compte CARThographie

La personne crée normalement son compte dans l’écosystème CARThographie.

## 22.2 Rattachement au groupe

Le compte rejoint le même groupe selon le processus normal d’accès.

Pendant un court moment, peuvent donc coexister :
- le nouveau Membre CARThographie ;
- l’ancien Membre AM correspondant à la même personne.

## 22.3 Fusion

Un Responsable déclenche explicitement la fusion.

La fusion :
- associe le compte CARThographie à l’ancien Membre AM ;
- récupère l’antériorité utile ;
- transfère les rattachements nécessaires ;
- supprime ensuite le profil Membre AM devenu redondant.

La fusion ne doit jamais être automatique sur la seule base :
- d’un nom ;
- d’un prénom ;
- d’un email ressemblant ;
- d’une ressemblance d’identité.

---

# 23. Données personnelles d’un Membre avec compte

Un Membre CARThographie gère son identité au niveau de son compte.

Le groupe ne doit pas arbitrairement modifier :
- son identité générale ;
- son adresse email de compte ;
- les informations relevant directement du compte CARThographie.

Le groupe gère uniquement les informations propres à son appartenance et à son activité dans l’équipe.

À l’inverse, le Membre AM n’ayant aucun compte permettant de gérer lui-même ses informations, l’équipe peut administrer les données nécessaires dans les limites du consentement obtenu.

---

# 24. Philosophie RGPD

Animation Messe traite des données plus sensibles que Lyrics Slide Show.

L’appartenance à une équipe paroissiale, certaines fonctions exercées ou certains éléments organisationnels peuvent révéler ou permettre d’inférer des convictions religieuses.

AM adopte donc volontairement une approche prudente :

- consentement opt-in lorsque nécessaire ;
- information claire ;
- minimisation des données ;
- absence de publicité ;
- absence de prospection ;
- absence de spam ;
- utilisation de l’email uniquement pour une finalité fonctionnelle déterminée ;
- visibilité des données limitée au besoin du groupe ;
- suppression des données devenues inutiles ;
- traçabilité des actions administratives sensibles ;
- possibilité de retrait du consentement pour les Membres AM.

Concernant les Membres AM, le principe directeur est :

> **Une équipe ne doit pas décider silencieusement qu’une personne réelle existe dans Animation Messe.**

La personne doit avoir accepté d’y être représentée.

---

# 25. Limites assumées du modèle de consentement

Aucun système léger ne peut garantir parfaitement que la personne ayant cliqué sur un lien email correspond juridiquement à l’identité saisie.

Pour atteindre ce niveau de certitude, il faudrait une vérification d’identité forte disproportionnée pour AM.

Animation Messe repose donc sur le principe suivant :

> **Le site cherche à obtenir un consentement explicite, traçable et révocable, et à limiter les abus raisonnablement prévisibles. Il ne cherche pas à certifier l’identité juridique de chaque Membre AM.**

Le contexte prévu est celui de petits groupes humains se connaissant réellement.

La volumétrie cible est faible :
- quelques paroisses ;
- quelques dizaines de personnes ;
- groupes de l’ordre d’une dizaine de personnes.

La confiance humaine reste donc une composante assumée du système.

---

# 26. Utilisation d’un groupe ouvert sans compte

Le groupe ouvert permet un usage anonyme sans connexion.

La personne anonyme peut préparer une animation ou une messe sans :
- créer de compte ;
- fournir son nom ;
- fournir son email ;
- devenir Membre ;
- apparaître dans une liste de personnes.

Aucune identité des Membres ou Responsables du groupe ne doit lui être exposée.

Les données internes du groupe restent privées.

---

# 27. Trois modes pour une animation anonyme

Une animation créée dans l’espace public d’un groupe ouvert peut être dans l’un des trois modes suivants :

- **Éphémère**
- **Conservée avec code**
- **Conservée sans code**

Une animation peut passer librement d’un mode à n’importe quel autre mode.

---

# 28. Mode éphémère

L’animation n’est pas destinée à être conservée durablement.

Elle vit uniquement dans la session courante de l’utilisateur.

Elle :
- n’est pas partagée ;
- n’est pas retrouvable depuis un autre appareil ou navigateur ;
- n’est pas visible des autres internautes ;
- ne constitue pas un espace de stockage durable.

Si la session prend fin, le travail est perdu.

L’utilisateur doit comprendre :

> **Cette animation n’est pas enregistrée et sera perdue à la fin de votre session.**

Une animation éphémère peut à tout moment devenir :
- conservée avec code ;
- conservée sans code.

Une animation conservée peut également redevenir éphémère.

Dans ce cas :
- sa copie persistante est supprimée ;
- son ancien lien cesse de fonctionner ;
- la version encore présente dans la session courante continue d’exister jusqu’à la fin de cette session.

Le site ne peut évidemment pas annuler les copies ou exports déjà réalisés par des tiers.

---

# 29. Mode conservé avec code

L’animation est conservée temporairement.

Elle est accessible à toute personne disposant :
- du lien permettant de retrouver l’animation ;
- du code demandé.

Aucun compte n’est nécessaire.

Le code doit être simple à transmettre oralement ou par messagerie.

Le fait de posséder le code permet de reprendre l’animation selon les droits prévus pour ce mode.

Ce mode constitue le compromis recommandé entre :
- simplicité ;
- absence de compte ;
- partage ;
- protection minimale.

L’animation n’est pas destinée à être répertoriée dans un annuaire public du site.

---

# 30. Mode conservé sans code

L’animation est conservée temporairement et accessible à toute personne disposant de son lien.

Aucun compte ni code n’est nécessaire.

Ce mode est volontairement permissif.

Toute personne disposant du lien peut potentiellement modifier le contenu selon les règles du mode public.

Avant d’activer ce mode, un avertissement clair doit expliquer le risque.

Exemple de principe :

> **Toute personne disposant de ce lien pourra accéder à cette animation sans code et pourra la modifier.**

L’utilisateur doit accepter explicitement ce risque.

Il n’est pas nécessaire de multiplier ensuite les alertes à chaque action.

Un indicateur persistant rappelant que l’animation est publique suffit.

---

# 31. Visibilité publique des animations

Même lorsqu’une animation est conservée sans code, elle n’a pas vocation à apparaître dans une liste publique mondiale des animations en cours.

Il faut distinguer :

- **accessible publiquement**
- **répertoriée publiquement**

Une animation sans code peut être accessible à toute personne disposant du lien sans être répertoriée dans un annuaire public.

Une animation avec code n’est pas répertoriée publiquement non plus.

Cette règle limite fortement le risque de vandalisme sans empêcher les usages de partage simple.

---

# 32. Passage entre les modes

Les transitions sont toutes autorisées :

- Éphémère → Avec code
- Éphémère → Sans code
- Avec code → Éphémère
- Avec code → Sans code
- Sans code → Avec code
- Sans code → Éphémère

## 32.1 Ajout d’un code

Une animation sans code peut être protégée ultérieurement avec un code.

## 32.2 Retrait d’un code

Une animation avec code peut devenir accessible sans code.

Cette action doit déclencher un avertissement avant confirmation.

## 32.3 Retour en éphémère

Une animation conservée peut redevenir éphémère.

Cette action signifie :

> **Arrêter le partage et supprimer la version conservée par Animation Messe.**

L’utilisateur doit être averti que :
- le lien cessera de fonctionner ;
- l’animation ne subsistera plus que dans sa session courante ;
- elle sera perdue à la fin de cette session.

---

# 33. Durée de conservation des animations anonymes

## 33.1 Animation conservée

Pour une animation :
- avec code ;
- ou sans code ;

la date de suppression est déterminée à partir de la **date de l’animation**.

Principe actuel :

> **Date de suppression = date de l’animation + environ 15 jours**

Cette durée pourra être ajustée ultérieurement dans le paramétrage global du produit.

Cette règle permet :
- de revenir sur une animation après la célébration ;
- de la remodifier ;
- de la dupliquer ;
- de changer sa date ;
- de la réutiliser comme base pour une nouvelle animation.

Si la date de l’animation est modifiée, sa nouvelle date d’expiration suit la nouvelle date d’animation.

Une animation oubliée finit donc automatiquement par être supprimée.

## 33.2 Animation éphémère

Une animation éphémère n’est pas destinée à persister au-delà de la session courante.

Fonctionnellement, son expiration est immédiate ou liée à la fin de session.

L’utilisateur doit simplement comprendre :

> **Cette animation n’est pas enregistrée.**

---

# 34. Données publiques autorisées dans une animation anonyme

Une animation publique peut contenir uniquement les données nécessaires à la préparation de la célébration.

Exemples :
- nom de la paroisse ou du groupe ;
- date ;
- lieu si nécessaire ;
- titre de la célébration ;
- textes ;
- chants ;
- déroulé ;
- informations utiles à la feuille de messe.

Elle ne doit jamais exposer :
- le nom d’un Responsable ;
- le nom d’un Membre ;
- le nom d’un Membre AM hors besoin métier explicitement prévu ;
- les disponibilités ;
- le planning interne ;
- les données de compte ;
- l’identité de la personne ayant créé ou modifié l’animation.

Le visiteur anonyme ne doit jamais avoir à fournir son identité.

---

# 35. Absence de traçage fonctionnel des visiteurs anonymes

L’usage public d’un groupe ouvert doit pouvoir fonctionner :
- sans compte ;
- sans profil ;
- sans publicité ;
- sans prospection ;
- sans rattachement à une identité ;
- sans historique comportemental personnel.

Les préparations anonymes ne doivent pas être rattachées à une identité utilisateur.

Des données purement techniques indispensables au fonctionnement ou à la sécurité de l’infrastructure peuvent exister, mais elles ne doivent pas être utilisées pour créer un profil utilisateur ou suivre l’usage d’une personne entre plusieurs sessions.

---

# 36. Résumé des rôles

## Administrateur

Rôle global du site.

> **Maintient, supporte et peut débloquer la plateforme entière.**

Il peut se nommer Responsable de n’importe quel groupe.

## Responsable

Rôle administratif d’un groupe.

> **Garantit l’administration, les accès et les validations engageantes du groupe.**

## Membre

Utilisateur normal du groupe.

> **Fait vivre quotidiennement le groupe.**

## Membre AM

Personne réelle sans compte CARThographie.

> **Permet de représenter et gérer dans AM une personne qui participe à l’équipe sans utiliser elle-même le logiciel.**

Il n’existe aucun rôle de modérateur.

---

# 37. Règle directrice des permissions

Lorsqu’une nouvelle fonction est conçue, la question de référence doit être :

> **Cette action relève-t-elle de la vie courante de l’équipe, engage-t-elle administrativement le groupe, ou relève-t-elle du support global ?**

- Vie courante → **Membre et Responsable**
- Engagement ou validation administrative → **Responsable**
- Support et gouvernance globale → **Administrateur**
- Personne sans accès logiciel → **Membre AM**

Ce principe doit permettre d’éviter progressivement l’apparition de rôles supplémentaires inutiles.

---

# 38. Philosophie générale du site

Animation Messe doit rester utilisable dans deux logiques complémentaires.

## Usage durable et collaboratif

Pour une équipe qui souhaite :
- gérer son groupe ;
- organiser son planning ;
- préparer durablement les célébrations ;
- travailler collectivement.

Cela passe par :
- un compte CARThographie ;
- un groupe ;
- des Membres ;
- des Responsables.

## Usage libre et ponctuel

Pour une personne ou une petite équipe qui souhaite simplement :
- préparer une célébration ;
- sélectionner des textes et des chants ;
- produire une feuille de messe.

Cela doit rester possible :
- sans compte ;
- sans donner son nom ;
- sans publicité ;
- sans coût ;
- sans profilage ;
- sans devoir entrer dans tout l’écosystème CARThographie.

Le groupe ouvert constitue le point d’entrée de cet usage libre.

---

# 39. Règles fonctionnelles essentielles

**GRP-ROLE-01** — Les rôles globaux et de groupe restent limités à Administrateur, Responsable, Membre et Membre AM.

**GRP-ROLE-02** — Il n’existe aucun rôle de modérateur.

**GRP-ADMIN-01** — Un Administrateur est un rôle global distinct du Responsable de groupe.

**GRP-ADMIN-02** — Un Administrateur peut se nommer Responsable d’un groupe pour intervenir dans son fonctionnement.

**GRP-ADMIN-03** — Les interventions sensibles d’un Administrateur doivent être traçables.

**GRP-RESP-01** — Un Responsable est un Membre disposant de pouvoirs administratifs supplémentaires sur son groupe.

**GRP-GARDE-01** — Un groupe doit toujours conserver au moins un Responsable.

**GRP-AM-01** — Un Membre AM représente une personne physique sans compte CARThographie.

**GRP-AM-02** — Un Membre AM ne peut pas se connecter, ne peut pas être Responsable et ne possède pas de droits applicatifs.

**GRP-AM-03** — La création d’un Membre AM nécessite une demande initiée par un Responsable et un consentement explicite.

**GRP-AM-04** — Une demande de création de Membre AM expire après 14 jours.

**GRP-AM-05** — Un refus de création ne crée aucun Membre AM et ne conserve qu’un indicateur temporaire visible des Responsables pendant 14 jours.

**GRP-AM-06** — Le Membre AM dispose d’un lien personnel lui permettant de gérer ou retirer son consentement sans créer de compte.

**GRP-AM-07** — Le secret personnel d’un Membre AM ne doit jamais être stocké ou exposé en clair.

**GRP-AM-08** — La fusion d’un Membre AM avec un compte CARThographie doit être déclenchée explicitement par un Responsable.

**GRP-PERM-01** — La vie courante relève des Membres et Responsables.

**GRP-PERM-02** — Les engagements administratifs et validations engageantes relèvent des Responsables.

**GRP-PUBLIC-01** — Un groupe ouvert peut exposer certaines fonctions sans compte sans exposer les données internes du groupe.

**GRP-PUBLIC-02** — Une animation publique anonyme ne doit exposer que les données nécessaires à la préparation de la célébration.

**GRP-RGPD-01** — Les données personnelles doivent suivre les principes de minimisation, transparence, consentement et suppression des données devenues inutiles.

---

# 40. Points encore à spécifier

Les points suivants doivent rester visibles pour la conception technique :

1. effets précis du retrait de consentement d’un Membre AM sur les affectations historiques dans le planning et les célébrations ;
2. comportement exact des notifications et rappels liés aux demandes d’accès ou de consentement ;
3. modèle de preuve et de conservation associé aux consentements, refus et retraits ;
4. périmètre exact des données publiques autorisées pour chaque mode d’animation anonyme.

---

# 41. Principe final

La philosophie fonctionnelle de cette partie peut se résumer ainsi :

> **Animation Messe doit permettre une organisation structurée et responsable pour les équipes qui souhaitent s’inscrire dans la durée, tout en laissant un accès libre, simple et anonyme aux fonctionnalités qui peuvent raisonnablement l’être.**

La protection des données personnelles ne repose pas uniquement sur des droits techniques.

Elle repose aussi sur :
- la minimisation ;
- la transparence ;
- le consentement ;
- la suppression des données devenues inutiles ;
- la séparation stricte entre données publiques et données internes ;
- des responsabilités humaines simples et compréhensibles.
