import base64
import threading
import time
import datetime
import requests as req_lib
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins="*")

# ==========================================
# CONFIG
# ==========================================
API_KEY = "AIzaSyDZyTQNS2eO8wg6wQMPKTMKk8ffEhssVIs"

# ==========================================
# FAKE IMAGES for rooms A1, A2, B1, C1, C2
# B2 = audience webcam (sent from browser)
# ==========================================
FAKE_ROOM_IMAGES = {
    "A1": "https://images.unsplash.com/photo-1517502884422-41eaead166d4?w=640&q=80",
    "A2": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=640&q=80",
    "B1": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=640&q=80",
    "C1": "https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=640&q=80",
    "C2": "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=640&q=80",
}

fake_image_cache = {}

# ==========================================
# ROOM STATE
# ==========================================
room_states = {
    "A1": {"code": "A1", "name": "Conference Room A", "occupancy": 8,  "capacity": 12, "status": "occupied", "lights": True,  "ac": True,  "energy": 18, "confidence": 0.95, "source": "static"},
    "A2": {"code": "A2", "name": "Open Office A",     "occupancy": 24, "capacity": 40, "status": "occupied", "lights": True,  "ac": True,  "energy": 32, "confidence": 0.92, "source": "static"},
    "B1": {"code": "B1", "name": "Server Room",       "occupancy": 0,  "capacity": 4,  "status": "empty",    "lights": False, "ac": True,  "energy": 45, "confidence": 0.99, "source": "static"},
    "B2": {"code": "B2", "name": "Break Room",        "occupancy": 0,  "capacity": 20, "status": "waste",    "lights": True,  "ac": True,  "energy": 12, "confidence": 0.00, "source": "browser_webcam"},
    "C1": {"code": "C1", "name": "Lab Space",         "occupancy": 6,  "capacity": 15, "status": "occupied", "lights": True,  "ac": True,  "energy": 28, "confidence": 0.88, "source": "static"},
    "C2": {"code": "C2", "name": "Training Room",     "occupancy": 0,  "capacity": 30, "status": "waste",    "lights": True,  "ac": True,  "energy": 22, "confidence": 0.00, "source": "static"},
}

alerts = []


# ==========================================
# HELPERS
# ==========================================
def add_alert(alert_type, room_id, room_name, message):
    alerts.insert(0, {
        "type": alert_type,
        "room_id": room_id,
        "room_name": room_name,
        "message": message,
        "time": datetime.datetime.now().strftime("%H:%M"),
    })
    if len(alerts) > 20:
        alerts.pop()


def determine_status(occupancy, lights_on, ac_on):
    if occupancy > 0:
        return "occupied"
    elif lights_on or ac_on:
        return "waste"
    else:
        return "empty"


# ==========================================
# GOOGLE VISION AI — analyze base64 image
# Used by both /analyze (browser webcam)
# ==========================================
def call_google_vision(base64_image):
    """
    Send a base64 image to Google Vision API.
    Returns {"count": int, "confidence": float}
    """
    try:
        url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
        payload = {
            "requests": [{
                "image": {"content": base64_image},
                "features": [
                    {"type": "OBJECT_LOCALIZATION"},
                    {"type": "LABEL_DETECTION"},
                    {"type": "FACE_DETECTION"},
                ]
            }]
        }

        response = req_lib.post(url, json=payload, timeout=8)
        results = response.json()

        real_person_count = 0
        face_count = 0
        confidence = 0.0

        if "responses" in results:
            r = results["responses"][0]

            for obj in r.get("localizedObjectAnnotations", []):
                if obj["name"] == "Person":
                    real_person_count += 1
                    confidence = max(confidence, obj["score"])
                    print(f"   [Vision AI] Person found ({int(obj['score']*100)}% confidence)")

            face_count = len(r.get("faceAnnotations", []))

        # Priority: faces > body shapes
        final_count = face_count if face_count > 0 else real_person_count
        final_confidence = confidence if confidence > 0 else (0.85 if face_count > 0 else 0.0)

        print(f"   [Vision AI] Result: {final_count} people, confidence: {final_confidence}")
        return {"count": final_count, "confidence": round(final_confidence, 2)}

    except Exception as e:
        print(f"[Vision AI] Error: {e}")
        return {"count": -1, "confidence": 0.0}


# ==========================================
# FAKE IMAGE FETCHER
# ==========================================
def get_fake_image(room_id):
    if room_id in fake_image_cache:
        return fake_image_cache[room_id]
    url = FAKE_ROOM_IMAGES.get(room_id)
    if not url:
        return None
    try:
        r = req_lib.get(url, timeout=8)
        if r.status_code == 200:
            b64 = base64.b64encode(r.content).decode()
            fake_image_cache[room_id] = b64
            print(f"[Images] Cached {room_id} ✅")
            return b64
    except Exception as e:
        print(f"[Images] Failed {room_id}: {e}")
    return None


