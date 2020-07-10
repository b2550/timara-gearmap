from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy

db = SQLAlchemy()


class User(db.Model):
    t_number = db.Column(db.Integer, primary_key=True)  # Strip T
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    barcode = db.Column(db.Integer, nullable=False)
    self_checkout = db.Column(db.Boolean)
    depot_assistant = db.Column(db.Boolean)
    # TODO: Disable user


class Gear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String)
    manufacturer = db.Column(db.String)
    categorization = db.Column(db.PickleType)
    description = db.Column(db.PickleType)
    image_url = db.Column(db.String)
    kit_items = db.Column(db.PickleType)
    access = db.Column(db.String)
    quantity = db.Column(db.Integer)
    created_date = db.Column(db.DateTime)
    modified_date = db.Column(db.DateTime)
    retired = db.Column(
        db.Boolean
    )  # TODO: Item either no longer in Gear Depot item set or was deleted from Omeka
    removed_from_circulation = db.Column(db.Boolean)
    maintenance = db.Column(
        db.Boolean
    )  # Item missing kit items or in need of repair
    notes = db.Column(db.String)


class GearBarcode(db.Model):
    barcode = db.Column(db.Integer, primary_key=True)
    gear_id = db.Column(db.Integer, db.ForeignKey("gear.id"), nullable=False)
    item = db.relationship("Gear", backref=db.backref("barcodes", lazy=True))


gear_reservations = db.Table(
    "gear_reservations",
    db.Column(
        "reservation_id",
        db.Integer,
        db.ForeignKey("reservation.id"),
        primary_key=True,
    ),
    db.Column(
        "gear_barcode",
        db.Integer,
        db.ForeignKey("gear_barcode.barcode"),
        primary_key=True,
    ),
)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.t_number"), nullable=False
    )
    user = db.relationship(
        "User", backref=db.backref("reservations", lazy=True)
    )
    status = db.Column(db.String)
    locker = db.Column(db.Integer)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    notes = db.Column(db.String)

    barcodes = db.relationship(
        "GearBarcode",
        secondary=gear_reservations,
        backref=db.backref("reservations", lazy=True),
    )
