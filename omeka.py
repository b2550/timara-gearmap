# import requests_async as requests
from datetime import datetime

import requests

from config import config, local_config
from database import Gear, db, GearBarcode


def sync_with_omeka():
    url = config["OMEKA_URI"] + "/items"
    media_url = config["OMEKA_URI"] + "/media/"  # Trailing slash needed
    page = 1
    count = 0
    barcode_count = 0

    print("Purging Gear Repo")
    Gear.query.delete()  # TODO: Don't do this. It will destroy all the database relationships if something is changed segnificantly. Instead check for item and update if needed.
    GearBarcode.query.delete()
    print("Syncing...")

    while True:
        page_count = 0
        page_barcode_count = 0
        r = requests.get(url)
        print(f">>> Syncing page {page} of {r.links.get('last')['url'][-2:]}")

        if r.status_code == 200:
            print("Request OK")
            all_items_json = r.json()
            for json_item in all_items_json:
                if json_item.get("o:resource_template").get("o:id") == int(
                    local_config["OMEKA API"]["resource_template_id"]
                ) and json_item.get("o:item_set")[0].get("o:id") == int(
                    local_config["OMEKA API"]["gear_item_set_id"]
                ):
                    page_count += 1
                    item = gear_item_parser(json_item)
                    print(
                        f"Adding item {item['model']} (Quantity: {item['quantity'].lower().replace('quantity: ', '') if item['quantity'] else '1'})"
                    )
                    db_item = Gear(
                        id=item["id"],
                        model=item["model"],
                        manufacturer=item["manufacturer"],
                        categorization=item["categories"],
                        description=item["descriptions"],
                        kit_items=item["kit_items"],
                        access=item["access_message"],
                        quantity=item["quantity"]
                        .lower()
                        .replace("quantity: ", ""),
                        created_date=datetime.strptime(
                            item["create_date"], "%Y-%m-%dT%H:%M:%S%z"
                        ),
                        modified_date=datetime.strptime(
                            item["modify_date"], "%Y-%m-%dT%H:%M:%S%z"
                        ),
                    )
                    for barcode in item["barcodes"]:
                        if len(barcode) > 6:
                            split_barcodes = barcode.split(",")
                            for split_barcode in split_barcodes:
                                split_barcode = split_barcode.replace(" ", "")
                                query = GearBarcode.query.filter_by(
                                    barcode=split_barcode
                                ).first()
                                if query is None and "*" not in split_barcode:
                                    page_barcode_count += 1
                                    db_barcode = GearBarcode(
                                        barcode=split_barcode,
                                        gear_id=item["id"],
                                    )
                                    db.session.add(db_barcode)
                                elif "*" in barcode:
                                    print(
                                        f"     - Barcode {split_barcode[:-1]} skipped because it is excluded via the astrix character (*)"
                                    )
                                else:
                                    print(
                                        f"===\nWARNING: DUPLICATE BARCODE FOUND: {split_barcode}\n{item['model']} ({item['id']}) will not work with this barcode\n{query.item.model} ({query.item.id}) already has the barcode in the database\n==="
                                    )
                        else:
                            query = GearBarcode.query.filter_by(
                                barcode=barcode
                            ).first()
                            if query is None:
                                page_barcode_count += 1
                                db_barcode = GearBarcode(
                                    barcode=barcode, gear_id=item["id"]
                                )
                                db.session.add(db_barcode)
                            else:
                                print(
                                    f"===\nWARNING: DUPLICATE BARCODE FOUND: {barcode}\n{item['model']} ({item['id']}) will not work with this barcode\n{query.item.model} ({query.item.id}) already has the barcode in the database\n==="
                                )
                    for media in item["media"]:
                        mr = requests.get(media_url + str(media))
                        media_item = mr.json()
                        if (
                            media_item["o:media_type"].split("/")[1]
                            in local_config["OMEKA API"]["image_types"]
                        ):
                            db_item.image_url = media_item["o:thumbnail_urls"][
                                "square"
                            ]
                            break
                    db.session.add(db_item)
            db.session.commit()
            count += page_count
            barcode_count += page_barcode_count
            print(
                f">>> Synced {page_count} items and {page_barcode_count} barcodes (for a current total of {count} items and {barcode_count} barcodes)"
            )
        if r.links.get("next"):
            url = r.links["next"]["url"]
            page += 1
        else:
            break
    print(
        f">>> Sync Complete. Synced {count} items and {barcode_count} barcodes. Wow!"
    )


def gear_item_parser(item):
    return {
        "id": item.get("o:id"),
        "template": item.get("o:resource_template").get("o:id"),
        "create_date": item.get("o:created").get("@value"),
        "modify_date": item.get("o:modified").get("@value"),
        "media": [
            media_id.get("o:id") for media_id in item.get("o:media") or []
        ],
        "all_item_set_ids": [
            item_set_id.get("o:id")
            for item_set_id in item.get("o:item_set") or []
        ],
        "model": item.get("gear:model")[0].get("@value")
        if item.get("gear:model")
        else "",
        "manufacturer": item.get("gear:manufacturer")[0].get("@value")
        if item.get("gear:manufacturer")
        else "",
        "categories": [
            category.get("@value")
            for category in item.get("gear:categorization") or []
        ],
        "descriptions": [
            description.get("@value")
            for description in item.get("dcterms:description") or []
        ],
        "kit_items": [
            kit_item.get("@value")
            for kit_item in item.get("gear:content") or []
        ],
        "barcodes": [
            barcode.get("@value")
            for barcode in item.get("gear:identifier") or []
        ],
        "access_message": item.get("dcterms:audience")[0].get("@value")
        if item.get("dcterms:audience")
        else "",
        "quantity": item.get("dcterms:coverage")[0].get("@value")
        if item.get("dcterms:coverage")
        else "",
    }
