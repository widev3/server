import math
import threading
from pathlib import Path
from astropy import units
from drivers.RadiotelescopeMount import RadiotelescopeMount
from flask import request, jsonify, Blueprint
from astropy.coordinates import EarthLocation
from drivers.MonitorMount import MonitorMount

mount_bp = Blueprint(Path(__file__).stem, __name__)

# Antonio: inizializza i globali per evitare NameError
mount = None
MOUNT_TYPE = None


# global mount
# mount = WOWMount()


def is_float(value: str) -> bool:
    try:
        f = float(value)
        return math.isfinite(f)
    except:
        return False


@mount_bp.route("/config/mounttype", methods=["POST"])
def set_mount_type():
    global mount, MOUNT_TYPE

    data = request.get_json()
    if not data or "type" not in data:
        return jsonify({"error": "missing required field 'type'"}), 400

    mtype = data["type"].lower()
    if mtype not in ["wow", "monitor"]:
        return jsonify({"error": "type must be 'wow' or 'monitor'"}), 400

    if mount.get_running():
        return jsonify({"error": "cannot switch while moving"}), 403

    MOUNT_TYPE = mtype
    if mtype == "monitor":
        from drivers.MonitorMount import MonitorMount

        mount = MonitorMount()
    else:
        from drivers.RadiotelescopeMount import RadiotelescopeMount

        mount = RadiotelescopeMount()

    return jsonify({"message": f"mount type switched to {mtype}"}), 200


@mount_bp.route("/location", methods=["POST"])
def mount_location():
    global mount
    if mount.get_running():
        return jsonify({"error": "already moving"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "empty body"}), 400

    if "lat" not in data:
        return jsonify({"error": "missing required field lat"}), 400

    lat = data["lat"]
    lat = lat * units.deg if is_float(lat) else lat

    if "lon" not in data:
        return jsonify({"error": "missing required field lon"}), 400

    lon = data["lon"]
    lon = lon * units.deg if is_float(lon) else lon

    if "height" not in data:
        return jsonify({"error": "missing required field height"}), 400

    height = data["height"]
    height = height * units.m if is_float(height) else height
    mount.set_location(EarthLocation(lat=lat, lon=lon, height=height))

    return jsonify({"message": "ok"}), 200


@mount_bp.route("/target", methods=["POST"])
def mount_target():
    global mount
    if mount.get_running():
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
        mount.set_target(alt=alt, az=az)
        return (
            jsonify(
                {
                    "message": "ok",
                    "target": {
                        "ra": round(mount.get_target().ra.deg, 6),
                        "dec": round(mount.get_target().dec.deg, 6),
                    },
                }
            ),
            200,
        )
    elif "ra" in data:
        ra = data["ra"]
        dec = data["dec"]
        ra = ra * units.deg if is_float(ra) else ra
        dec = dec * units.deg if is_float(dec) else dec
        mount.set_target(ra=ra, dec=dec)
        return (
            jsonify(
                {
                    "message": "ok",
                    "target": {
                        "ra": round(mount.get_target().ra.deg, 6),
                        "dec": round(mount.get_target().dec.deg, 6),
                    },
                }
            ),
            200,
        )
    else:
        return jsonify({"error": "neither ra/dec nor alt/az"}), 400


@mount_bp.route("/offset", methods=["POST"])
def mount_offset():
    global mount
    if mount.get_running():
        return jsonify({"error": "already moving"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "empty body"}), 400

    if "absolute" in data:
        absolute = data["absolute"]
        if "ra" in absolute and (ra := absolute["ra"]):
            mount.set_absolute_offset(ra=ra)
        if "dec" in absolute and (ra := absolute["dec"]):
            mount.set_absolute_offset(dec=ra)
        if "alt" in absolute and (alt := absolute["alt"]):
            mount.set_absolute_offset(alt=alt)
        if "az" in absolute and (az := absolute["az"]):
            mount.set_absolute_offset(az=az)
    elif "relative" in data:
        relative = data["relative"]
        if "ra" in relative and (ra := relative["ra"]):
            mount.set_relative_offset(ra=ra)
        if "dec" in relative and (ra := relative["dec"]):
            mount.set_relative_offset(dec=ra)
        if "alt" in relative and (alt := relative["alt"]):
            mount.set_relative_offset(alt=alt)
        if "az" in relative and (az := relative["az"]):
            mount.set_relative_offset(az=az)
    elif "timedelta" in data:
        timedelta = data["timedelta"]
        ra_g = int(15 * timedelta / 3600)
        timedelta -= 3600 * ra_g / 15
        ra_m = int(timedelta / 60)
        timedelta -= ra_m * 60
        ra_s = timedelta
        ra = ra_g + ra_m / 60 + ra_s / 3600
        mount.set_relative_offset(ra=ra * units.deg)
    else:
        return jsonify({"error": "'absolute', 'relative' or 'timedelta'"}), 400

    return (
        jsonify(
            {
                "message": "ok",
                "offset": {
                    "ra": round(mount.get_offset().ra.deg, 6),
                    "dec": round(mount.get_offset().dec.deg, 6),
                },
            }
        ),
        200,
    )


@mount_bp.route("/run", methods=["GET"])
def mount_run():
    global mount
    if mount.get_running():
        return jsonify({"error": "already moving"}), 403

    if mount.get_location() is None:
        return jsonify({"error": "mount location is not set"}), 400

    if not mount.get_target():
        return jsonify({"error": "mount target is not set"}), 400

    bh = request.args.get("bh")
    if not bh:
        return jsonify({"error": "missing required argument bh"}), 400
    if bh not in ["follow", "transit", "route"]:
        return jsonify({"error": "bh must be 'follow', 'transit' or 'route'"}), 400
    if bh in ["transit", "route"] and not mount.get_offset():
        return jsonify({"error": f"mount offset must be set when bh is {bh}"}), 400

    thread = threading.Thread(target=lambda: mount.run(bh))
    thread.start()

    return jsonify({"message": "ok"}), 200


@mount_bp.route("/stop", methods=["GET"])
def mount_stop():
    global mount
    if not mount.get_running():
        return jsonify({"error": "already stopped"}), 403

    mount.stop()
    return jsonify({"message": "ok"}), 200


@mount_bp.route("/status", methods=["GET"])
def mount_status():
    global mount
    return (
        jsonify(
            {
                "location": mount.get_location(),
                "target": {
                    "ra": (
                        None
                        if mount.get_target() is None
                        else round(mount.get_target().ra.deg, 6)
                    ),
                    "dec": (
                        None
                        if mount.get_target() is None
                        else round(mount.get_target().dec.deg, 6)
                    ),
                },
                "offset": {
                    "ra": (
                        None
                        if mount.get_offset() is None
                        else round(mount.get_offset().ra.deg, 6)
                    ),
                    "dec": (
                        None
                        if mount.get_offset() is None
                        else round(mount.get_offset().dec.deg, 6)
                    ),
                },
                "position": {
                    "ra": (
                        None
                        if mount.get_position()[0] is None
                        else round(mount.get_position()[0], 6)
                    ),
                    "dec": (
                        None
                        if mount.get_position()[1] is None
                        else round(mount.get_position()[1], 6)
                    ),
                },
                "bh": mount.get_behavior(),
                "is_running": mount.get_running(),
            }
        ),
        200,
    )
