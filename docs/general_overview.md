# Vue générale de la documentation fonctionnelle

Ce document est le point d’entrée à lire au début d’une nouvelle conversation Codex sur Animation Messe.

Il résume l’état des SFD, l’ordre de lecture recommandé et les décisions transverses déjà arbitrées. Il ne remplace pas les SFD : en cas de doute, lire le document métier concerné avant de modifier le code ou la documentation.

---

# 1. Corpus disponible

> SFD : Spécifications fonctionnelles détaillées.

Les documents actuels sont :

- `docs/SFD-01-groupes_et_membres.md` — groupes, rôles, accès, Membres AM, consentement, usages publics.
- `docs/SFD-02-planning.md` — calendrier, génération du planning, disponibilités, fonctions, validation du planning.
- `docs/SFD-03-chants.md` — relation AM/LSS, recueils, tags, structure des chants, synchronisation, suppressions.
- `docs/SFD-04-celebrations.md` — célébrations, déroulé, blocs chants/textes, AELF, validation, feuilles, archivage, partage.

Ces SFD constituent la base fonctionnelle à partir de laquelle les documents techniques doivent être produits.

Les exigences fonctionnelles par app Django sont :

- `docs/app_main/functional_requirements.md` — socle partagé, authentification, session, paramètres globaux.
- `docs/app_member/functional_requirements.md` — membre authentifié, préférences faibles, rôles globaux.
- `docs/app_group/functional_requirements.md` — groupes, rôles de groupe, Membres AM, recueil et tags.
- `docs/app_celebration/functional_requirements.md` — célébrations, déroulé, AELF, validation, feuilles.
- `docs/app_planning/functional_requirements.md` — planning dérivé des célébrations, cellules, fonctions, validation planning.

Les contrats BDD consolidés par app Django sont :

- `docs/app_member/models.md` — profil global AM, préférences, rôle Administrateur, héritage technique à corriger.
- `docs/app_group/models.md` — groupes, membres, rôles, fonctions, paramètres planning, recueil chants et contrats vers les apps métier.
- `docs/app_celebration/models.md` — célébrations, cellules planning, déroulé, AELF, gabarits, feuilles et validations.
- `docs/app_planning/models.md` — contrat de non-possession BDD, services planning et interfaces vers `app_group` et `app_celebration`.

Les contrats techniques transverses déjà disponibles sont :

- `docs/keycloak_connexion.md` — authentification Keycloak, session AM, provisioning, diagnostics.
- `docs/popup_messagebox.md` — API popup globale `window.LSSMessageBox` utilisée dans AM.
- `docs/wiki_help_mapping.md` — mapping entre routes Django et pages du wiki Animation Messe.
- `docs/pj_codex_block_naming.md` — vocabulaire stable pour désigner les blocs de page dans les échanges Codex.

---

# 2. Ordre de lecture recommandé

Pour comprendre le modèle global :

1. Lire `SFD-01-groupes_et_membres.md` pour les rôles, permissions de base et contraintes RGPD.
2. Lire `SFD-04-celebrations.md` pour l’objet métier central et son cycle de vie.
3. Lire `SFD-02-planning.md` pour comprendre comment le planning est dérivé des célébrations.
4. Lire `SFD-03-chants.md` pour la frontière entre Lyrics Slide Show et Animation Messe.

Pour concevoir une fonctionnalité technique :

- commencer par la SFD du module concerné ;
- lire ensuite le `functional_requirements.md` de l’app Django concernée ;
- vérifier ensuite les SFD transverses impactées ;
- chercher les règles identifiées par préfixe ;
- vérifier les points encore à spécifier avant d’inventer une règle.

---

# 3. Décisions transverses à conserver

Les décisions suivantes sont déjà arbitrées et doivent guider les futures conceptions techniques.

## 3.1. Objet métier canonique

Le terme métier canonique est **célébration**.

Une ligne de planning correspond à une célébration existante.

Le mot **animation** peut encore apparaître comme terme d’usage, notamment dans :

- fonction d’animation ;
- animation publique anonyme ;
- certains libellés historiques de planning.

Il ne doit pas être modélisé comme une entité concurrente de la célébration.

## 3.2. Deux validations distinctes

La **validation du planning** fige les cellules de célébration utilisées par le planning. Elle ne copie pas les personnes sélectionnées vers une seconde équipe séparée.

La **validation de célébration** verrouille le déroulé et déclenche la génération des feuilles de messe.

Ces deux validations ne doivent pas être fusionnées techniquement.

## 3.3. Relation entre AM et LSS

Lyrics Slide Show est la source de vérité des chants.

Animation Messe conserve la manière dont un groupe utilise ces chants :

- recueil du groupe ;
- tags de groupe ;
- sélection de blocs/couplets ;
- occurrences dans une célébration.

La suppression d’un chant LSS suit une règle hybride :

- le chant est retiré des usages courants AM et des sélections futures ;
- les blocs déjà présents dans des célébrations existantes sont conservés comme références cassées signalées ;
- les feuilles déjà générées restent exploitables si elles contiennent leur propre texte final.

## 3.4. Données personnelles et Membres AM

Un Membre AM représente une personne réelle sans compte CARThographie.

Il peut être affecté à des plannings ou célébrations, mais ne possède aucun droit applicatif.

Les règles de consentement, retrait, secret personnel et minimisation RGPD de `SFD-01` doivent être relues avant toute conception touchant aux personnes sans compte.

---

# 4. Identifiants de règles

Les SFD utilisent des identifiants de règles pour faciliter la conception technique et les tests.

- `GRP-*` — groupes, membres, rôles, accès, consentement, usages publics.
- `PLAN-*` — planning, génération, cellules, fonctions, validation du planning.
- `CHANT-*` — chants, LSS, recueils, tags, synchronisation, références cassées.
- `CELEB-*` — célébrations, déroulé, AELF, validation, archivage, feuilles.

Lorsqu’une règle technique est créée, elle doit autant que possible pointer vers un ou plusieurs identifiants SFD.

---

# 5. Points ouverts

Chaque SFD contient une section de points encore à spécifier.

Ces points ne sont pas des détails éditoriaux : certains bloquent volontairement une conception technique complète.

Avant d’implémenter une fonctionnalité touchant un point ouvert :

1. relire la section correspondante ;
2. vérifier si une autre SFD a déjà tranché le sujet ;
3. demander un arbitrage fonctionnel si la règle reste absente ;
4. mettre à jour la SFD avant ou pendant la conception technique.

---

# 6. Contrôles utiles pour Codex

Commandes utiles après modification documentaire :

```bash
rg -n "^#" docs/SFD-*.md docs/general_overview.md
rg -n "GRP-|PLAN-|CHANT-|CELEB-" docs/SFD-*.md
rg -n "animation|célébration|validation|suppression.*LSS|référence.*cassée|Membre AM|RGPD" docs/SFD-*.md
git diff --check
```

Pour vérifier spécifiquement la politique LSS hybride :

```bash
rg -n "CHANT-DEL|CELEB-CHANT-04|référence.*cassée|ne sont pas supprim|ne supprime pas automatiquement" docs/SFD-03-chants.md docs/SFD-04-celebrations.md
```

---

# 7. Règle de travail

Ne pas créer de document technique à partir d’une seule SFD si le sujet touche :

- aux rôles ou permissions ;
- à une célébration ;
- au planning ;
- aux chants LSS ;
- aux données personnelles ;
- à l’archivage ou à la purge.

Dans ces cas, croiser au minimum la SFD du module avec `SFD-01-groupes_et_membres.md` et `SFD-04-celebrations.md`.
