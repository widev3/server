import math
import os.path
import threading
from pathlib import Path
from astropy import units
from drivers.Monitor import Monitor
from SessionProperties import SessionProperties as SP
from flask import request, jsonify, Blueprint
from astropy.coordinates import EarthLocation
from drivers.Radiotelescope import Radiotelescope

mount_bp = Blueprint(Path(__file__).stem, __name__)


def is_float(value: str) -> bool:
    try:
        f = float(value)
        return math.isfinite(f)
    except:
        return False


@mount_bp.before_request
def mount_bp_before_request():
    if SP().MOUNT is None:
        return jsonify({"error": "unknown hardware type for the mount"}), 400


@mount_bp.route("/location", methods=["POST"])
def mount_location():
    if SP().MOUNT.get_running():
        return jsonify({"error": "already moving"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "empty body"}), 400

    if "lat" not in data:
        return jsonify({"error": "missing required field lat"}), 400
    if "lon" not in data:
        return jsonify({"error": "missing required field lon"}), 400
    if "height" not in data:
        return jsonify({"error": "missing required field height"}), 400

    lat = data["lat"]
    lon = data["lon"]
    height = data["height"]

    lat = lat * units.deg if is_float(lat) else lat
    lon = lon * units.deg if is_float(lon) else lon
    height = height * units.m if is_float(height) else height

    SP().MOUNT.set_location(EarthLocation(lat=lat, lon=lon, height=height))
    return jsonify({"message": "ok"}), 200


@mount_bp.route("/target", methods=["POST"])
def mount_target():
    if SP().MOUNT.get_running():
        return jsonify({"error": "already moving"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "empty body"}), 400

    if "ra" in data and "dec" not in data:
        return jsonify({"error": "missing required field target.dec"}), 400
    if "dec" in data and "ra" not in data:
        return jsonify({"error": "missing required field target.ra"}), 400
    if "alt" in data and "az" not in data:
        return jsonify({"error": "missing required field target.az"}), 400
    if "az" in data and "alt" not in data:
        return jsonify({"error": "missing required field target.alt"}), 400
    if "ra" in data and "alt" in data:
        return jsonify({"error": "target should be in ra/dec or alt/az"}), 400

    if "az" in data:
        alt = data["alt"]
        az = data["az"]
        alt = alt * units.deg if is_float(alt) else alt
        az = az * units.deg if is_float(az) else az
        SP().MOUNT.set_target(alt=alt, az=az)
    elif "ra" in data:
        ra = data["ra"]
        dec = data["dec"]
        ra = ra * units.deg if is_float(ra) else ra
        dec = dec * units.deg if is_float(dec) else dec
        SP().MOUNT.set_target(ra=ra, dec=dec)
    else:
        return jsonify({"error": "neither ra/dec nor alt/az"}), 400

    target = SP().MOUNT.get_target()
    return (
        jsonify(
            {
                "message": "ok",
                "target": {
                    "ra": round(target.ra.deg, 6),
                    "dec": round(target.dec.deg, 6),
                },
            }
        ),
        200,
    )


@mount_bp.route("/offset", methods=["POST"])
def mount_offset():
    if SP().MOUNT.get_running():
        return jsonify({"error": "already moving"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "empty body"}), 400

    if "absolute" in data:
        absolute = data["absolute"]
        if "ra" in absolute:
            SP().MOUNT.set_absolute_offset(ra=absolute["ra"])
        if "dec" in absolute:
            SP().MOUNT.set_absolute_offset(dec=absolute["dec"])
        if "alt" in absolute:
            SP().MOUNT.set_absolute_offset(alt=absolute["alt"])
        if "az" in absolute:
            SP().MOUNT.set_absolute_offset(az=absolute["az"])
    elif "relative" in data:
        relative = data["relative"]
        if "ra" in relative:
            SP().MOUNT.set_relative_offset(ra=relative["ra"])
        if "dec" in relative:
            SP().MOUNT.set_relative_offset(dec=relative["dec"])
        if "alt" in relative:
            SP().MOUNT.set_relative_offset(alt=relative["alt"])
        if "az" in relative:
            SP().MOUNT.set_relative_offset(az=relative["az"])
    elif "timedelta" in data:
        timedelta = data["timedelta"]
        ra_g = int(15 * timedelta / 3600)
        timedelta -= 3600 * ra_g / 15
        ra_m = int(timedelta / 60)
        timedelta -= ra_m * 60
        ra_s = timedelta
        ra = ra_g + ra_m / 60 + ra_s / 3600
        SP().MOUNT.set_relative_offset(ra=ra * units.deg)
    else:
        return jsonify({"error": "'absolute', 'relative' or 'timedelta'"}), 400

    offset = SP().MOUNT.get_offset()
    return (
        jsonify(
            {
                "message": "ok",
                "offset": {
                    "ra": round(offset.ra.deg, 6),
                    "dec": round(offset.dec.deg, 6),
                },
            }
        ),
        200,
    )


@mount_bp.route("/run", methods=["GET"])
def mount_run():
    if SP().MOUNT.get_running():
        return jsonify({"error": "already moving"}), 403
    if SP().MOUNT.get_location() is None:
        return jsonify({"error": "mount location is not set"}), 400
    if not SP().MOUNT.get_target():
        return jsonify({"error": "mount target is not set"}), 400

    bh = request.args.get("bh")
    if not bh:
        return jsonify({"error": "missing required argument bh"}), 400
    if bh not in ["follow", "transit", "route"]:
        return jsonify({"error": "bh must be 'follow', 'transit' or 'route'"}), 400
    if bh in ["transit", "route"] and not SP().MOUNT.get_offset():
        return jsonify({"error": f"mount offset must be set when bh is {bh}"}), 400

    thread = threading.Thread(target=lambda: SP().MOUNT.run(bh))
    thread.start()

    return jsonify({"message": "ok"}), 200


@mount_bp.route("/stop", methods=["GET"])
def mount_stop():
    if not SP().MOUNT.get_running():
        return jsonify({"error": "already stopped"}), 403

    SP().MOUNT.stop()
    return jsonify({"message": "ok"}), 200


@mount_bp.route("/status", methods=["GET"])
def mount_status():
    if not SP().MOUNT:
        return jsonify({"error": "mount not initialized"}), 400

    position = SP().MOUNT.get_position() or (None, None)
    offset = SP().MOUNT.get_offset() or type("Obj", (), {"ra": None, "dec": None})()
    target = SP().MOUNT.get_target() or type("Obj", (), {"ra": None, "dec": None})()
    location = SP().MOUNT.get_location()

    return (
        jsonify(
            {
                "location": location,
                "target": {
                    "ra": (None if target.ra is None else round(target.ra.deg, 6)),
                    "dec": (None if target.dec is None else round(target.dec.deg, 6)),
                },
                "offset": {
                    "ra": (None if offset.ra is None else round(offset.ra.deg, 6)),
                    "dec": (None if offset.dec is None else round(offset.dec.deg, 6)),
                },
                "position": {
                    "ra": None if position[0] is None else round(position[0], 6),
                    "dec": None if position[1] is None else round(position[1], 6),
                },
                "bh": getattr(SP().MOUNT, "get_behavior", lambda: None)(),
                "is_running": getattr(SP().MOUNT, "get_running", lambda: False)(),
            }
        ),
        200,
    )
