WIKI_DEFAULT_URL = "https://github.com/ChristianPRO1982/animation-messe/wiki"
WIKI_MODERATION_URL = f"{WIKI_DEFAULT_URL}/Mod%C3%A9ration-du-site"

WIKI_PAGE_BY_URL_NAME: dict[str, str] = {
    "homepage": WIKI_DEFAULT_URL,
    "login": f"{WIKI_DEFAULT_URL}/Connexion",
    "site_params": WIKI_MODERATION_URL,
    "theme_preferences": f"{WIKI_DEFAULT_URL}/Th%C3%A8mes",
    "language": f"{WIKI_DEFAULT_URL}/Langue",
    "privacy_policy": f"{WIKI_DEFAULT_URL}/Confidentialit%C3%A9",
}


def get_wiki_help_url(url_name: str | None) -> str:
    return WIKI_PAGE_BY_URL_NAME.get(str(url_name or "").strip(), WIKI_DEFAULT_URL)
