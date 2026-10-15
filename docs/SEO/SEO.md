# Consignes Codex — transposer le socle SEO de Lyrics Slide Show

## Objet et portée

Ce document est destiné à être copié à la racine d'un projet frère de Lyrics Slide Show (LSS). Il explique comment reprendre sa politique SEO et les principes de sa refonte front dans un autre dépôt Django, même si seuls certains templates sont communs.

Codex : commence par lire la documentation et les templates du dépôt destinataire. Identifie les pages publiques, les pages métier, les permissions, les routes et le template de base avant de modifier le code. Applique les règles ci-dessous aux équivalents locaux ; les chemins LSS cités sont des repères dans le dépôt source, pas la preuve que ces fichiers existent dans le dépôt destinataire.

Le but est un socle SEO simple, explicite et maintenable. Préserve les URL publiques existantes, l'authentification, les permissions, les recherches et les usages métier. Adapte la marque, le domaine, les textes, les noms de routes et les données structurées au produit destinataire.

## Documents Markdown à copier avec ce fichier

Les chemins suivants sont relatifs à la racine du dépôt LSS. Conserve-les si possible dans la copie, ou indique leur nouvel emplacement à Codex.

| Document source | Copie | Utilité dans le projet destinataire |
| --- | --- | --- |
| [docs/SEO.md](docs/SEO.md) | À copier | Contrat SEO détaillé de LSS : indexation, canonical, catalogue, sitemap, robots et tests. Ses routes et formulations restent des exemples LSS à adapter. |
| [docs/pj_codex_block_naming.md](docs/pj_codex_block_naming.md) | À copier | Vocabulaire du nouveau front et correspondance entre panneaux visibles, blocs Django et classes CSS. |
| [docs/app_main/template_04.homepage.html.md](docs/app_main/template_04.homepage.html.md) | Si l'accueil est repris | Structure de l'accueil, contenu éditorial, cartes et rendu Markdown côté serveur. |
| [docs/app_song/template_10.song_catalogue.html.md](docs/app_song/template_10.song_catalogue.html.md) | Si un catalogue de chants est repris | Contrat du catalogue public HTML, pagination et canonical. |
| [docs/app_song/template_02.song.html.md](docs/app_song/template_02.song.html.md) | Si la fiche chant est reprise | Séparation du H1, des marqueurs métier, du résumé et des actions. |

Ce guide contient les règles essentielles pour démarrer. Les deux premières copies donnent à Codex les contrats de référence complets ; les trois autres servent uniquement pour les templates concernés. Aucun autre fichier Markdown externe à ce guide n'est nécessaire à sa compréhension.

Dans LSS, `docs/SEO.md` reste la source de vérité SEO : ce fichier racine est un guide de transfert. Dans le dépôt destinataire, documente la politique adaptée dans un emplacement de référence unique, avec la liste réelle des pages indexables de ce produit.

## 1. Indexation explicite et accès métier

- Toute page HTML est `noindex, follow` par défaut.
- Seules les pages publiques explicitement choisies passent à `index, follow`.
- Une nouvelle page reste donc non indexable tant qu'aucune décision explicite ne l'expose.
- L'accessibilité anonyme ne suffit pas à rendre une page indexable : une interface de travail, de projection ou de télécommande peut être publique et rester `noindex`.
- Une page indexable doit offrir son contenu public utile sans connexion, groupe sélectionné, secret ni préférence privée préalable.
- Les permissions restent appliquées côté serveur. `noindex` et `robots.txt` ne remplacent jamais un contrôle d'accès.

Laisse hors index les comptes, préférences, formulaires de création/modification, outils d'administration et de modération, callbacks SSO, provisioning, diagnostics, workflows d'animation, projection et télécommandes. Les endpoints techniques ne doivent pas être ajoutés au sitemap.

Établis dans le projet frère un tableau par famille de routes : accès anonyme, indexation, canonical et présence au sitemap. Ne recopie pas automatiquement la liste blanche LSS.

