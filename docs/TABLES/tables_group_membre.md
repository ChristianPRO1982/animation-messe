# Directive Codex — migrations initiales Animation Messe et SQL `common`

## 1. Objectif

Mettre en place le premier socle de données propre à **Animation Messe**, principalement pour :

* `app_member` ;
* `app_group` ;
* les tables partagées de tags stockées manuellement dans le schéma PostgreSQL `common`.

Ce travail doit préparer proprement les développements futurs de :

* `app_planning` ;
* `app_celebration` ;
* la gestion du répertoire de chants ;
* la génération des feuilles de messe.

Ne pas implémenter ces applications métier maintenant.

Le but de cette étape est d'obtenir une base :

* cohérente ;
* normalisée ;
* simple à maintenir ;
* suffisamment transverse pour éviter que les rôles ou fonctions du groupe dépendent d'une application métier particulière.

---

# 2. Documents de référence

Avant toute modification, lire au minimum :

* `docs/general_overview.md`
* `docs/SFD-01-groupes_et_membres.md`
* `docs/SFD-02-planning.md`
* `docs/SFD-03-chants.md`
* `docs/SFD-04-celebrations.md`
* `docs/app_group/functional_requirements.md`
* `docs/app_member/functional_requirements.md`
* `docs/keycloak_connexion.md`

En cas de contradiction :

> les SFD font foi.

Certaines anciennes parties de `app_member` proviennent de Lyrics Slide Show et sont obsolètes pour Animation Messe, notamment le rôle `moderator`.

Animation Messe ne possède **aucun rôle de modérateur**.

---

# 3. Contraintes impératives concernant `users.users`

## 3.1. Ne pas modifier `users.users`

Le schéma et la table existants doivent être conservés tels quels :

```text
users.users
```

Animation Messe ne doit créer :

* aucune migration dans le schéma `users` ;
* aucune colonne dans `users.users` ;
* aucune table de remplacement ;
* aucune copie locale de cette table.

Le modèle actuel `DirectoryUserRecord` reste `managed = False`.

Il continue à exposer les données actuellement disponibles, notamment :

* `id` UUID ;
* `username` ;
* `first_name` ;
* `last_name` ;
* `email` ;
* `enabled` ;
* `email_verified` ;
* etc.

L'identité canonique d'un utilisateur CARThographie reste :

```text
users.users.id
```

de type UUID.

## 3.2. Pas de duplication d'identité

Pour un utilisateur possédant un compte CARThographie, Animation Messe ne doit pas recopier dans ses tables :

* prénom ;
* nom ;
* username ;
* email.

Ces données doivent être lues dans `users.users`.

Une duplication ne sera autorisée ultérieurement que pour un besoin historique explicite de type snapshot.

## 3.3. Suppression d'un compte

Le membre local AM doit être relié à :

```text
users.users(id)
```

avec :

```text
ON DELETE CASCADE
```

La suppression du compte source supprime donc le profil AM courant associé.

Les futures tables historiques, notamment planning et célébrations, devront être conçues pour ne pas provoquer de suppression en cascade de leur historique simplement parce qu'un utilisateur disparaît.

---

# 4. Convention de nommage des tables AM

Toutes les tables gérées par Django pour Animation Messe sont créées dans :

```text
am
```

Préfixes :

```text
app_member       -> m_*
app_group        -> g_*
app_planning     -> p_*
app_celebration  -> c_*
```

## 4.1. Convention des identifiants

Chaque table possède un alias naturel.

Son identifiant primaire reprend cet alias.

Exemples :

```text
m_member                 -> mm_id
m_preferences            -> mp_id

g_group                  -> gg_id
g_group_member           -> ggm_id
g_am_member              -> gam_id
g_role                   -> gr_id
g_group_member_role      -> ggmr_id
g_function               -> gf_id
g_group_member_function  -> ggmf_id
g_location               -> gl_id
```

Cette convention est obligatoire.

## 4.2. Convention des clés étrangères

Une FK conserve **exactement le nom de la PK qu'elle référence**.

Exemple :

```text
g_group.gg_id
    ↓
g_group_member.gg_id
    ↓
g_function.gg_id
```

Une FK vers :

