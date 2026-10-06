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