### Liste de référence LSS

| Page LSS | Robots | Canonical | Sitemap |
| --- | --- | --- | --- |
| `/` | `index, follow` | URL propre | Oui |
| `/groups/`, `/login/`, `/privacy-policy/` | `index, follow` | URL propre | Oui |
| `/songs/catalogue/` | `index, follow` | URL propre | Oui |
| `/songs/catalogue/?page=N`, N > 1 | `index, follow` | URL de cette page, avec `?page=N` | Non |
| `/songs/<song_id>/`, chant non licencié | `index, follow` | URL propre du chant | Oui |
| `/songs/`, avec ou sans filtres | `noindex, follow` | `/songs/` sans paramètres | Non |
| Pages métier, privées et techniques | `noindex, follow` pour les pages HTML | Normalement absente | Non |

Dans LSS, le critère de publicité d'un chant est `licensed=False`, indépendamment de sa validation. Dans un autre produit, utilise ses propres règles d'accès anonyme ; ne déduis pas la publicité d'un contenu de son seul statut de validation.

## 2. Centraliser les métadonnées

Référence de code LSS : `app_main/seo.py` et `templates/base.html`.

Prévois un helper commun pour construire le contexte SEO et un rendu commun dans le `<head>`. Évite les variantes de balises recopiées dans chaque page.

Contrat de contexte utilisé par LSS :

| Variable | Rôle |
| --- | --- |
| `seo_title` | Titre de l'onglet et titre SEO |
| `seo_description` | Meta description |
| `seo_robots` | `noindex, follow` par défaut, `index, follow` sur décision explicite |
| `seo_canonical_url` | URL canonique absolue, si applicable |
| `seo_og_title`, `seo_og_description`, `seo_og_url` | Métadonnées de partage |
| `seo_og_type`, `seo_site_name` | Type Open Graph et nom du produit |
| `seo_json_ld` | JSON-LD sérialisé côté serveur, si applicable |

Le helper LSS `seo_context(..., index=False)` impose un choix explicite pour l'indexation. Il accepte aussi un chemin ou une canonical ; il faut donc vérifier leur cohérence avec `index`, pas supposer que le helper le fait automatiquement.

Le template de base doit assurer le fallback même lorsqu'aucun contexte SEO n'est fourni :

```django
<title>{% block title %}{{ seo_title|default:product_name }}{% endblock %}</title>
<meta name="description" content="{{ seo_description|default:'' }}">
<meta name="robots" content="{{ seo_robots|default:'noindex, follow' }}">
{% if seo_canonical_url %}
  <link rel="canonical" href="{{ seo_canonical_url }}">
{% endif %}
```

Cet extrait est indicatif : `product_name` doit être fourni par le projet destinataire. Les templates enfants qui surchargent `title` doivent respecter `seo_title` lorsqu'il existe. Vérifie le HTML final pour éviter les balises title, description, robots ou canonical en double.

**Templates autonomes :** inspecte toutes les pages qui n'étendent pas `base.html`, notamment projection, lecture mobile et télécommande. Elles ne reçoivent pas son fallback. Ajoute un contrat commun de `<head>` ou une balise robots explicite selon leur politique. L'absence d'une URL dans le sitemap ne la rend pas non indexable.

## 3. URL canoniques

- Utilise une base canonique de production configurée explicitement, propre au produit destinataire.
- Dans LSS, la configuration est `LSS_CANONICAL_BASE_URL`, avec `https://lss.carthographie.fr` comme valeur par défaut. Remplace ces références dans le projet frère.
- Construis les chemins via les routes Django (`reverse`) puis les URL absolues via un helper commun.
- Les canonical des pages indexables doivent être absolues et en HTTPS.
- Écarte de la canonical les paramètres de recherche, de suivi et de préférence qui ne définissent pas une page éditoriale distincte.
- Une page paginée indexable conserve sa propre canonical avec son numéro de page ; elle ne pointe pas systématiquement vers la première page.
- Une page `noindex` ne reçoit normalement pas de canonical. L'exception LSS est la recherche interactive `/songs/`, canonicalisée vers sa racine sans paramètres.
- Ne crée pas de slugs ni de nouvelles routes uniquement pour ce transfert SEO.

