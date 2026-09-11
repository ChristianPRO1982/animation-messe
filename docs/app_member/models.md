# app_member — Modèle BDD

Ce document décrit la cible BDD minimale de `app_member` nécessaire à la
consolidation de `app_group`.

Les règles fonctionnelles sources restent :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/app_member/functional_requirements.md`
- `docs/keycloak_connexion.md`

---

# 1. Frontière

`app_member` porte uniquement les données persistantes globales attachées à un
utilisateur CARThographie authentifié dans Animation Messe.

Il ne possède pas :

- l'identité externe ;
- les groupes ;
- les rôles de groupe ;
- les Membres AM sans compte ;
- les consentements ;
- les fonctions de groupe ;
- les données de planning ou de célébration.

`users.users` reste la source de vérité des comptes. Les modèles AM ne doivent
pas recopier le prénom, le nom, l'email, le username ou l'état d'activation.

---

# 2. Convention

Toutes les tables gérées par Django pour `app_member` sont dans le schéma :

```text
am
```

Les tables utilisent le préfixe :

```text
m_*
```

Chaque table possède une PK explicite nommée selon son alias.

Une FK reprend exactement le nom de la PK référencée.

---

# 3. Table `am.m_member`

## Rôle

Cette table représente le profil global Animation Messe d'un utilisateur
CARThographie actif.

Elle ne représente pas un compte et ne remplace jamais `users.users`.

## Structure

```text
table : am.m_member
alias : mm
PK    : mm_id
```

Champs minimum :

```text
mm_id UUID
is_admin BOOLEAN
created_at
updated_at
```

## Relations

```text
mm_id
    -> users.users.id
    ON DELETE CASCADE
```

Comme `users.users` est externe au périmètre Django AM, la FK réelle peut être
créée par `RunSQL`.

## Règles

`is_admin` représente uniquement le rôle global Administrateur du site AM.

Il n'existe pas de rôle global `moderator` dans la cible AM.

Être Administrateur ne rend pas automatiquement la personne Membre ou
Responsable d'un groupe. Un Administrateur peut s'ajouter explicitement à un
groupe lorsque son intervention métier le nécessite.

---

# 4. Table `am.m_preferences`

## Rôle

Cette table porte les préférences personnelles faibles d'un membre authentifié.

## Structure

```text
table : am.m_preferences
alias : mp
PK    : mp_id
```

Champs minimum :

```text
mp_id
mm_id
theme_slug
calendar_week_start
created_at
updated_at
```

## Relations

```text
mm_id
    -> am.m_member.mm_id
    ON DELETE CASCADE
```

Un membre possède au maximum une ligne de préférences.

## Contraintes

```text
UNIQUE (mm_id)
calendar_week_start IN ('monday', 'sunday')
```

Valeur par défaut :

```text
calendar_week_start = 'monday'
```

`theme_slug` reste une préférence faible. La source runtime actuelle du thème
peut rester le navigateur tant qu'un flux de synchronisation serveur n'est pas
spécifié.

---

# 5. Héritage technique à corriger

Le dépôt contient actuellement des migrations et du code issus d'une conception
historique :

```text
am.m_member_roles
is_moderator
song_search
```

Ces éléments ne constituent plus la cible fonctionnelle AM.

Lors de la future migration BDD :

- préserver l'information `is_admin` existante ;
- supprimer toute notion de modérateur global ;
- remplacer l'ancrage direct des préférences sur `users.users` par une relation
  vers `am.m_member` ;
- retirer `song_search` si aucun besoin AM durable ne le justifie.

Si les migrations historiques n'ont jamais été appliquées dans l'environnement
cible, il est acceptable de repartir avec une migration initiale propre. Si
elles ont déjà été appliquées, créer des migrations correctives sans réécrire
l'historique.

---

# 6. Contrat fourni aux autres apps

`app_group` peut dépendre de :

- `am.m_member.mm_id` pour représenter un utilisateur CARThographie dans un
  groupe ;
- `am.m_member.is_admin` pour les pouvoirs globaux de support et
  d'administration ;
- `am.m_preferences.calendar_week_start` pour l'affichage personnel du
  calendrier.

`app_group`, `app_planning` et `app_celebration` ne doivent pas lire un rôle
global autre que l'Administrateur AM.
