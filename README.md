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
- `common.group_tags` est livré par le repo propriétaire de `common` ;
  `app_group.0002` pose la FK `am.s_song_tag.gt_id -> common.group_tags.gt_id`.

Contrôles au dernier point de validation :

```text
ruff check: passed
ruff format: passed
django check: passed
pytest: 127 passed
coverage: 95%
```
