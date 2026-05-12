from django.conf import settings

API_TOKEN = settings.KOBO_API_TOKEN
BASE_URL = "https://kf.kobotoolbox.org/api/v2/assets/"

# METTEZ VOS VRAIS UID ICI
from django.conf import settings

API_TOKEN = settings.KOBO_API_TOKEN
BASE_URL = "https://kf.kobotoolbox.org/api/v2/assets/"

# METTEZ VOS VRAIS UID ICI
FORM_UIDS = {
    "eleves_registre": "aeCDyBDsfPCRBHB259zT2G",
     #"eleves_registre": "aeCDyBDsfPCRBHB259zT2G",
     "eleves_abs_q": "awqPdaWeA6XnHS87BAJwVq",
    "eleves_abs_m": "a7apKJ8UpffZR4hxqAXK6u",
    "ens_registre": "aeTpgZno9krCvy87Kux4nZ",
    "ens_abs_q": "apnNUiwDAx8kC2VrP8juqP",
    "ens_abs_m": "aMP9QRHNDLHnRyZvJgu4w9",
}

HEADERS = {"Authorization": f"Token {API_TOKEN}"}