```text
g_group_member.ggm_id
```

s'appelle toujours :

```text
ggm_id
```

Ne pas générer des noms tels que :

```text
member_id
group_member_id
group_fk
```

lorsque la PK cible est `ggm_id`.

---

# 5. Architecture générale

La répartition des responsabilités doit être la suivante.

```text
users.users
    identité CARThographie

app_member
    profil global Animation Messe
    administration globale du site
    préférences personnelles

app_group
    appartenance à un groupe
    Membres AM
    rôles du groupe
    fonctions du groupe
    affectation des rôles et fonctions
    paramètres du groupe

app_planning
    utilisation concrète du planning

app_celebration
    célébrations
    déroulés
    droits effectifs sur une célébration
    validation
    feuilles de messe
```

Principe important :

> Un paramètre durable définissant le fonctionnement d'un groupe appartient à `app_group`.

> Une donnée représentant ce qui s'est réellement produit dans une célébration ou dans un planning appartient à l'application métier correspondante.

Ne pas créer une grosse colonne JSON générique contenant tous les paramètres du groupe.

Créer des colonnes ou tables métier explicites au fur et à mesure que les paramètres sont stabilisés.

---

# 6. `app_member`

## 6.1. Table `am.m_member`

Alias :

```text
mm
```

PK :

```text
mm_id UUID
```

`mm_id` correspond exactement à :

```text
users.users.id
```

Ajouter en base PostgreSQL une FK réelle :

```text
m_member.mm_id
    -> users.users.id
    ON DELETE CASCADE
```

Comme `users.users` est externe à Django AM, utiliser si nécessaire une opération `RunSQL` pour créer cette FK sans rendre Django propriétaire de `users.users`.

Champs minimum :

```text
mm_id
is_admin
created_at
updated_at
```

`is_admin` représente exclusivement :

> Administrateur du site Animation Messe.

Il s'agit du seul rôle global AM.

Il n'existe pas :

```text
is_moderator
```

et il ne faut recréer aucun concept de modérateur.

### Règle importante

Être Administrateur du site ne rend pas automatiquement la personne :

* Membre d'un groupe ;
* Responsable d'un groupe ;
* participant au planning.

L'Administrateur peut administrer les groupes globalement et peut explicitement s'ajouter à un groupe lorsqu'une intervention métier le nécessite.

---

# 7. Préférences personnelles

Créer/conserver :

```text
am.m_preferences
```

Alias :

```text
mp
```

PK :

```text
mp_id
```

FK unique :

```text
mm_id
    -> am.m_member.mm_id
    ON DELETE CASCADE
```

Un membre possède au maximum une ligne de préférences.

Prévoir au minimum :

```text
theme_slug
calendar_week_start
```

`calendar_week_start` doit accepter uniquement :

```text
monday
sunday
```

Valeur par défaut :

```text
monday
```

Le champ historique `song_search` provenant de LSS n'a pas vocation à faire partie du nouveau modèle AM.

S'il n'est utilisé que par l'ancien modèle et ses tests, le supprimer proprement.

---

# 8. Le groupe commun LSS / AM

Les groupes LSS et AM représentent la même entité fonctionnelle.

Le système actuel possède déjà :

```text
lss.g_groups
```

avec :

```text
group_id
```

Ce système ne doit pas être refondu pendant cette tâche.

Créer dans AM une extension 1–1 :

```text
am.g_group
```

Alias :

```text
gg
```

PK :

```text
gg_id INTEGER
```

Le `gg_id` doit reprendre exactement la valeur de :

```text
lss.g_groups.group_id
```

Ajouter la contrainte :

```text
am.g_group.gg_id
    -> lss.g_groups.group_id
    ON DELETE CASCADE
```

Ne pas recopier dans `am.g_group` :

* le nom du groupe ;
* sa description LSS ;
* ses autres informations intrinsèques déjà présentes dans `lss.g_groups`.

`am.g_group` représente l'extension Animation Messe du groupe commun.

La présence d'une ligne dans `am.g_group` signifie que le groupe dispose de son environnement AM.

---

# 9. Paramètres principaux du groupe

`app_group` est responsable de tous les paramètres durables propres au groupe.

