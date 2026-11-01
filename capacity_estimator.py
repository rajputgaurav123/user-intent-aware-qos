import subprocess
import json


def estimate_link_capacity(interface="veth-test"):
    try:
        result = subprocess.check_output(
            ["tc", "-j", "qdisc", "show", "dev", interface],
            text=True
        )

        qdiscs = json.loads(result)

        for qdisc in qdiscs:
            if qdisc.get("kind") == "tbf":
                rate_bytes = qdisc["options"]["rate"]
                capacity_mbps = rate_bytes * 8 / 1_000_000

                return capacity_mbps

        return None

    except Exception as error:
        print("Capacity detection error:", error)
        return None


if __name__ == "__main__":
    capacity = estimate_link_capacity()

    if capacity is not None:
        print(f"Detected link capacity: {capacity:.2f} Mbps")
    else:
        print("No configured TBF capacity found.")

