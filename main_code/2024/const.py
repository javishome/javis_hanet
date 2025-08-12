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
SVC_UPDATE_PERIOD = "update_period"
SVC_DELETE_PERIOD = "delete_period"
SVC_CHECK_FACEID_GROUP_SENSOR = "check_faceid_group_sensor"
SVC_SYNC_PERIODS = "sync_periods"

# 1 prod
SERVER_URL = "https://lock-api."
PATH_CONFIG = "/config/"
MODE = "prod"

# # 2 dev (server test and ha test)
# SERVER_URL = "https://improved-liger-tops.ngrok-free.app"
# PATH_CONFIG = os.getcwd() + "/config/"
# MODE = "dev"
# #3 real dev (for server test on ha real)
# SERVER_URL = "https://improved-liger-tops.ngrok-free.app"
# PATH_CONFIG = "/config/"
# MODE = "dev_ha_real"
# common
PATH = PATH_CONFIG + "person_javis_v2.json"
# DATA_TIME_MUL_PATH = PATH_CONFIG + "data_time_mul.json"
FOLDER_PERSON_LOG = PATH_CONFIG + "timesheet/"
PATH_PERSON_LOG = FOLDER_PERSON_LOG + "timesheet.log"
API_GET_PLACES_INFO_URL =  "/api/hanet/get_places"
API_GET_INFO_WITH_PLACES = "/api/hanet/get_info_with_places"
FACE_SENSOR_PATH = PATH_CONFIG + "packages/face_sensor.yaml"
HRM_URL = "https://hrm.javishome.vn"
TIMESHEET_SECRET_KEY= "JbY7Qu0fPR27"