from collections import namedtuple

from flask import Blueprint, render_template
from flask_socketio import emit
import dateutil.parser
from sqlalchemy import or_

from config import socketio
from database import Reservation, db, Gear, GearBarcode, User

user = Blueprint("user", __name__, url_prefix="/")


@user.route("/", methods=("GET", "POST"))
def reserve():
    return render_template("reserve.html")


@socketio.on("connect")
def connect():
    refresh_inventory()


@socketio.on("refresh_inventory")
def refresh_inventory():
    inventory = [
        {
            "id": gear.id,
            "model": gear.model,
            "quantity": gear.quantity,
            "barcodes": [entry.barcode for entry in gear.barcodes],
        }
        for gear in Gear.query.all()
    ]
    emit("refresh_inventory", inventory)


@socketio.on("barcode_query")
def query_barcode(query, start_date, end_date):
    try:
        start_date = dateutil.parser.parse(start_date).date()
        end_date = dateutil.parser.parse(end_date).date()
    except ValueError:
        emit("error", "Please enter a valid start and end date.")
        return
    barcode = GearBarcode.query.filter_by(barcode=query).first()
    if barcode:
        # Check if gear is already reserved
        if check_for_date_overlap(barcode.reservations, start_date, end_date):
            # If already reserved, try to find alternative same item model
            alternative = find_alternative_barcode(
                barcode, start_date, end_date
            )
            if alternative is not None:
                emit(
                    "warning",
                    f"{barcode.item.model} with barcode {query} has conflicting reservations. Please substitute with barcode {alternative.barcode}.",
                )
                query = alternative
            else:
                emit(
                    "error",
                    f"{barcode.item.model} with barcode {query} has conflicting reservations and no alternatives are available.",
                )
            return
        item = {
            "model": barcode.item.model,
            "quantity": barcode.item.quantity,
            "barcode": int(query),
            "all_barcodes": [entry.barcode for entry in barcode.item.barcodes],
        }
        emit("append", item)
    else:
        # Check for user by T-number or ID
        user = User.query.filter(
            or_(
                User.t_number == query.replace("T", "")
                if type(query) is str
                else query,
                User.barcode == query,
            )
        ).first()
        if user:
            data = {
                "t_number": user.t_number,
                "name": user.name,
                "email": user.email,
                "barcode": user.barcode,
                "self_checkout": user.self_checkout,
                "depot_assistant": user.depot_assistant,
            }
            emit("user", data)


@socketio.on("submit")
def submit(start_date, end_date, barcodes, user_id):
    try:
        start_date = dateutil.parser.parse(start_date).date()
        end_date = dateutil.parser.parse(end_date).date()
    except ValueError:
        emit("error", "Please enter a valid start and end date.")
        return
    user_query = User.query.filter_by(t_number=user_id).first()
    if user_query:
        reservation = Reservation(
            user_id=user_id, start_date=start_date, end_date=end_date
        )
        db.session.add(reservation)
        for barcode in barcodes:
            gear = GearBarcode.query.filter_by(barcode=barcode).first()
            if gear:
                reservation.barcodes.append(gear)
        db.session.commit()
        emit("submit_success", f"{reservation.id:08d}")
    else:
        emit("error", "Please scan/enter a Student ID barcode or T-number")


def check_for_date_overlap(reservations, start_date, end_date):
    Range = namedtuple("Range", ["start", "end"])
    reservation_range = Range(start=start_date, end=end_date)
    for reservation in reservations:
        check_range = Range(
            start=reservation.start_date, end=reservation.end_date
        )
        latest_start = max(reservation_range.start, check_range.start)
        earliest_end = min(reservation_range.end, check_range.end)
        delta = (earliest_end - latest_start).days + 1
        if delta > 0:
            return True


def find_alternative_barcode(barcode, start_date, end_date):
    for barcode in barcode.item.barcodes:
        if not check_for_date_overlap(
            barcode.reservations, start_date, end_date
        ):
            return barcode
    return None


@user.route("/gear")
def gear():
    query = Gear.query.all()
    return render_template("gear.html", gear_items=query)