def preload_all_fake_images():
    print("[Images] Pre-loading fake room images...")
    for room_id in FAKE_ROOM_IMAGES:
        get_fake_image(room_id)
    print("[Images] All cached ✅")


# ==========================================
# API ROUTES
# ==========================================

@app.route("/rooms", methods=["GET"])
def get_rooms():
    return jsonify(list(room_states.values()))


@app.route("/alerts", methods=["GET"])
def get_alerts():
    return jsonify(alerts)


@app.route("/summary", methods=["GET"])
def get_summary():
    waste    = [r for r in room_states.values() if r["status"] == "waste"]
    occupied = [r for r in room_states.values() if r["status"] == "occupied"]
    return jsonify({
        "total_rooms": len(room_states),
        "occupied": len(occupied),
        "waste": len(waste),
        "waste_rooms": [r["code"] for r in waste],
    })


# ==========================================
# NEW: /analyze  — receives browser webcam frame
#
# Flutter sends:  { "room_id": "B2", "image_base64": "..." }
# Server returns: { "count": 2, "confidence": 0.91, "status": "occupied" }
#
# Flutter calls this every 5 seconds with a captured frame
# ==========================================
@app.route("/analyze", methods=["POST"])
def analyze_frame():
    data = request.get_json()

    if not data or "image_base64" not in data:
        return jsonify({"error": "Missing image_base64"}), 400

    room_id      = data.get("room_id", "B2").upper()
    base64_image = data["image_base64"]

    print(f"[Analyze] Received frame for room {room_id} ({len(base64_image)} bytes)")

    # Call Google Vision AI
    result = call_google_vision(base64_image)

    if result["count"] == -1:
        # Vision API failed — don't update state, return error
        return jsonify({"error": "Vision API unavailable", "count": 0, "confidence": 0}), 503

    count      = result["count"]
    confidence = result["confidence"]

    # Update room state
    old_status = room_states[room_id]["status"]
    new_status = determine_status(
        count,
        room_states[room_id]["lights"],
        room_states[room_id]["ac"],
    )

    room_states[room_id].update({
        "occupancy":   count,
        "confidence":  confidence,
        "status":      new_status,
        "source":      "browser_webcam",
    })

    # Trigger waste alert if status just changed
    if old_status != "waste" and new_status == "waste":
        add_alert(
            "WARNING",
            room_id,
            room_states[room_id]["name"],
            f"Room is empty but lights/AC still ON — energy waste detected by Vision AI.",
        )
        print(f"[Alert] ⚠️  Waste alert for {room_id}!")

    return jsonify({
        "room_id":    room_id,
        "count":      count,
        "confidence": confidence,
        "status":     new_status,
        "timestamp":  datetime.datetime.now().strftime("%H:%M:%S"),
    })


# ==========================================
# SNAPSHOT — fake images for non-webcam rooms
# B2 snapshot now comes from Flutter directly
# (browser already has the frame)
# ==========================================
@app.route("/snapshot/<room_id>", methods=["GET"])
def get_snapshot(room_id):
    room_id = room_id.upper()
    room    = room_states.get(room_id)

    if not room:
        return jsonify({"error": "Room not found"}), 404

    # B2 = browser webcam, Flutter handles the image itself
    if room_id == "B2":
        return jsonify({
            "room_id":      room_id,
            "room_name":    room["name"],
            "image_base64": None,           # Flutter uses its own captured frame
            "image_source": "browser_webcam",
            "is_live":      True,
            "occupancy":    room["occupancy"],
            "capacity":     room["capacity"],
            "status":       room["status"],
            "confidence":   room["confidence"],
            "timestamp":    datetime.datetime.now().strftime("%H:%M:%S"),
        })

    # All other rooms = fake stock photo
    image_b64 = get_fake_image(room_id)
    if not image_b64:
        return jsonify({"error": "Image unavailable"}), 503

    return jsonify({
        "room_id":      room_id,
        "room_name":    room["name"],
        "image_base64": image_b64,
        "image_source": "simulated_feed",
        "is_live":      False,
        "occupancy":    room["occupancy"],
        "capacity":     room["capacity"],
        "status":       room["status"],
        "confidence":   room["confidence"],
        "timestamp":    datetime.datetime.now().strftime("%H:%M:%S"),
    })


# ==========================================
# START
# ==========================================
if __name__ == "__main__":
    threading.Thread(target=preload_all_fake_images, daemon=True).start()

    print("=" * 55)
    print("[Server] ✅ GreenPulse Vision AI Backend (Cloud Mode)")
    print("[Server] 📷 B2 = audience browser webcam")
    print("[Server] 🖼  Other rooms = simulated feed")
    print("[Server] 🌐 Running at http://localhost:5000")
    print("[Server] Routes: /rooms  /analyze  /snapshot/<id>  /alerts")
    print("=" * 55)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
