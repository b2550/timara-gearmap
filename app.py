import configparser
import os

# import requests_async as requests
import requests
from flask import Flask
from flask_migrate import Migrate
from flask_socketio import SocketIO

from config import config, csrf, socketio
from database import db
from omeka import sync_with_omeka
from checkout_system import user
from admin_panel import admin

app = Flask(__name__)

# --- Register Blueprints ---
app.register_blueprint(user)
app.register_blueprint(admin)


# --- FLASK CONFIG ---
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DB_URI", "sqlite:///depot.db"
)

if app.config["SECRET_KEY"] == "secret":
    app.logger.warning(
        "SECRET_KEY environment variable not set. Do not do this in a production environment."
    )

# --- CHECK FOR BAD VALUES ---
if config.get("OMEKA_URI") is None:
    raise RuntimeError(
        f"Omeka URI is not set. Please set the value of OMEKA_URI in an environment variable."
    )
else:
    config["OMEKA_URI"] = f"http://{config['OMEKA_URI']}/api"

r = requests.get(config["OMEKA_URI"])
if r.status_code != 500:
    raise RuntimeError(
        f"Failed to connect to Omeka URI: {config['OMEKA_URI']} returned {r.status_code}"
    )


db.init_app(app)
csrf.init_app(app)
socketio.init_app(app)
migrate = Migrate(app, db)


with app.app_context():
    db.create_all()


@app.cli.command("omeka-sync")
def omeka_sync():
    sync_with_omeka()


if __name__ == "__main__":
    socketio.run(app)