Dans `g_group`, prévoir au minimum les paramètres stabilisés ne nécessitant pas une table dédiée :

```text
gg_id
is_open
celebration_retention_months
created_at
updated_at
```

`celebration_retention_months` :

```text
1 <= valeur <= 24
```

La valeur par défaut peut être définie explicitement dans le modèle, mais ne pas inventer d'autres politiques de rétention.

## Attention sur l'archivage

Le groupe possède la **politique de conservation**.

En revanche :

```text
c_celebration.is_archived
```

appartiendra plus tard à `app_celebration`.

Ne pas mettre un état `archived` de célébration dans `app_group`.

---

# 10. Appartenance AM à un groupe

Créer :

```text
am.g_group_member
```

Alias :

```text
ggm
```

PK :

```text
ggm_id
```

Champs :

```text
ggm_id
gg_id
mm_id
member_kind
joined_at
created_at
updated_at
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Pour un membre possédant un compte :

```text
mm_id
    -> am.m_member.mm_id
    ON DELETE CASCADE
```

`mm_id` est nullable car un Membre AM ne possède pas de compte CARThographie.

`member_kind` accepte uniquement :

```text
account
am
```

Contraintes :

```text
member_kind = account  => mm_id IS NOT NULL
member_kind = am       => mm_id IS NULL
```

Pour un membre `account`, imposer l'unicité :

```text
(gg_id, mm_id)
```

Un utilisateur CARThographie ne peut donc avoir qu'une appartenance AM au même groupe.

---

# 11. Signification de Membre

Ne pas créer un rôle `Membre` redondant.

Pour un compte CARThographie :

> exister dans `g_group_member` avec `member_kind = account` signifie être Membre du groupe dans AM.

Le Membre constitue le niveau fonctionnel de base.

Les droits supplémentaires sont ajoutés par des rôles.

---

# 12. Membre AM

Le Membre AM est une personne réelle ne possédant aucun accès informatique propre.

Créer :

```text
am.g_am_member
```

Alias :

```text
gam
```

PK :

```text
gam_id
```

FK 1–1 unique :

```text
ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE CASCADE
```

Champs minimum :

```text
gam_id
ggm_id
first_name
last_name
gamt_id
consented_at
consent_version
consent_email_fingerprint
withdrawal_secret_hash
created_at
updated_at
```

Un Membre AM :

* n'a pas de compte ;
* ne peut pas se connecter ;
* n'obtient jamais de permission applicative ;
* ne peut jamais être Responsable ;
* ne peut jamais être Responsable impression.

Il peut néanmoins :

* recevoir une ou plusieurs fonctions ;
* apparaître dans le planning ;
* être affecté à des célébrations.

---

# 13. Titres configurables des Membres AM

Les titres proposés aux Membres AM sont des paramètres du groupe.

Créer :

```text
am.g_am_member_title
```

Alias :

```text
gamt
```

PK :

```text
gamt_id
```

Champs :

```text
gamt_id
gg_id
label
position
is_active
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

`g_am_member.gamt_id` est nullable.

Suppression d'un titre :

```text
ON DELETE SET NULL
```

Ne pas coder en dur la liste de titres.

Un groupe peut définir et ordonner ses propres intitulés.

---

# 14. Rôles du groupe

Les rôles appartiennent à `app_group`.

Créer :

```text
am.g_role
```

Alias :

```text
gr
```

PK :

```text
gr_id
```

Champs :

