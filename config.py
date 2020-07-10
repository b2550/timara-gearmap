# --- GLOBAL CONFIGURATION (VALUES SHOULD NEVER CHANGE DURING RUNTIME) ---
import configparser
import os

from flask_seasurf import SeaSurf
from flask_socketio import SocketIO

config = {
    "OMEKA_URI": os.getenv("OMEKA_URI"),
    "OMEKA_KEY_IDEN": os.getenv("OMEKA_KEY_IDEN"),
    "OMEKA_KEY_CRED": os.getenv("OMEKA_KEY_CRED"),
    "CONFIG_FILE": os.getenv("CONFIG_FILE", "config.ini"),
}

# --- LOCAL CONFIGURATION FILE (VALUES CAN BE EDITED FROM ADMIN PANEL) ---
local_config = configparser.ConfigParser()
if not os.path.isfile(config["CONFIG_FILE"]):
    local_config["VERSION"] = {"CONFIG": "1"}
    local_config["OMEKA API"] = {
        "resource_template_id": "2",
        "gear_item_set_id": "114",
        "image_types": ["jpg", "jpeg", "png", "gif", "tiff"],
    }
    with open(config["CONFIG_FILE"], "w") as configfile:
        local_config.write(configfile)
else:
    local_config.read(config["CONFIG_FILE"])

csrf = SeaSurf()
socketio = SocketIO()
