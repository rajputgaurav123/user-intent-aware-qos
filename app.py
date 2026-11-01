from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from policy_engine import choose_policy
import joblib
import pandas as pd
app = Flask(__name__)

VALID_INTENTS = {"video_call", "gaming", "streaming", "download"}
VALID_CONDITIONS = {"low", "moderate", "high", "critical"}

@app.get("/")
def dashboard():
    return send_from_directory("results", "dashboard.html")

@app.get("/throughput_comparison.png")
def comparison_chart():
    return send_from_directory("results", "throughput_comparison.png")

@app.get("/api/experiment-results")
def experiment_results():
    try:
        csv_path = Path(__file__).resolve().parent / "combined_qos_results.csv"
        df = pd.read_csv(csv_path)
        df = df.astype(object).where(pd.notna(df), None)
        return jsonify({"rows": df.to_dict(orient="records")})
    except (OSError, ValueError) as error:
        app.logger.warning("Experiment results could not be loaded: %s", error)
        return jsonify({"error": "Experiment results could not be loaded."}), 500


@app.get("/api/health")
def health():
    return jsonify({
        "status": "online",
        "service": "User-Intent-Aware Adaptive QoS Engine"
    })
@app.get("/api/ml-model")
def ml_model_details():
    try:
        import random

        model_path = Path(__file__).resolve().parent / "traffic_classifier_2700.joblib"
        model = joblib.load(model_path)

        profiles = {
            "interactive": {
                "mean": [18.24, 22.18, 6.14, 0.51],
                "min": [1, 5, 1, 0],
                "max": [55.062, 52.318, 18.715, 1.724]
            },
            "streaming": {
                "mean": [32.93, 55.58, 12.32, 0.83],
                "min": [2, 5, 1, 0],
                "max": [77.525, 141.351, 38.351, 3.026]
            },
            "bulk": {
                "mean": [56.75, 76.28, 18.28, 1.20],
                "min": [5, 5, 1, 0],
                "max": [100, 180, 50, 5]
            }
        }

        profile = random.choice(list(profiles.values()))

        feature_names = [
            "throughput_mbps",
            "latency_ms",
            "jitter_ms",
            "packet_loss_pct"
        ]

        values = []
        for mean, minimum, maximum in zip(
            profile["mean"], profile["min"], profile["max"]
        ):
            value = mean * random.uniform(0.85, 1.15)
            values.append(round(max(minimum, min(value, maximum)), 2))

        input_data = pd.DataFrame([values], columns=feature_names)

        prediction = model.predict(input_data)[0]
        probabilities = model.predict_proba(input_data)[0]

        class_probabilities = {
            str(label): round(float(probability) * 100, 2)
            for label, probability in zip(model.classes_, probabilities)
        }

        return jsonify({
            "success": True,
            "model_type": type(model).__name__,
            "training_data": "Synthetic dataset",
            "real_world_validated": False,
            "predicted_class": str(prediction),
            "confidence_percent": round(float(max(probabilities)) * 100, 2),
            "class_probabilities": class_probabilities,
            "input_features": feature_names,
            "features": {
                name: value for name, value in zip(feature_names, values)
            }
        })

    except (OSError, ValueError) as error:
        app.logger.warning("ML prediction failed: %s", error)
        return jsonify({
            "success": False,
            "error": "The ML prediction could not be completed."
        }), 500

@app.post("/api/apply")
def apply_policy():
    data = request.get_json(silent=True) or {}
    intent = data.get("intent", "")
    condition = data.get("congestion", "moderate")

    if intent not in VALID_INTENTS:
        return jsonify({"error": "Invalid intent"}), 400
    if condition not in VALID_CONDITIONS:
        return jsonify({"error": "Invalid congestion condition"}), 400

    allocation = choose_policy(intent, condition)

    return jsonify({
        "success": True,
        "simulation_only": True,
        "network_settings_changed": False,
        "intent": intent,
        "congestion": condition,
        "allocation": allocation,
        "message": "Policy simulated only; no network settings were changed."
    })


@app.post("/api/policy")
def get_policy():
    data = request.get_json(silent=True) or {}
    intent = data.get("intent", "")
    condition = data.get("congestion", "moderate")

    if intent not in VALID_INTENTS:
        return jsonify({"error": "Invalid intent"}), 400

    if condition not in VALID_CONDITIONS:
        return jsonify({"error": "Invalid congestion condition"}), 400

    allocation = choose_policy(intent, condition)

    return jsonify({
        "intent": intent,
        "congestion": condition,
        "allocation": allocation,
        "total_percent": sum(allocation.values()),
        "applied_to_network": False,
        "message": "Policy calculated successfully; not yet applied."
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
