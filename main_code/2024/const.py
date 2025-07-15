# defind config
# common
DOMAIN = "javis_hanet"
HOST1 = "javisco.com"
HOST2 = "javishome.io"
HOST3 = "javiscloud.com"
CLIENT_ID = "94414a66f3c6a7e2ceadc17af8ccdd60"
CLIENT_SECRET = "secret"
AUTHORIZE_URL = "https://oauth.hanet.com/oauth2/authorize"
SVC_WRITE_PERSON = "write_person"
SVC_PUSH_TO_QCD = "push_to_qcd"

# 1 prod
SERVER_URL = "https://lock-api."
PATH_CONFIG = "/config/"
MODE = "prod"

# # 2 dev (server test and ha test)
# SERVER_URL = "https://improved-liger-tops.ngrok-free.app"
# PATH_CONFIG = os.getcwd() + "/config/"
# MODE = "dev"
# #3 real dev (for server test on ha real)
SERVER_URL = "https://improved-liger-tops.ngrok-free.app"
PATH_CONFIG = "/config/"
MODE = "dev_ha_real"
# common
PATH = PATH_CONFIG + "person_javis_v2.json"
FOLDER_PERSON_LOG = PATH_CONFIG + "timesheet/"
PATH_PERSON_LOG = FOLDER_PERSON_LOG + "timesheet.log"
API_GET_PLACES_INFO_URL = SERVER_URL + "/api/hanet/get_places"
API_GET_INFO_WITH_PLACES = SERVER_URL + "/api/hanet/get_info_with_places"