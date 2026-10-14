# Email — Functional Requirements

Le module email porte les e-mails transactionnels et les e-mails de vie métier
d'Animation Messe.

En V1, le module fournit la mécanique transversale mais ne branche aucun
déclencheur métier automatique dans les autres apps Django.

Sources fonctionnelles principales :

- `docs/SFD-01-groupes_et_membres.md`
- `docs/SFD-02-planning.md`
- `docs/SFD-04-celebrations.md`
- `docs/app_group/functional_requirements.md`
- `docs/app_planning/functional_requirements.md`
- `docs/app_celebration/functional_requirements.md`

Contrat technique cible :

- `docs/email/models.md`

---

# 1. Rôle fonctionnel

Le module email est responsable :

- de préparer les e-mails nécessaires au fonctionnement du service ;
- de déterminer les destinataires à partir des règles métier Django ;
- de rendre les sujets et contenus depuis des templates Django ;
- de déclencher l'envoi via une couche technique dédiée ;
- de tracer l'état minimal de chaque notification ;
- d'éviter les doubles envois involontaires ;
- de respecter la minimisation des données personnelles.

Le module email n'est pas responsable :

- de l'authentification ;
- de la possession des groupes, membres, plannings ou célébrations ;
- d'une newsletter ou d'un outil marketing ;
- du suivi d'ouverture ou de clic ;
- d'un moteur générique de workflow ;
- de la synchronisation directe avec n8n.

---

# 2. Types d'e-mails

Les e-mails d'Animation Messe sont des e-mails de service. Ils doivent être
liés à une action utilisateur, une règle métier ou un état important du système.

Familles minimales prévues :

- groupes et accès ;
- Membres AM et consentement ;
- planning ;
- célébrations ;
- feuilles et documents générés ;
- compte et sécurité ;
- information réglementaire importante.

Chaque type d'e-mail doit avoir :

- un identifiant stable ;
- une finalité claire ;
- une liste de destinataires déterminée par Django ;
- un niveau d'urgence ou de criticité si nécessaire ;
- une règle d'idempotence lorsque le double envoi serait nuisible ;
- des templates dédiés.

---

# 3. Groupes et accès

Le module email peut envoyer des e-mails liés aux groupes, par exemple :

- invitation à rejoindre un groupe ;
- information après acceptation d'une demande de rattachement ;
- information après attribution ou retrait d'un accès AM ;
- notification d'un changement important concernant le rôle d'un membre ;
- confirmation d'une action sensible réalisée par un Responsable.

Ces e-mails ne doivent pas créer de droit par eux-mêmes.

Les droits réels restent portés par les tables et services métier :

- `common.g_group_user` ;
- `common.g_group_user.am_access` ;
- `common.g_group_user.is_group_admin` ;
- `am.g_group_member` ;
- les services de `app_group`.

---

# 4. Membres AM et consentement

La création d'un Membre AM nécessite un e-mail d'information et de consentement.

Cet e-mail peut contenir :

- l'identité du groupe concerné ;
- le prénom et le nom saisis pour la personne invitée ;
- le texte de consentement applicable ou un lien vers sa version ;
- un lien ou secret personnel de validation ;
- une date d'expiration ;
- une explication claire sur le retrait possible.

Le secret personnel ne doit jamais être loggé.

Après acceptation, refus, expiration ou retrait, l'e-mail en clair doit être
conservé uniquement selon les règles de minimisation prévues par `app_group`.

---

# 5. Planning

Le module email doit pouvoir porter des e-mails de vie métier liés au planning.

Exemples :

- envoi du planning personnel d'une personne ;
- rappel d'une affectation future ;
- notification de changement d'état d'une cellule de planning ;
- information après validation du planning ;
- information après dévalidation ou modification importante ;
- demande de disponibilité pour une période donnée.

Un planning personnel ne doit contenir que les informations nécessaires au
destinataire.

Par défaut, il ne doit pas divulguer inutilement :

- les données personnelles des autres membres ;
- les indisponibilités détaillées d'autres personnes ;
- des informations internes au groupe sans besoin fonctionnel.

Lorsqu'un e-mail concerne une célébration précise, il doit privilégier les
informations utiles à l'action du destinataire :

- date ;
- heure ;
- lieu ;
- fonction prévue ;
- état ou consigne nécessaire.

---

# 6. Célébrations et documents

Le module email peut envoyer des e-mails liés aux célébrations, par exemple :

- notification de validation d'une célébration ;
- information après modification importante du déroulé ;
- confirmation de génération ou disponibilité d'une feuille ;
- demande de relecture ;
- information sur une célébration annulée ou déplacée.

La validation du planning et la validation de célébration restent deux
événements distincts. Les e-mails doivent respecter cette distinction.

---

# 7. Comptes et sécurité

Les e-mails liés aux comptes restent des e-mails de service.

