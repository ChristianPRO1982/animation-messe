WIKI_DEFAULT_URL = "https://github.com/ChristianPRO1982/animation-messe/wiki"

# Temporary contract: only the wiki home exists for now.
# Keep the mapping empty until a dedicated wiki project is ready.
WIKI_PAGE_BY_URL_NAME: dict[str, str] = {}


def get_wiki_help_url(url_name: str | None) -> str:
    return WIKI_PAGE_BY_URL_NAME.get(str(url_name or "").strip(), WIKI_DEFAULT_URL)