Contrôle que la configuration ne produit ni domaine LSS résiduel, ni URL localhost, ni URL HTTP en production. Le helper LSS ne force pas à lui seul le schéma HTTPS : vérifie la configuration et le résultat rendu.

## 4. Structure du front et contenu visible

La refonte LSS sépare les outils de navigation du contenu principal. Reprends cette organisation lorsque les templates sont communs, en t'appuyant sur la nomenclature copiée.

| Zone visible | Blocs Django LSS | Rôle |
| --- | --- | --- |
| Panneau section | `section_title`, `section_intro`, `section_nav` | Repères et navigation locale |
| Panneau outils | `tools_title`, `tools_intro`, `page_tools` | Actions et raccourcis |
| Panneau mobile | `mobile_side_title`, `mobile_side_intro`, `mobile_side_visual`, `mobile_side_content` | Présentation et actions adaptées aux petits écrans |
| En-tête principal | `page_kicker`, `page_title`, `page_intro` | Contexte, H1 et introduction |
| Encadré résumé | `page_summary` | Synthèse et informations complémentaires |
| Contenu principal | `content` | Contenu utile de la page |
| Pied de contenu | `content_footer` | Complément facultatif |

Le panneau principal englobe l'en-tête, le résumé, le contenu et son pied. Les noms de blocs sont des conventions de réutilisation ; les classes CSS et la disposition visuelle ne constituent pas à elles seules une politique SEO.

Règles de structure à appliquer :

- Un seul H1 principal, descriptif et visible, porté par `page_title` lorsque la page utilise le shell commun.
- Un titre HTML SEO et un H1 peuvent différer : le title précise le sujet et le produit ; le H1 nomme le contenu visible.
- Les sections et cartes utilisent une hiérarchie cohérente de H2/H3. Le niveau de titre dépend du sens, pas de la taille typographique souhaitée.
- Le contexte court peut aller dans `page_kicker`, l'explication dans `page_intro`, les informations secondaires dans `page_summary`.
- Les badges de validation, favoris, licence et autres marqueurs métier restent hors du H1.
- Préserve les éléments sémantiques du shell : navigation, `<main>`, sections et liens avec libellés compréhensibles.
- Le contenu public utile et les liens d'exploration sont rendus dans le HTML Django initial. Ils ne dépendent pas d'un clic, d'une popup ou d'un appel JavaScript pour exister.
- Utilise de vrais `<a href="…">` pour la navigation et la pagination ; réserve les boutons aux actions.
- Vérifie les variantes desktop/mobile : elles ne doivent pas introduire un second H1 ni retirer le contenu principal sur petit écran.
- Si un loader est repris, conserve le contenu rendu serveur et un mécanisme de sortie en cas d'échec du chargement. Vérifie aussi la lecture sans JavaScript.

À l'accueil, présente clairement le service avec un H1 et des textes utiles ; les cartes peuvent porter des H2. Si tu reprends le mini-Markdown LSS, conserve l'échappement du HTML d'entrée et la validation des URL. Le SEO ne justifie pas de rendre du HTML administrable brut avec `safe`.

## 5. Séparer recherche interactive et catalogue public

Si le projet frère propose la même recherche de chants, conserve la distinction LSS :

- La recherche `/songs/` sert les utilisateurs, conserve ses filtres et reste `noindex, follow`, y compris sans paramètres.
- Ses variantes GET gardent une canonical vers `/songs/` sans paramètres.
- Le catalogue `/songs/catalogue/` sert l'exploration publique : liste légère rendue serveur, indexable, sans recherche personnalisée ni dépendance à la session.

