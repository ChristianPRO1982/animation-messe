# Lien wiki contextuel - Animation Messe

## Objet

Le bouton `?` du footer utilise `request.resolver_match.url_name` pour choisir
une page wiki contextuelle.

Pour l'instant, une seule page wiki est active. Toutes les routes doivent donc
pointer vers la home du wiki Animation Messe :

- `https://github.com/ChristianPRO1982/animation-messe/wiki`

Source de verite technique :

- `app_main/wiki_help.py`

Regle de maintenance actuelle :

- garder `WIKI_PAGE_BY_URL_NAME` vide tant qu'il n'existe pas de pages wiki
  dediees ;
- toute route, connue ou inconnue, doit pointer vers la home du wiki ;
- garder ce document aligne avec `app_main/wiki_help.py` quand le projet wiki
  dedie sera ouvert.

URL par defaut :

- `https://github.com/ChristianPRO1982/animation-messe/wiki`

## Mapping actuel

| `url_name` | Cible wiki principale | Notes |
| --- | --- | --- |
| toutes les routes | home du wiki AM | Mapping contextuel volontairement desactive |

## Routes en fallback par defaut

Toutes les routes sont en fallback par defaut pour le moment.

## Routes futures attendues

Les apps metier creees pour AM devront enrichir ce mapping quand leurs pages seront stabilisees :

- routes `app_group` : groupes, roles de groupe, Membres AM, recueils et tags ;
- routes `app_celebration` : gabarits, celebrations, deroule, AELF, feuilles de messe ;
- routes `app_planning` : planning, disponibilites, affectations, validation du planning ;
- routes chant exposees cote AM : consultation ou selection de chants LSS selon les ecrans retenus.

## Regle de travail

Ne pas recopier le mapping wiki de Lyrics Slide Show. Le mapping AM devra suivre
les routes Django reelles du projet Animation Messe quand des pages dediees
existeront dans le wiki `animation-messe`.
