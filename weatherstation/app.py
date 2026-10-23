from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from .ble_profile import CHARACTERISTICS, get_profile
from .model import SENSOR_UNITS, Station
from .mqtt_transport import MqttTransport

ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger("weatherstation")


def create_app(config_path: Path | None = None):
    station = Station(config_path or ROOT / "config.json")
    transport = MqttTransport(station, station.update_config)
    app = Flask(__name__, static_folder=None)
    app.config["STATION"] = station
    app.config["MQTT"] = transport
    app.config["RATE_BUCKETS"] = {}
    app.config["RATE_LIMIT_PER_MINUTE"] = 60
    app.config["RATE_LOCK"] = threading.Lock()

    @app.before_request
    def rate_limit():
        if not request.path.startswith("/api/"):
            return None
        now = time.monotonic()
        key = request.remote_addr or "unknown"
        with app.config["RATE_LOCK"]:
            count, start = app.config["RATE_BUCKETS"].get(key, (0, now))
            if now - start >= 60:
                count, start = 0, now
            if count >= app.config["RATE_LIMIT_PER_MINUTE"]:
                return jsonify({"error": "rate limit exceeded", "limit_per_minute": 60}), 429
            app.config["RATE_BUCKETS"][key] = (count + 1, start)
        return None

    @app.after_request
    def cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Max-Age"] = "600"
        return response

    @app.route("/api/<path:_path>", methods=["OPTIONS"])
    def options(_path):
        return ("", 204)

    @app.get("/")
    def index():
        return send_from_directory(ROOT / "web", "index.html")

    @app.get("/api/sensors")
    def get_sensors():
        return jsonify(station.snapshot())

    @app.get("/api/sensors/<sensor_type>")
    def get_sensor(sensor_type: str):
        if sensor_type not in SENSOR_UNITS:
            return jsonify({"error": "unknown sensor type", "available": list(SENSOR_UNITS)}), 404
        sample = station.snapshot()
        return jsonify({"device_id": sample["device_id"], "timestamp": sample["timestamp"],
                        "sequence": sample["sequence"], "sensor": sensor_type,
                        **sample["sensors"][sensor_type]})

    @app.get("/api/history")
    def get_history():
        try:
            minutes = int(request.args.get("minutes", "60"))
            return jsonify({"minutes": minutes, "count": len(station.history(minutes)),
                            "samples": station.history(minutes)})
        except (ValueError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400

    @app.post("/api/config")
    def post_config():
        values = request.get_json(silent=True)
        if not isinstance(values, dict):
            return jsonify({"error": "request body must be a JSON object"}), 400
        try:
            config = station.update_config(values)
            mqtt = app.config["MQTT"]
            if "interval_seconds" in values:
                mqtt._publish(f"{mqtt.root}/config/interval", str(config["interval_seconds"]), retain=True)
            if "location" in values:
                mqtt._publish(f"{mqtt.root}/config/location", config["location"], retain=True)
            if "calibration" in values:
                mqtt._publish(f"{mqtt.root}/config/calibration", json.dumps(values["calibration"]), retain=True)
            return jsonify({"ok": True, "config": config})
        except (ValueError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400

    @app.get("/api/status")
    def get_status():
        cfg = station.config_snapshot()
        return jsonify({"device_id": cfg["device_id"], "location": cfg["location"],
                        "uptime_seconds": station.diagnostics()["uptime_seconds"],
                        "mqtt_connected": transport.connected.is_set(),
                        "mqtt_broker": f"{cfg['mqtt']['host']}:{cfg['mqtt']['port']}",
                        "ble": "GATT profile available; physical radio provided by ESP32 firmware",
                        "last_sensor_update": station.snapshot()["timestamp"]})

    @app.get("/api/diagnostics")
    def get_diagnostics():
        result = station.diagnostics()
        result["connections"] = station.connection_stats.copy()
        result["protocols"] = {"mqtt": "connected" if transport.connected.is_set() else "reconnecting",
                               "http": "online", "ble": "profile emulator (no host BLE adapter required)"}
        return jsonify(result)

    @app.get("/api/dashboard")
    def dashboard_data():
        """One-call dashboard snapshot so polling stays under the demo rate limit."""
        cfg = station.config_snapshot()
        diagnostic = station.diagnostics()
        return jsonify({
            "sensors": station.snapshot(),
            "status": {
                "device_id": cfg["device_id"], "location": cfg["location"],
                "uptime_seconds": diagnostic["uptime_seconds"],
                "mqtt_connected": transport.connected.is_set(),
                "mqtt_broker": f"{cfg['mqtt']['host']}:{cfg['mqtt']['port']}",
                "last_sensor_update": station.snapshot()["timestamp"],
            },
            "diagnostics": {**diagnostic, "connections": station.connection_stats.copy()},
            "history": station.history(60),
            "config": cfg,
            "ble_profile": get_profile(),
        })

    @app.get("/api/ble/profile")
    def ble_profile():
        return jsonify(get_profile())

    @app.get("/api/ble/read/<characteristic>")
    def ble_read(characteristic: str):
        if characteristic not in CHARACTERISTICS:
            return jsonify({"error": "unknown characteristic", "available": list(CHARACTERISTICS)}), 404
        station.record_ble_read()
        cfg = station.config_snapshot()
        snapshot = station.snapshot()
        if characteristic in SENSOR_UNITS:
            value = snapshot["sensors"][characteristic]
        elif characteristic == "interval_seconds":
            value = {"value": cfg["interval_seconds"], "unit": "s"}
        elif characteristic == "location":
            value = {"value": cfg["location"], "unit": ""}
        elif characteristic == "calibration":
            value = {"value": cfg["calibration"], "unit": "JSON offsets"}
        else:
            value = {"value": station.diagnostics(), "unit": "JSON"}
        return jsonify({"characteristic": characteristic, **value})

    @app.post("/api/ble/write/<characteristic>")
    def ble_write(characteristic: str):
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or "value" not in body:
            return jsonify({"error": "body must contain value"}), 400
        try:
            if characteristic == "interval_seconds":
                station.update_config({"interval_seconds": body["value"]})
            elif characteristic == "location":
                station.update_config({"location": body["value"]})
            elif characteristic == "calibration":
                station.update_config({"calibration": body["value"]})
            else:
                return jsonify({"error": "characteristic is read-only or unknown"}), 400
            station.record_ble_write()
            config = station.config_snapshot()
            return jsonify({"ok": True, "config": config, "transport": "desktop GATT-profile emulator"})
        except (ValueError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400

    @app.get("/api/docs")
    def api_docs():
        # Generate the endpoint list from Flask's registered routes on each request.
        paths: dict[str, Any] = {}
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith("/api/") and rule.rule != "/api/<path:_path>":
                methods = sorted(method for method in rule.methods if method in {"GET", "POST"})
                paths[rule.rule] = {method.lower(): {"summary": rule.endpoint.replace("_", " ")} for method in methods}
        return jsonify({"openapi": "3.0.3", "info": {"title": "Weather Station API", "version": "1.0.0"}, "paths": paths})

    return app, station, transport


def run_server():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app, station, transport = create_app()
    stop = threading.Event()

    def sampling_loop():
        while not stop.is_set():
            sample = station.sample()
            transport.publish_snapshot(sample)
            LOG.info("T %.1f°C | RH %.1f%% | P %.1f hPa | light %.0f lx | AQI %.0f | wind %.1f m/s | MQTT %s",
                     sample["sensors"]["temperature"]["value"], sample["sensors"]["humidity"]["value"],
                     sample["sensors"]["pressure"]["value"], sample["sensors"]["light"]["value"],
                     sample["sensors"]["air_quality"]["value"], sample["sensors"]["wind_speed"]["value"],
                     "online" if transport.connected.is_set() else "retrying")
            stop.wait(station.config_snapshot()["interval_seconds"])

    transport.start()
    worker = threading.Thread(target=sampling_loop, name="weather-sampler", daemon=True)
    worker.start()
    cfg = station.config_snapshot()
    LOG.info("REST dashboard: http://%s:%s", cfg.get("http_host", "127.0.0.1"), cfg.get("http_port", 5000))
    try:
        app.run(host=cfg.get("http_host", "127.0.0.1"), port=int(cfg.get("http_port", 5000)), threaded=True, use_reloader=False)
    finally:
        stop.set()
        transport.stop()