Contrat du catalogue LSS à reprendre si cette fonctionnalité existe :

- Seulement les chants accessibles anonymement ; dans LSS, `licensed=False`.
- Pagination fixe de 50 chants, tri stable par `title`, `subtitle`, `song_id`.
- Vrais liens HTML vers les fiches et entre les pages ; pagination en haut et en bas de la liste.
- Pas de chargement JavaScript obligatoire de la liste, ni de paroles complètes ou de descriptions longues dans le catalogue.
- `?page=1` redirige en 301 vers l'URL du catalogue sans paramètres.
- Numéro invalide, inférieur à 1 ou hors plage : vraie réponse HTTP 404, sans retour silencieux à la dernière page ni redirection vers l'accueil.
- Pages suivantes indexables avec canonical propre ; seule la racine du catalogue est dans le sitemap.
- Maillage explicite LSS : une entrée dans le menu hamburger global et un lien discret en dernier dans le panneau outils de la recherche. Le sitemap déclare aussi la racine du catalogue.

Vérifie le gestionnaire global d'erreur 404 : il ne doit pas transformer ces erreurs de pagination en redirections ou en réponses 200.

## 6. Fiche publique d'un chant ou d'une ressource

Pour un chant, la convention LSS est :

- Titre complet : `title - subtitle` si le sous-titre existe, sinon `title`.
- Title SEO : `Paroles de <titre complet> – <nom du produit>`.
- H1 : titre complet seul, sans préfixe « Paroles de », marque ni badges.
- Contexte visible près du H1 : « Paroles du chant ».
- Description SEO courte et déterministe fondée sur le titre, normalisée en texte brut et tronquée proprement. LSS vise au maximum 160 caractères ; ce seuil est un choix d'implémentation.
- La description ne reprend pas automatiquement la description libre, les métadonnées ni de longs extraits de paroles.
- La description libre peut rester visible lorsqu'elle aide le lecteur.
- Canonical vers l'URL historique propre ; inclusion au sitemap seulement si le chant est public.

Exemple de formulation à adapter et traduire : « Retrouvez les paroles de <titre complet>, avec le texte du chant structuré pour la lecture et la projection dans <nom du produit>. »

Pour une autre ressource métier, adapte le vocabulaire et le contenu du titre. Ne présente pas une fiche qui ne contient pas de paroles comme une page de paroles.

## 7. Sitemap et robots.txt

Expose les deux ressources dynamiquement via Django, sur le domaine du produit destinataire.

### `/sitemap.xml`

- XML valide, URL absolues canoniques uniquement.
- Liste blanche de pages publiques choisies et requête filtrée selon les droits anonymes pour les ressources dynamiques.
- Aucun résultat de recherche, filtre, préférence, contenu privé, endpoint technique ou page de workflow.
- Pour le catalogue LSS, seule la racine figure au sitemap, pas les pages `?page=N`.
- Aucun lien vers le Wiki ou une documentation hébergée sur un autre domaine.
- Ne fabrique pas de `lastmod` à partir de la date du jour. LSS l'omet faute de date de modification fiable des chants.
- Pas de `priority` ni de `changefreq` dans le socle LSS.

### `/robots.txt`

Reprends ce contenu en remplaçant le domaine indicatif :

```text
User-agent: *
Allow: /
Sitemap: https://domaine-du-projet.example/sitemap.xml
```

Ne bloque pas les pages `noindex` dans `robots.txt` : leur balise robots doit pouvoir être lue. Le contrôle de leur accès reste indépendant.

## 8. Partage et données structurées

