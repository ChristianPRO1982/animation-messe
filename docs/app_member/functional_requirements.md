# app_member — Functional Requirements

`app_member` porte les données persistantes attachées à un utilisateur authentifié d’Animation Messe, une fois l’identité résolue par `app_main`.

Il ne gère ni l’identité externe, ni les rôles de groupe, ni les Membres AM.

Sources fonctionnelles principales :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/general_overview.md`

---

# 1. Rôle fonctionnel

`app_member` est responsable :

- des préférences persistantes faibles d’un membre authentifié ;
- des rôles globaux AM `moderator` et `admin` ;
- des services exposant ces rôles au reste du projet ;
- des formulaires ou services consommés par `app_main` pour l’administration globale ;
- de la recherche en lecture seule dans le répertoire externe lorsque nécessaire à l’administration globale.

`app_member` n’est pas responsable :

- de la création de comptes ;
- de la modification de `users.users` ;
- des rôles de groupe ;
- de l’appartenance à un groupe ;
- des Membres AM sans compte ;
- des consentements ;
- des préférences métier propres au planning ou aux célébrations.

---

# 2. Frontière d’identité

L’identifiant fonctionnel d’un membre authentifié est le UUID Keycloak présent dans `users.users.id`.

`app_member` peut référencer cet identifiant, mais ne doit jamais dupliquer :

- email ;
- prénom ;
- nom ;
- statut d’activation ;
- attributs Keycloak.

Ces données restent lues depuis `users.users` par `app_main`.

---

# 3. Rôles globaux AM

Les rôles globaux locaux sont :

- `moderator` ;
- `admin`.

Un `admin` est toujours implicitement `moderator`.

Ces rôles sont globaux à toute l’application AM.

Ils ne remplacent pas les rôles de groupe :

- Responsable ;
- Membre ;
- Membre AM.

Les rôles de groupe relèvent de `app_group`.

---

# 4. Permissions globales

Un administrateur global AM peut :

- gérer les rôles globaux des membres authentifiés ;
- gérer les paramètres globaux du site ;
- publier un message administrateur global ;
- hériter de toutes les permissions modérateur.

Un modérateur global AM peut :

- publier un message modérateur global ;
- disposer de pouvoirs de support transverses explicitement prévus par les apps métier.

Les pouvoirs métier concrets restent définis par les apps concernées.

Exemples :

- `app_group` définit si un modérateur global peut intervenir sur un groupe ;
- `app_celebration` définit si un modérateur global peut consulter ou débloquer une célébration ;
- `app_planning` définit si un modérateur global peut diagnostiquer une ligne de planning.

---

# 5. Préférences persistantes

Les préférences membres sont stockées dans `am.m_preferences`.

Elles doivent rester :

- faibles en sensibilité ;
- liées à un usage durable du produit ;
- justifiées fonctionnellement ;
- attachées à un utilisateur authentifié uniquement.

Les invités ne reçoivent aucune préférence persistante serveur.

Le champ `theme_slug`, s’il existe, reste un emplacement réservé.

La source runtime actuelle du thème reste le navigateur tant qu’un flux de synchronisation serveur n’est pas spécifié avec `app_main`.

Le champ `song_search`, hérité du miroir LSS, ne doit pas devenir le contrat principal d’AM.

Il peut être conservé temporairement pour compatibilité technique, mais les futures préférences AM doivent être renommées ou modélisées selon leurs vrais usages.

---

# 6. Tables fonctionnelles

Tables actuellement attendues dans le périmètre AM :

- `am.m_preferences` ;
- `am.m_member_roles`.

`am.m_member_roles` porte :

- `member_id` ;
- `is_moderator` ;
- `is_admin`.

Contraintes fonctionnelles :

- `member_id` référence l’identité externe `users.users.id` ;
- `is_admin` implique `is_moderator` ;
- retirer `moderator` retire aussi `admin` ;
- une ligne sans aucun rôle actif peut être supprimée.

---

# 7. Règles fonctionnelles

**MEMBER-ID-01** — `app_member` référence les membres authentifiés par le UUID externe `users.users.id`.

**MEMBER-ID-02** — `app_member` ne duplique pas les données d’identité du répertoire externe.

**MEMBER-ROLE-01** — Les rôles globaux locaux sont `moderator` et `admin`.

**MEMBER-ROLE-02** — `admin` implique toujours `moderator`.

**MEMBER-ROLE-03** — Les rôles globaux AM ne remplacent pas les rôles de groupe.

**MEMBER-ROLE-04** — Les rôles de groupe relèvent de `app_group`.

**MEMBER-PREF-01** — Les préférences persistantes concernent uniquement les membres authentifiés.

**MEMBER-PREF-02** — Aucune préférence serveur n’est créée pour un invité.

**MEMBER-PREF-03** — Toute nouvelle préférence persistée doit être justifiée par un usage AM durable.

**MEMBER-BOUNDARY-01** — `app_member` ne doit jamais écrire dans `users.users`.

**MEMBER-BOUNDARY-02** — Les Membres AM sans compte et leurs consentements relèvent de `app_group`.

---

# 8. Points encore à spécifier

1. liste finale des préférences persistantes réellement utiles à AM ;
2. devenir du champ hérité `song_search` ;
3. pouvoirs exacts du rôle global `moderator` dans les apps métier ;
4. éventuelle synchronisation serveur de la préférence de thème ;
5. interface cible de gestion des rôles globaux hors page compte.