```text
gr_id
gg_id
code
label
position
is_system
is_active
created_at
updated_at
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Contrainte unique :

```text
(gg_id, code)
```

Les deux rôles système de V1 sont :

```text
responsable
responsable_impression
```

Libellés métier :

```text
Responsable
Responsable impression
```

Ces rôles sont cumulables.

Ne pas ajouter :

```text
moderator
modérateur
```

## Responsable

Le Responsable est avant tout un Membre.

Il cumule les capacités normales d'un Membre avec les capacités administratives du groupe.

Il est notamment responsable :

* de l'administration du groupe ;
* des membres ;
* des demandes d'accès ;
* de la création et suppression des Membres AM ;
* du planning ;
* des validations du planning prévues par sa SFD ;
* de la validation et dévalidation des célébrations.

### Règle fondamentale

Seul un Responsable peut :

```text
valider une célébration
dévalider une célébration
```

Un Membre disposant du droit de modifier une célébration :

```text
NE PEUT PAS la valider.
```

## Responsable impression

Le Responsable impression est un rôle cumulable.

Il donne uniquement les droits liés aux feuilles de messe prévues après validation d'une célébration.

Il ne donne aucun droit supplémentaire :

* sur le planning ;
* sur le déroulé ;
* sur la validation ;
* sur l'administration du groupe.

Le code fonctionnel à utiliser est :

```text
responsable_impression
```

Même si certaines anciennes documentations utilisent encore le terme provisoire « Éditeur de feuilles ».

---

# 15. Attribution des rôles

Créer :

```text
am.g_group_member_role
```

Alias :

```text
ggmr
```

PK :

```text
ggmr_id
```

Champs :

```text
ggmr_id
ggm_id
gr_id
created_at
```

FK :

```text
ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE CASCADE
```

FK :

```text
gr_id
    -> am.g_role.gr_id
    ON DELETE CASCADE
```

Unicité :

```text
(ggm_id, gr_id)
```

Les services métier doivent vérifier que :

```text
g_group_member.gg_id == g_role.gg_id
```

et qu'un Membre AM ne reçoit aucun rôle donnant des droits.

---

# 16. Garde-fou du dernier Responsable

Un groupe doit toujours posséder au moins un Responsable.

Il est interdit :

* de supprimer le dernier Responsable ;
* de retirer le rôle Responsable au dernier Responsable ;
* au dernier Responsable de quitter le groupe.

Ce contrôle ne doit pas être implémenté avec un simple `CHECK`, car il dépend de plusieurs lignes.

L'implémenter dans un service transactionnel Django.

Utiliser notamment :

```text
transaction.atomic()
select_for_update()
```

afin d'éviter deux retraits simultanés laissant le groupe sans Responsable.

Prévoir des tests spécifiques de concurrence logique.

---

# 17. Fonctions dans le groupe

Les fonctions ne doivent plus appartenir à `app_planning`.

Elles sont transverses et appartiennent à `app_group`.

Créer :

```text
am.g_function
```

Alias :

```text
gf
```

PK :

```text
gf_id
```

Champs :

```text
gf_id
gg_id
name
position
is_active
auto_edit_celebration
created_at
updated_at
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Prévoir une unicité insensible à la casse du nom dans un groupe.

Exemples de fonctions initiales :

```text
Chantre
Organiste
Maître de chœur
Responsable de groupe musical
```

Ces valeurs ne doivent toutefois pas devenir un enum rigide.

Chaque groupe pourra administrer sa liste et son ordre.

## `auto_edit_celebration`

Ce booléen représente la règle actuellement connue :

> lorsqu'un membre portant cette fonction est attaché à une célébration, cette fonction peut lui attribuer automatiquement le droit de modification selon la configuration du groupe.

Ne pas créer pour l'instant de moteur générique RBAC ou de permissions dynamiques.

Une V2 pourra ajouter d'autres compétences aux fonctions.

---

# 18. Fonctions possibles des membres

Créer :

```text
am.g_group_member_function
```

Alias :

```text
ggmf
```

PK :

```text
ggmf_id
```

Champs :

```text
ggmf_id
ggm_id
gf_id
created_at
```

FK :

```text
ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE CASCADE
```

FK :

```text
gf_id
    -> am.g_function.gf_id
    ON DELETE CASCADE
```

Unicité :

```text
(ggm_id, gf_id)
```

Cette table concerne :

* les Membres avec compte ;
* les Membres AM.

Une personne peut avoir plusieurs fonctions.

Les services doivent vérifier que la fonction et la personne appartiennent au même groupe.

Chaque Membre ou Membre AM actif doit normalement disposer d'au moins une fonction.

Cette règle transversale doit être contrôlée par les services et non par un simple `CHECK` SQL.

---

# 19. Lieux habituels

Les lieux habituels sont des paramètres du groupe.

Créer :

```text
am.g_location
```

Alias :

```text
gl
```

PK :

```text
gl_id
```

Champs :

