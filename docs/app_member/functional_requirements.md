# app_member — Functional Requirements

`app_member` porte les données persistantes attachées à un utilisateur authentifié d’Animation Messe, une fois l’identité résolue par `app_main`.

Il ne gère ni l’identité externe, ni les rôles de groupe, ni les Membres AM.

Sources fonctionnelles principales :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/general_overview.md`

Contrat BDD cible :

- `docs/app_member/models.md`

---

# 1. Rôle fonctionnel

`app_member` est responsable :

- du profil global AM d’un utilisateur CARThographie ;
- des préférences persistantes faibles d’un membre authentifié ;
- du rôle global Administrateur du site AM ;
- des services exposant ce rôle au reste du projet ;
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

# 3. Rôle global AM

Le seul rôle global local cible est :

- Administrateur du site AM.

Ce rôle est stocké comme `is_admin` dans le modèle BDD cible.

Il n’existe aucun rôle global de modération dans Animation Messe.

Le rôle Administrateur ne remplace pas les rôles de groupe :

- Responsable ;
- Membre ;
- Membre AM.

Les rôles de groupe relèvent de `app_group`.

---

# 4. Permissions globales

Un Administrateur global AM peut :

- gérer les profils globaux AM ;
- gérer les paramètres globaux du site ;
- publier un message administrateur global ;
- créer, administrer ou supprimer des groupes selon les règles de `SFD-01` ;
- se nommer explicitement Responsable d’un groupe pour intervenir dans son fonctionnement.

Être Administrateur ne rend pas automatiquement la personne :

- Membre d’un groupe ;
- Responsable d’un groupe ;
- participant au planning ;
- membre d’une célébration.

Les pouvoirs métier concrets restent définis par les apps concernées.

---

# 5. Préférences persistantes

Les préférences membres sont stockées dans `am.m_preferences`.

Elles doivent rester :

- faibles en sensibilité ;
- liées à un usage durable du produit ;
- justifiées fonctionnellement ;
- attachées à un utilisateur authentifié uniquement.

Les invités ne reçoivent aucune préférence persistante serveur.

Le modèle cible prévoit au minimum :

- `theme_slug` ;
- `calendar_week_start`.

La source runtime actuelle du thème peut rester le navigateur tant qu’un flux de synchronisation serveur n’est pas spécifié avec `app_main`.

Les anciennes préférences héritées de LSS ne doivent pas devenir le contrat principal d’AM.

---

# 6. Tables fonctionnelles cibles

Tables attendues dans le périmètre AM :

- `am.m_member` ;
- `am.m_preferences`.

`am.m_member` référence `users.users.id` par `mm_id` et porte `is_admin`.

`am.m_preferences` référence `am.m_member.mm_id` et porte les préférences faibles.

Le détail des champs, contraintes et relations est défini dans `docs/app_member/models.md`.

---

# 7. Héritage technique

Le dépôt contient encore une structure historique héritée de LSS :

- table de rôles globale séparée ;
- rôle de modération ;
- préférence de recherche de chants.

Ces éléments doivent être traités comme des artefacts de migration à corriger lors de la future passe BDD. Ils ne constituent plus la cible fonctionnelle d’Animation Messe.

Toute migration corrective devra préserver l’information Administrateur existante.

---

# 8. Règles fonctionnelles

**MEMBER-ID-01** — `app_member` référence les membres authentifiés par le UUID externe `users.users.id`.

**MEMBER-ID-02** — `app_member` ne duplique pas les données d’identité du répertoire externe.

**MEMBER-ROLE-01** — Le seul rôle global AM cible est Administrateur du site.

**MEMBER-ROLE-02** — Les rôles globaux AM ne remplacent pas les rôles de groupe.

**MEMBER-ROLE-03** — Les rôles de groupe relèvent de `app_group`.

**MEMBER-PREF-01** — Les préférences persistantes concernent uniquement les membres authentifiés.

**MEMBER-PREF-02** — Aucune préférence serveur n’est créée pour un invité.

**MEMBER-PREF-03** — Toute nouvelle préférence persistée doit être justifiée par un usage AM durable.

**MEMBER-BOUNDARY-01** — `app_member` ne doit jamais écrire dans `users.users`.

**MEMBER-BOUNDARY-02** — Les Membres AM sans compte et leurs consentements relèvent de `app_group`.

---

# 9. Points encore à spécifier

1. liste finale des préférences persistantes réellement utiles à AM hors `theme_slug` et `calendar_week_start` ;
2. éventuelle synchronisation serveur de la préférence de thème ;
3. interface cible de gestion des profils globaux hors page compte ;
4. stratégie exacte de migration si les migrations historiques `app_member` ont déjà été appliquées.
