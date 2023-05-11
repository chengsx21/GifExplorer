'''
    configure for the app
'''
from GifExplorer.settings import DEBUG
from .search import ElasticSearchEngine

if not DEBUG:
    USER_VERIFICATION_MAX_TIME = 300
else:
    USER_VERIFICATION_MAX_TIME = 3

if not DEBUG:
    GIF_EXTERNAL_LINK_MAX_TIME = 86400
else:
    GIF_EXTERNAL_LINK_MAX_TIME = 3

MAX_GIFS_PER_PAGE = 20

MAX_USERS_PER_PAGE = 10

MAX_SEARCH_HISTORY = 200

SEARCH_ENGINE = ElasticSearchEngine()

SECRET_KEY = "Welcome to the god damned SE world!"

CATEGORY_LIST = {
    "": "",
    "home": "",
    "sport": "sports",
    "fashion": "fashion",
    "food": "food",
    "animal": "animal",
    "emoji": "emoji",
    "sports": "sports",
    "politics": "politics",
    "tech": "tech",
    "social": "social",
    "finance": "finance",
    "auto": "auto",
    "game": "game",
    "health": "health",
    "meme": "meme",
}