```text
gl_id
gg_id
name
address
position
is_active
created_at
updated_at
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Un lieu enregistré constitue uniquement une suggestion.

Plus tard, une célébration conservera son lieu sous forme de texte et pourra utiliser un lieu libre.

Ne jamais rendre `g_location` obligatoire pour une célébration.

---

# 20. Demandes d'accès AM

Créer :

```text
am.g_access_request
```

Alias :

```text
gar
```

PK :

```text
gar_id
```

Champs minimum :

```text
gar_id
gg_id
mm_id
request_type
consented_at
consent_version
created_at
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

FK :

```text
mm_id
    -> am.m_member.mm_id
    ON DELETE CASCADE
```

`request_type` permet au minimum de distinguer :

```text
join_group
am_access
```

`join_group` :

> utilisateur ne faisant pas encore partie du groupe commun.

`am_access` :

> utilisateur déjà membre du groupe côté LSS mais demandant l'accès aux données et fonctions AM.

Une seule demande active doit exister pour un même couple :

```text
gg_id + mm_id
```

Les demandes sont des objets transitoires.

Après décision, ne pas conserver artificiellement une ligne active devenue inutile.

---

# 21. Demande de création d'un Membre AM

Créer :

```text
am.g_am_member_request
```

Alias :

```text
gamr
```

PK :

```text
gamr_id
```

Champs minimum :

```text
gamr_id
gg_id
requested_by_ggm_id
first_name
last_name
email
consent_token_hash
consent_version
status
expires_at
refused_at
display_hint
purge_at
created_at
updated_at
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

La personne ayant initié la demande est un Responsable :

```text
requested_by_ggm_id
    -> am.g_group_member.ggm_id
    ON DELETE SET NULL
```

Le `SET NULL` est volontaire :

> une demande déjà envoyée ne doit pas disparaître automatiquement simplement parce que son Responsable initiateur quitte le groupe.

## Durée

Une demande est valable :

```text
14 jours
```

## Acceptation

À l'acceptation :

1. créer `g_group_member` avec `member_kind = am` ;
2. créer `g_am_member` ;
3. créer les fonctions nécessaires ;
4. supprimer la demande temporaire.

L'adresse email en clair ne doit pas être conservée dans le Membre AM actif.

## Expiration sans réponse

Après 14 jours :

* supprimer prénom ;
* supprimer nom ;
* supprimer email ;
* supprimer la demande.

## Refus

En cas de refus :

* supprimer les données identifiantes ;
* supprimer l'email en clair ;
* conserver seulement l'indicateur pseudonymisé prévu ;
* par exemple `M***` ;
* programmer sa suppression après 14 jours maximum.

---

# 22. Fusion Membre AM vers compte CARThographie

La structure doit permettre une future fusion sans casser les historiques.

Principe :

```text
g_group_member.ggm_id
```

est l'ancre stable représentant la personne **dans le groupe**.

Lors d'une fusion :

```text
member_kind : am -> account
mm_id       : NULL -> UUID users.users.id
```

Puis supprimer :

```text
g_am_member
```

Le `ggm_id` doit rester inchangé.

Ainsi les futures tables :

* planning ;
* célébrations ;
* affectations ;

pourront conserver leur référence vers le même `ggm_id`.

Il ne faudra pas réécrire tout l'historique lors d'une fusion.

---

# 23. Tags : règle d'architecture

Les tables de tags partagées entre AM et LSS doivent être physiquement dans :

```text
common
```

Elles ne doivent **pas** être créées automatiquement par les migrations Django de `app_group`.

Le schéma `common` est partagé et doit être provisionné explicitement par SQL.

Dans Django, les éventuels modèles représentant ces tables devront être :

```python
managed = False
```

Ne pas créer une migration Django qui essaie de créer ces tables dans :

```text
am
```

---

# 24. Tags communs

Créer par SQL manuel :

```text
common.tags
```

Alias logique :

```text
tag
```

PK :

```text
tag_id
```

Champs :

```text
tag_id
name
position
is_active
created_at
updated_at
```

Le nom doit être unique de manière insensible à la casse après nettoyage des espaces.

Un tag commun :

* n'appartient à aucun groupe ;
* est visible pour tous les groupes ;
* appartient au référentiel partagé avec LSS.

Ne pas mettre de `gg_id` dans cette table.

---

# 25. Tags de groupe

Créer par SQL manuel :

```text
common.group_tags
```

Alias :

```text
gt
```

PK :

```text
gt_id
```

Champs :

```text
gt_id
gg_id
name
position
is_active
created_at
updated_at
```

FK :

```text
gg_id
    -> am.g_group.gg_id
    ON DELETE CASCADE
