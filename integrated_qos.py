import joblib
import pandas as pd

from apply_tc_policy import apply_tc_policy
from measure_network import measure_network
from policy_engine import choose_policy
from qos_correction import review_and_save
FEATURES = [
    "throughput_mbps",
    "latency_ms",
    "jitter_ms",
    "packet_loss_pct"
]

print("\n=== User-Intent-Aware Adaptive QoS Engine ===")

intents = {
    "1": ("Video Call", "video_call"),
    "2": ("Gaming", "gaming"),
    "3": ("Streaming", "streaming"),
    "4": ("Download", "download")
}

for key, (label, _) in intents.items():
    print(f"{key}. {label}")

choice = input("\nChoose your priority (1-4): ").strip()

if choice not in intents:
    print("Invalid choice. Please run again.")
    raise SystemExit

intent_name, user_intent = intents[choice]

# Load the trained classifier
model = joblib.load("traffic_classifier_2700.joblib")

# Automatically measure the network
metrics = measure_network()

# Check whether all required measurements are available
if any(metrics.get(feature) is None for feature in FEATURES):
    print("\nSome measurements are unavailable.")
    print("Cannot make a reliable ML prediction. Please try again.")
    raise SystemExit

# Predict traffic class using measured features
sample = pd.DataFrame(
    [[metrics[feature] for feature in FEATURES]],
    columns=FEATURES
)

predicted_class = model.predict(sample)[0]

confidence = None
review_and_save(predicted_class, confidence)
if hasattr(model, "predict_proba"):
    confidence = float(max(model.predict_proba(sample)[0]))

# Initial heuristic based on measured latency, jitter and packet loss.
# These thresholds are assumptions, not measured link utilization.
latency = metrics["latency_ms"]
jitter = metrics["jitter_ms"]
packet_loss = metrics["packet_loss_pct"]

if packet_loss >= 5 or latency >= 150:
    congestion_level = "critical"
elif packet_loss >= 2 or latency >= 100:
    congestion_level = "high"
elif latency >= 70 or jitter >= 20:
    congestion_level = "moderate"
else:
    congestion_level = "low"

# Select a policy based on user intent and estimated network condition
allocation = choose_policy(user_intent, congestion_level)

print("\n=== QoS Decision Report ===")
print("User priority:", intent_name)
print("ML-predicted traffic class:", predicted_class)

if confidence is not None:
    print(f"Model confidence: {confidence * 100:.1f}%")

print("\n--- Measured Network Metrics ---")
print(f"Download throughput estimate: {metrics['throughput_mbps']:.2f} Mbps")
print(f"Average latency: {latency:.2f} ms")
print(f"Latency variation: {jitter:.2f} ms")
print(f"Packet loss: {packet_loss:.1f}%")

print("\nEstimated network condition:", congestion_level.title())
print("(Based on initial latency, jitter and packet-loss thresholds.)")

print("\n--- Proposed Traffic Allocation ---")
for traffic, percentage in allocation.items():
    print(f"{traffic}: {percentage}%")

print("Total allocation:", sum(allocation.values()), "%")
print("\n--- Applying QoS Policy ---")

try:
    apply_tc_policy(allocation, user_intent=user_intent)
except Exception as error:
    print("Could not apply QoS policy:", error)
    print("Check that veth-test and its HTB classes exist.")
print("\nNote: The classifier was trained on synthetic data.")
print("This is an experimental prediction, not validated real-world classification.")
print("QoS applied only to isolated test interface: veth-test.")
print("Real Internet interface settings were not changed.")