Exemples :

- information sur une modification importante des conditions d'utilisation ;
- relance avant suppression d'un compte inactif ;
- confirmation de suppression ;
- notification de changement de politique de confidentialité.

Les e-mails d'authentification ou de récupération de mot de passe restent sous
la responsabilité du système d'identité concerné si Keycloak les porte déjà.

Animation Messe ne doit pas dupliquer inutilement ces flux.

---

# 8. Cycle de vie d'une notification

Un événement métier suit le flux fonctionnel suivant :

```text
événement métier
-> décision Django de notifier ou non
-> création ou réutilisation d'une notification
-> rendu des templates
-> tentative d'envoi
-> mise à jour du statut
-> log technique minimal
```

Une erreur d'envoi ne doit pas corrompre l'opération métier principale.

Exemple : la validation d'un planning doit pouvoir réussir même si le provider
email est temporairement indisponible. L'échec d'envoi est alors tracé.

---

# 9. Idempotence

Le système doit éviter les doubles envois involontaires.

Pour les notifications importantes, une clé métier doit permettre de retrouver
une notification déjà créée.

Exemples de clé métier :

```text
type + groupe + objet métier + destinataire
type + célébration + membre
type + période planning + membre
```

La règle ne doit pas empêcher un renvoi volontaire.

Un renvoi volontaire doit être une nouvelle notification ou un nouvel essai
explicitement tracé selon le cas métier.

---

# 10. Confidentialité

Les e-mails doivent appliquer la minimisation RGPD.

Ils ne doivent contenir que les données nécessaires à leur finalité.

Le sujet d'un e-mail ne doit pas contenir de donnée sensible ou inutilement
personnelle.

Les logs ne doivent jamais contenir :

- mot de passe ;
- token ;
- secret personnel ;
- lien complet contenant un secret ;
- contenu complet d'un e-mail contenant des données personnelles.

Le modèle de notification ne doit pas stocker le corps complet du message par
défaut.

---

# 11. Administration

Une visualisation minimale peut être disponible dans Django Admin.

En V1, cette visualisation est fournie par Django Admin.

Elle permet de consulter :

- type ;
- destinataire ;
- groupe concerné ;
- objet métier concerné ;
- statut ;
- date de création ;
- date d'envoi ;
- erreur éventuelle.

Elle ne doit pas être un éditeur complexe d'e-mails.

---

# 12. Hors périmètre V1

La première version ne doit pas mettre en place :

- Celery ;
- Redis ;
- queue distribuée ;
- retry complexe ;
- provider Outlook spécifique ;
- Microsoft Graph ;
- OAuth Outlook ;
- synchronisation n8n ;
- connexion directe n8n vers PostgreSQL ;
- moteur générique de workflow ;
- newsletter ;
- e-mails marketing ;
- tracking d'ouverture ;
- tracking de clic ;
- éditeur visuel de templates.

---

# 13. Règles fonctionnelles

**EMAIL-CORE-01** — Les e-mails transactionnels simples sont déclenchés par
Django.

**EMAIL-CORE-02** — Les apps métier n'appellent jamais directement le provider
email.

**EMAIL-CORE-03** — Le provider réel est masqué derrière un service Django.

**EMAIL-TRACE-01** — Chaque notification envoyable possède une trace minimale.

**EMAIL-TRACE-02** — Une erreur d'envoi est enregistrée sans rollback
indésirable de l'opération métier principale.

**EMAIL-IDEMP-01** — Les notifications importantes disposent d'une stratégie
d'idempotence.

**EMAIL-TEMPLATE-01** — Les sujets et corps d'e-mails sont rendus depuis des
templates Django.

**EMAIL-RGPD-01** — Les e-mails ne contiennent que les données nécessaires.

**EMAIL-RGPD-02** — Les secrets et tokens ne sont jamais loggés.

**EMAIL-PLANNING-01** — Le système peut envoyer un planning personnel à une
personne.

**EMAIL-PLANNING-02** — Un planning personnel ne divulgue pas inutilement les
données des autres membres.

**EMAIL-N8N-01** — n8n ne lit pas directement PostgreSQL pour déterminer les
e-mails à envoyer.

**EMAIL-V1-01** — La V1 fournit l'infrastructure email sans déclencheur métier
automatique.

**EMAIL-ADMIN-01** — La V1 expose les notifications dans Django Admin.

**EMAIL-OUTLOOK-01** — Outlook reste hors implémentation spécifique en V1.

---

# 14. Points encore à spécifier

1. Provider de production retenu : SMTP, Brevo, Mailjet, Resend, SES ou autre.
2. Politique exacte de retry manuel ou automatique.
3. Catalogue final des types d'e-mails V1.
4. Préférences utilisateur éventuelles pour certains rappels non critiques.
5. Format exact des e-mails de planning personnel.