```

Unicité insensible à la casse :

```text
gg_id + name normalisé
```

Deux groupes différents peuvent donc avoir chacun :

```text
Kyrie
```

sans partager le même objet.

Les tags de groupe :

* sont administrés par Animation Messe ;
* appartiennent à un groupe ;
* sont stockés dans `common` car LSS doit également pouvoir les consulter.

---

# 26. Associations des tags aux chants

Ne pas mélanger cette première migration `app_group` avec toute la modélisation du répertoire de chants.

Cependant, préparer dans le SQL `common` les relations partagées suivantes si elles n'existent pas encore.

## Tag commun ↔ chant LSS

```text
common.song_tags
```

Alias :

```text
st
```

PK :

```text
st_id
```

FK :

```text
tag_id
    -> common.tags.tag_id
    ON DELETE CASCADE
```

FK :

```text
song_id
    -> lss.s_songs.song_id
    ON DELETE CASCADE
```

Unicité :

```text
(tag_id, song_id)
```

## Tag de groupe ↔ chant LSS

```text
common.group_song_tags
```

Alias :

```text
gst
```

PK :

```text
gst_id
```

FK :

```text
gt_id
    -> common.group_tags.gt_id
    ON DELETE CASCADE
```

FK :

```text
song_id
    -> lss.s_songs.song_id
    ON DELETE CASCADE
```

Unicité :

```text
(gt_id, song_id)
```

---

# 27. Tags appliqués aux blocs / couplets

La SFD exige la donnée :

```text
bloc LSS × tag du groupe -> sélection par défaut
```

Créer :

```text
common.group_verse_tags
```

Alias :

```text
gvt
```

PK :

```text
gvt_id
```

Champs :

```text
gvt_id
gst_id
verse_id
selected_by_default
```

FK :

```text
gst_id
    -> common.group_song_tags.gst_id
    ON DELETE CASCADE
```

FK :

```text
verse_id
    -> lss.s_verses.verse_id
    ON DELETE CASCADE
```

Valeur par défaut :

```text
selected_by_default = TRUE
```

Unicité :

```text
(gst_id, verse_id)
```

Le service applicatif doit vérifier que le `verse_id` appartient bien au `song_id` de `group_song_tags`.

Ne pas modifier `lss.s_verses` uniquement pour créer une contrainte composite supplémentaire.

---

# 28. Ordre de création

L'ordre attendu est :

```text
1. vérifier l'historique des migrations existantes

2. créer / corriger app_member
   am.m_member
   am.m_preferences

3. créer app_group
   am.g_group
   am.g_group_member
   am.g_am_member_title
   am.g_am_member
   am.g_role
   am.g_group_member_role
   am.g_function
   am.g_group_member_function
   am.g_location
   am.g_access_request
   am.g_am_member_request

4. exécuter le SQL partagé common
   common.tags
   common.group_tags
   common.song_tags
   common.group_song_tags
   common.group_verse_tags
```

---

# 29. Attention aux migrations `app_member` déjà présentes

Le dépôt contient déjà des migrations historiques dans `app_member`.

Elles correspondent à une ancienne conception comprenant notamment :

```text
m_preferences
m_member_roles
is_moderator
is_admin
song_search
```

Avant de les réécrire :

```text
python manage.py showmigrations app_member
```

et vérifier également la table :

```text
django_migrations
```

dans l'environnement cible.

## Si les migrations actuelles n'ont jamais été appliquées

Il est acceptable de nettoyer les migrations initiales et de repartir avec un `0001_initial.py` propre correspondant au nouveau modèle.

## Si elles ont déjà été appliquées

Ne jamais réécrire l'histoire.

Créer des migrations correctives vers le nouveau modèle.

En particulier :

* créer `m_member` ;
* transférer `is_admin` ;
* supprimer toute notion de modérateur ;
* corriger `m_preferences` ;
* supprimer ensuite l'ancienne structure devenue inutile.

La stratégie doit être sans perte de l'information `is_admin`.

---

# 30. Cascades attendues

Utiliser `CASCADE` pour les relations de possession directe.

Exemples :

```text
users.users
    CASCADE -> m_member

