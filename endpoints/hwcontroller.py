from flask import jsonify, request, Blueprint
from drivers.MonitorMount import MonitorMount

hwcontroller_bp = Blueprint("hwcontroller", __name__)
mount = MonitorMount()


@hwcontroller_bp.route("/move", methods=["POST"])
def move_servo():
    ch = int(request.args.get("ch", 0))
    angle = float(request.args.get("angle", 90))
    ok, err = mount.move_servo(ch, angle)
    if not ok:
        return jsonify({"ok": False, "error": err}), 400
    return jsonify({"ok": True, "ch": ch, "angle": angle})


@hwcontroller_bp.route("/stop", methods=["POST"])
def stop():
    mount.stop()
    return jsonify({"ok": True, "message": "Servos stopped"})


@hwcontroller_bp.route("/status", methods=["GET"])
def status():
    return jsonify(
        {
            "running": mount.get_running(),
            "position": mount.get_position(),
            "info": mount.get_info(),
        }
    )
