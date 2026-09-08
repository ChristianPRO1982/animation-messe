# Mapping du lien wiki contextuel - Animation Messe

## Objet

Le bouton `?` du footer utilise `request.resolver_match.url_name` pour choisir une page wiki contextuelle.

Source de verite technique :

- `app_main/wiki_help.py`

Regle de maintenance :

- ajouter une entree dans `WIKI_PAGE_BY_URL_NAME` pour toute nouvelle page importante ;
- si aucune entree n'existe, le lien pointe automatiquement vers la home du wiki ;
- garder ce document aligne avec `app_main/wiki_help.py` quand une route importante est ajoutee ou changee.

URL par defaut :

- `https://github.com/ChristianPRO1982/animation-messe/wiki`

## Mapping actuel

| `url_name` | Cible wiki principale | Notes |
| --- | --- | --- |
| `homepage` | home du wiki AM | Point d'entree generique |
| `login` | `Connexion` | Page principale pour expliquer la connexion |
| `site_params` | `Modération-du-site` | Administration et moderation du site |
| `theme_preferences` | `Thèmes` | Preferences visuelles |
| `language` | `Langue` | Choix de langue |
| `privacy_policy` | `Confidentialité` | Politique de confidentialite |

## Routes en fallback par defaut

Ces routes existent dans `app_main` mais n'ont pas encore de page wiki dediee dans le mapping courant. Elles pointent donc vers la home du wiki :

- `account`
- `auth_callback`
- `keycloak_diagnostic`
- `provision_redirect`
- `provision_complete`
- `logout`
- `heavy`
- `heavy_asset`

## Routes futures attendues

Les apps metier creees pour AM devront enrichir ce mapping quand leurs pages seront stabilisees :

- routes `app_group` : groupes, roles de groupe, Membres AM, recueils et tags ;
- routes `app_celebration` : gabarits, celebrations, deroule, AELF, feuilles de messe ;
- routes `app_planning` : planning, disponibilites, affectations, validation du planning ;
- routes chant exposees cote AM : consultation ou selection de chants LSS selon les ecrans retenus.

## Regle de travail

Ne pas recopier le mapping wiki de Lyrics Slide Show. Le mapping AM doit suivre les routes Django reelles du projet Animation Messe et pointer vers le wiki `animation-messe`.
