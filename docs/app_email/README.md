# Email — Vue générale

Ce dossier décrit le système cible d'envoi d'e-mails d'Animation Messe.

L'objectif est de permettre à Django d'envoyer les e-mails transactionnels et
les e-mails de vie métier de l'application, sans dépendre de n8n pour les cas
simples.

La V1 implémentée cible l'infrastructure seulement : modèle de notification,
service d'envoi, rendu des templates, configuration et consultation Django
Admin. Aucun déclencheur métier n'est encore branché automatiquement dans
`app_group`, `app_planning` ou `app_celebration`.

Les e-mails ne sont pas limités à l'administration du site. Ils couvrent aussi
les interactions ordinaires entre les groupes, les membres, le planning et les
célébrations : invitation d'un Membre AM, envoi d'un planning personnel,
notification d'une modification de célébration, confirmation d'une action
importante, etc.

---

# 1. Documents

- [Guide d'utilisation inter-apps](usage.md) — à lire avant d'ajouter un envoi :
  appels, templates, idempotence, transactions, configuration et tests.
- [Raccordement Brevo](brevo.md) — secret SMTP hors dépôt, Docker local,
  double autorisation et procédure de test contrôlé.
- `docs/app_email/functional_requirements.md` — règles fonctionnelles, familles
  d'e-mails, confidentialité, idempotence et périmètre.
- `docs/app_email/models.md` — contrat technique cible, modèle de notification,
  service d'envoi, templates, configuration et tests.

---

# 2. Décision d'architecture

Django est propriétaire :

- des règles métier déclenchant un e-mail ;
- du choix des destinataires ;
- du contenu fonctionnel ;
- de l'état de la notification ;
- de la traçabilité minimale.

n8n ne doit pas interroger directement PostgreSQL pour déterminer les e-mails à
envoyer.

n8n pourra être utilisé plus tard pour des workflows complexes, différés ou
planifiés, mais les e-mails transactionnels simples doivent rester dans Django.

Le provider Outlook n'est pas implémenté en V1. Il pourra être utilisé plus
tard via une configuration SMTP standard ou via un adapter dédié.

---

# 3. Principe de non-couplage

Les apps métier ne doivent pas appeler directement `send_mail()` ou un provider
SMTP/API.

Elles doivent appeler un service applicatif central, par exemple :

```text
app_email.services
```

ou une organisation équivalente explicitement documentée.

Le provider d'envoi doit pouvoir évoluer sans modifier les services métier :

```text
app_group / app_planning / app_celebration
    -> service email Django
        -> backend Django email
            -> SMTP ou provider API
```