m_member
    CASCADE -> m_preferences

lss.g_groups
    CASCADE -> g_group

g_group
    CASCADE -> membres du groupe
    CASCADE -> rôles
    CASCADE -> fonctions
    CASCADE -> lieux
    CASCADE -> demandes
    CASCADE -> tags de groupe

g_group_member
    CASCADE -> rôles attribués
    CASCADE -> fonctions attribuées
    CASCADE -> g_am_member

g_role
    CASCADE -> attributions du rôle

g_function
    CASCADE -> attributions de fonction

group_tag
    CASCADE -> associations chant

group_song_tag
    CASCADE -> configuration des blocs
```

Utiliser `SET NULL` lorsque la disparition de l'objet secondaire ne doit pas détruire l'objet principal.

Exemple :

```text
g_am_member_title
    SET NULL -> g_am_member.gamt_id
```

ou :

```text
g_group_member
    SET NULL -> g_am_member_request.requested_by_ggm_id
```

---

# 31. Futures références historiques

Ne pas créer pour l'instant les tables de `app_planning` ou `app_celebration`.

Lorsqu'elles seront créées, elles devront pouvoir référencer :

```text
ggm_id
```

pour une personne du groupe.

Mais une suppression d'un membre ne devra pas entraîner automatiquement la destruction :

* d'une célébration ;
* d'un planning ;
* d'un déroulé ;
* d'une archive.

Prévoir plus tard selon le besoin :

```text
SET NULL
```

ou snapshots historiques.

Ne jamais utiliser un `CASCADE` destructif depuis un membre vers une célébration.

---

# 32. Matrice fonctionnelle de référence

## Administrateur du site AM

Portée :

```text
site
```

Peut administrer globalement Animation Messe.

Il n'est pas automatiquement Membre ou Responsable des groupes.

## Membre

Portée :

```text
groupe
```

Peut notamment :

* gérer son planning ;
* gérer les cellules de planning des Membres AM ;
* être affecté à une célébration ;
* modifier une célébration lorsqu'il possède le droit effectif de modification.

Il ne peut jamais valider ou dévalider une célébration simplement parce qu'il peut la modifier.

## Responsable

Portée :

```text
groupe
```

C'est un Membre avec des capacités administratives supplémentaires.

Il peut notamment :

* administrer le groupe ;
* gérer les entrées et sorties ;
* gérer les Membres AM ;
* gérer le planning selon les règles prévues ;
* intervenir sur les célébrations ;
* valider et dévalider les célébrations.

## Responsable impression

Portée :

```text
groupe
```

Rôle cumulable.

Il intervient uniquement sur les feuilles de messe après validation de la célébration.

Il n'obtient aucun droit supplémentaire sur :

* le planning ;
* le déroulé ;
* la validation.

## Membre AM

Portée :

```text
groupe
```

Aucun droit logiciel.

Il peut seulement être représenté et manipulé par les Membres et Responsables autorisés.

## Fonction

Exemples :

```text
Chantre
Organiste
Maître de chœur
Responsable de groupe musical
```

Ce n'est pas un rôle de sécurité.

Une fonction décrit la capacité habituelle de la personne dans l'équipe.

Une fonction peut néanmoins être utilisée par les règles du groupe pour déclencher certaines capacités automatiques, par exemple le droit initial de modifier une célébration lorsqu'une personne y est affectée.

---

# 33. Ce qu'il ne faut surtout pas faire

Ne pas :

* modifier `users.users` ;
* dupliquer prénom/nom/email des utilisateurs CARThographie ;
* recréer un utilisateur Django local indépendant ;
* créer un rôle `moderator` ;
* utiliser `lss.g_group_user.is_group_admin` comme rôle Responsable AM ;
* mettre les fonctions Chantre/Organiste dans `app_planning` ;
* coder les fonctions en enum rigide ;
* donner au Membre le droit de valider une célébration ;
* donner des droits applicatifs au Membre AM ;
* créer les tags partagés dans le schéma `am` ;
* laisser Django créer automatiquement les tables du schéma `common` ;
* mettre tous les paramètres du groupe dans une grosse colonne JSON ;
* créer maintenant les tables de planning et célébration ;
* utiliser des cascades susceptibles de supprimer un historique de célébration à cause de la suppression d'une personne.

---

# 34. SQL `common`

Créer dans le dépôt un fichier SQL versionné explicite, par exemple :

```text
db/common/001_am_tags.sql
```

Ce fichier doit :

* créer les tables nécessaires ;
* créer les contraintes ;
* créer les index ;
* créer les index d'unicité insensibles à la casse ;
* créer les FK ;
* prévoir les droits PostgreSQL nécessaires aux applications qui doivent lire ou écrire ces tables ;
* être suffisamment sûr pour être exécuté manuellement sur les environnements concernés.

Ne pas encapsuler cette création dans une migration Django.

Avant d'inventer des noms de rôles PostgreSQL dans les `GRANT`, inspecter les scripts/configurations DB existants du projet et reprendre les rôles réellement utilisés.

---

# 35. Modèles Django pour `common`

Si AM a besoin de modèles Django pour :

```text
common.tags
common.group_tags
common.song_tags
common.group_song_tags
common.group_verse_tags
```

ils doivent être déclarés avec :

```text
managed = False
```

Les modèles représentent une structure existante.

Ils n'en sont pas propriétaires.

Aucune migration Django ne doit générer de `CREATE TABLE`, `ALTER TABLE` ou `DROP TABLE` pour ces tables.

---

# 36. Tests minimum attendus

Ajouter des tests vérifiant au minimum :

* absence totale du rôle moderator ;
* création d'un membre AM lié à `users.users` par UUID ;
* impossibilité de créer deux appartenances account identiques dans un groupe ;
* Membre AM sans `mm_id` ;
* account avec `mm_id` obligatoire ;
* impossibilité de donner un rôle de sécurité à un Membre AM ;
* rôles Responsable et Responsable impression cumulables ;
* impossibilité de retirer le dernier Responsable ;
* plusieurs fonctions possibles pour le même membre ;
* fonctions possibles pour un Membre AM ;
* fonction et membre obligatoirement issus du même groupe ;
* unicité d'un rôle par membre ;
* unicité d'une fonction par membre ;
* rétention groupe limitée à 24 mois ;
* suppression d'un titre Membre AM mettant `gamt_id` à NULL ;
* aucun modèle Django propriétaire des tables `common`.

Tester également le SQL `common` lorsque l'environnement de tests PostgreSQL le permet.

---

# 37. Livrables

À la fin de la tâche, fournir :

1. les modèles Django mis à jour pour `app_member` ;
2. les modèles Django de `app_group` ;
3. les migrations correspondantes ;
4. les éventuels `RunSQL` nécessaires uniquement aux FK externes ;
5. le SQL versionné pour les tables `common` ;
6. les modèles `managed=False` nécessaires pour accéder à `common`, si utiles dès cette étape ;
7. les tests associés ;
8. un résumé des tables créées ;
9. un résumé clair des FK et des stratégies `CASCADE` / `SET NULL` ;
10. la liste des éventuels points impossibles à implémenter sans toucher à une structure externe.

Avant de terminer :

```text
python manage.py makemigrations --check
python manage.py migrate
python manage.py check
pytest
```

et exécuter Ruff selon la configuration actuelle du projet.

---

# 38. Principe final à conserver

La frontière architecturale doit rester :

```text
users.users
    = identité CARThographie existante et intangible

app_member
    = utilisateur global d'Animation Messe

app_group
    = personne dans un groupe
      + rôles
      + fonctions
      + paramètres durables du groupe

common
    = données réellement partagées entre applications

app_planning / app_celebration
    = exploitation concrète de ces paramètres
```

Cette séparation doit être privilégiée lorsque plusieurs solutions techniques sont possibles.
