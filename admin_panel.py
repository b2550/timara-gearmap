from flask import Blueprint

admin = Blueprint("admin", __name__, url_prefix="/admin")


@admin.route("/")
def dashboard():
    return "todo"


@admin.route("/settings", methods=("GET", "POST"))
def settings():
    return "todo"


@admin.route("/reservations", methods=("GET", "POST"))
def reservations():
    return "todo"


@admin.route("/users", methods=("GET", "POST"))
def gear():
    return "todo"
