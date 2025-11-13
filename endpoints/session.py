import uuid
from pathlib import Path
from flask import jsonify, Blueprint
from SingletonSID import SingletonSID
from classes.DeviceInfo import DeviceInfo

session_bp = Blueprint(Path(__file__).stem, __name__)


@session_bp.route("/acquire", methods=["GET"])
def session_acquire():
    if not SingletonSID().SID:
        SingletonSID().SID = uuid.uuid4()
        
        device_id = DeviceInfo.get_identifier()         # get device hardware info
        SingletonSID().DEVICE_ID = device_id            # save info
        mount = DeviceInfo.select_mount(device_id)      # select the type

        print(f"[SESSION] Nuova sessione: SID={SingletonSID().SID} DEVICE={device_id} MOUNT={mount.__class__.__name__}")

        return jsonify({
            "session_id": str(SingletonSID().SID),
            "device_id": device_id,
            "mount_type": mount.__class__.__name__
        }), 200

    return jsonify({"message": "session in use"}), 403


@session_bp.route("/release", methods=["GET"])
def session_release():
    if SingletonSID().SID:
        SingletonSID().SID = None
        SingletonSID().DEVICE_ID = None   # reset 
        return jsonify({"message": "ok"}), 200

    return jsonify({"message": "cannot release an empty session"}), 403


@session_bp.route("/info", methods=["GET"])
def session_info():
    sid = SingletonSID().SID
    device = SingletonSID().DEVICE_ID

    if not sid:
        return jsonify({
            "session_id": None,
            "device_id": None,
            "status": "empty"
        }), 200

    return jsonify({
        "session_id": str(sid),
        "device_id": device,
        "status": "active"
    }), 200