- Open Graph minimal : `og:title`, `og:description`, `og:url`, `og:type`, `og:site_name`.
- Aligne ces valeurs sur la canonical et les métadonnées de la page. N'ajoute pas d'URL de partage privée ou porteuse de secret.
- LSS n'impose pas d'image Open Graph dédiée.
- L'accueil LSS expose un JSON-LD `WebSite` et `SoftwareApplication`. Adapte le nom, l'URL, la description, la catégorie et l'offre au produit destinataire ; ne reprends l'offre gratuite que si elle est exacte.
- Sérialise le JSON côté serveur. Si le JSON est injecté dans un script avec `safe`, échappe notamment `<` en `\u003C` pour empêcher une fermeture de balise script par une donnée texte. Ne concatène pas du JSON à la main.
- N'invente pas d'avis, de notes ou de caractéristiques pour enrichir les données structurées.

## 9. Internationalisation

Le code technique reste en anglais ; les textes d'interface et SEO ont le français pour langue source et passent par Django i18n. Les chaînes utilisées en JavaScript proviennent de templates traduits ou d'un pont i18n contrôlé par l'application.

Renseigne la langue effective du document dans `<html lang="…">`. Ne crée pas de `hreflang` tant que le produit ne possède pas d'URL distinctes et stables pour chaque langue. Un sélecteur de langue stocké en session ne suffit pas. Ne crée pas de nouvelles routes linguistiques uniquement pour copier ce socle.

## 10. Mise en œuvre et validation dans le dépôt destinataire

1. Lire les documents copiés et la documentation métier locale ; dresser la matrice des routes publiques et privées.
2. Repérer le template de base, les surcharges de `title`, les templates autonomes et la structure H1/H2.
3. Adapter le helper SEO, la configuration du domaine et le rendu commun du `<head>`.
4. Appliquer le contexte SEO explicite uniquement aux pages choisies ; adapter le front sans casser les actions métier.
5. Adapter le catalogue public si pertinent, le sitemap, `robots.txt` et le maillage HTML.
6. Ajouter les tests d'intégration correspondants et mettre à jour la documentation de référence locale.

Vérifications attendues sur le HTML et les réponses HTTP :

- Une page indexable : title, description, robots, canonical HTTPS du bon domaine et H1 cohérents.
- Une page métier nouvelle sans contexte SEO : fallback `noindex, follow`, sans canonical.
- Une page autonome : politique robots vérifiée malgré l'absence d'héritage de `base.html`.
- Recherche et filtres : `noindex` et canonical racine, fonctionnement utilisateur conservé.
- Catalogue : exclusion des contenus non publics, pagination en liens HTML, canonical propre à chaque page, 301 de la page 1 et vraies 404 invalides, y compris avec la configuration d'erreur de production.
- Fiche publique : H1 sans badges et métadonnées correctes ; fiche restreinte : accès métier préservé et absence du sitemap.
- Sitemap : XML valide, seulement les URL autorisées, aucune fuite de données privées ou d'URL LSS résiduelle.
- `robots.txt` : bon domaine, sitemap déclaré et absence de blocage empêchant la lecture de `noindex`.
- Accueil : JSON-LD valide, exact pour le produit et injecté correctement.
- Aucun doublon de balises SEO ou de H1 dans les variantes responsive ; contenu principal disponible dans le HTML initial.

Référence de tests dans LSS : `app_main.tests.SeoIntegrationTests`. Adapte ce nom et la commande au dépôt destinataire. Dans LSS :

```bash
uv run python manage.py test app_main.tests.SeoIntegrationTests --noinput -v 2
```

### Points de vigilance lors de la copie

Ce guide décrit le contrat à appliquer, pas une garantie que chaque ancien template LSS le respecte déjà. En particulier, les templates autonomes ne bénéficient pas du fallback du shell et le traitement global des 404 doit être contrôlé. Copie les principes et vérifie le résultat local, plutôt que de reproduire ces écarts éventuels.

Le transfert est terminé lorsque la politique d'indexation du projet frère est explicite, documentée et testée, que ses pages publiques exposent leur contenu et leurs liens dans le HTML, et que son domaine et sa marque remplacent les références LSS dans toutes les sorties SEO.
