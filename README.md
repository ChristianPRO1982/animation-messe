# animation-messe
Site web en django permettant de gérer l'animation des messes

## Commandes Django locales

Les conteneurs Docker utilisent `.env.dev` avec `DB_HOST=postgres`.

Pour lancer Django depuis l'hôte, on réutilise `.env.dev` puis on force
seulement les valeurs qui doivent différer hors Docker.

Fonction et alias zsh conseillés :

```zsh
djsetenvdev() {
  set -a
  if [ -f .env.dev ]; then
    source .env.dev
  else
    echo "Aucun fichier .env.dev dans $(pwd)" >&2
    set +a
    return 1
  fi
  DB_HOST=127.0.0.1
  DB_CONN_MAX_AGE=0
  set +a
}

alias djmakemigrations='uvr python manage.py makemigrations'
alias djmigrate='uvr python manage.py migrate'
alias djmig='djsetenvdev && djmakemigrations && djmigrate'
```

## Niveau courant

- `app_main` et `app_member` : socle initial valide.
- `app_group` : fondation BDD valide avec groupes communs `common`, ancre AM
  des participants, Membres AM, paramètres planning et recueil.
- `app_group.services` est la frontière d'écriture métier pour les futurs
  écrans de gestion : demandes AM, rôles, fonctions, recueil et règles de
  célébration doivent passer par ces services.
- `common.group_tags` est livré par le repo propriétaire de `common` ;
  `app_group.0002` pose la FK `am.s_song_tag.gt_id -> common.group_tags.gt_id`.

Contrôle d'intégration PostgreSQL optionnel, à lancer après `djsetenvdev` quand
la base dev et les schémas `common` / `lss` sont disponibles :

```zsh
UV_CACHE_DIR=.uv-cache uv run python manage.py check_app_group_services
```

Contrôles au dernier point de validation :

```text
ruff check: passed
ruff format: passed
django check SQLite: passed
app_group tests SQLite: passed
makemigrations app_group --check --dry-run: passed
```
