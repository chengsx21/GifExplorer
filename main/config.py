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
    TASK_HANDLING_MAX_TIME = 1200
else:
    TASK_HANDLING_MAX_TIME = 3

if not DEBUG:
    GIF_EXTERNAL_LINK_MAX_TIME = 86400
else:
    GIF_EXTERNAL_LINK_MAX_TIME = 3

if not DEBUG:
    CACHE_MAX_TIME = 120
else:
    CACHE_MAX_TIME = 10

MAX_GIFS_PER_PAGE = 20

MAX_USERS_PER_PAGE = 10

MAX_MESSAGES_PER_PAGE = 50

MAX_SEARCH_HISTORY = 200

MAX_CACHE_HISTORY = 500

CACHE_HISTORY = {}

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
