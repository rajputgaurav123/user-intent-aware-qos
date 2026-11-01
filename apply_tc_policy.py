
import subprocess

def apply_tc_policy(allocation, interface="veth-test",
                    capacity_mbps=None, user_intent="video_call"):
    if capacity_mbps is None:
        capacity_mbps = get_configured_capacity(interface)
    classes = {
        "interactive": "1:10",
        "streaming": "1:20",
        "bulk": "1:30"
    }

    if set(allocation) != set(classes):
        raise ValueError("Unexpected traffic allocation")

    if sum(allocation.values()) != 100:
        raise ValueError("Allocation must total 100%")

    if any(v < 5 for v in allocation.values()):
        raise ValueError("Each traffic class must receive at least 5%")

    intent_class = {
        "video_call": "1:10",
        "gaming": "1:10",
        "streaming": "1:20",
        "download": "1:30"
    }

    if user_intent not in intent_class:
        raise ValueError("Unknown user intent")

    # Update bandwidth limits on the isolated test interface.
    for traffic, class_id in classes.items():
        rate_kbit = round(
            capacity_mbps * 1000 * allocation[traffic] / 100
        )
        subprocess.run([
            "sudo", "-n", "tc", "class", "change",
            "dev", interface, "parent", "1:1",
            "classid", class_id, "htb",
            "rate", f"{rate_kbit}kbit",
            "ceil", f"{rate_kbit}kbit"
        ], check=True)

    # Clear our previous filters at priorities 1-3.
    for pref in (1, 2, 3):
        subprocess.run([
            "sudo", "-n", "tc", "filter", "del",
            "dev", interface, "protocol", "ip",
            "parent", "1:", "pref", str(pref)
        ], check=False, capture_output=True, text=True)

    # Each test port always represents its own traffic class.
    port_class = {
        5201: "1:10",  # Interactive
        5203: "1:20",  # Streaming
        5202: "1:30"   # Bulk
    }

    for pref, (port, class_id) in enumerate(port_class.items(), start=1):
        subprocess.run([
            "sudo", "-n", "tc", "filter", "add",
            "dev", interface, "protocol", "ip",
            "parent", "1:", "prio", str(pref),
            "flower", "ip_proto", "tcp",
            "dst_port", str(port),
            "classid", class_id
        ], check=True)

    print(f"QoS policy applied to {interface}")
    print(f"Selected user intent: {user_intent}")
    print(f"Intent's priority class: {intent_class[user_intent]}")

    for traffic, percentage in allocation.items():
        print(f"{traffic}: {percentage}%")

def rollback_policy(interface="veth-test", capacity_mbps=None):
    if capacity_mbps is None:
        capacity_mbps = get_configured_capacity(interface)
    # Equal-share baseline: one-third capacity per class
    rate_mbps = capacity_mbps / 3

    classes = ["1:10", "1:20", "1:30"]

    for class_id in classes:
        subprocess.run([
            "sudo", "-n", "tc", "class", "change",
            "dev", interface, "parent", "1:1",
            "classid", class_id, "htb",
            "rate", f"{rate_mbps:.2f}mbit",
            "ceil", f"{rate_mbps:.2f}mbit"
        ], check=True)

    print(
        f"Equal-share baseline restored: "
        f"{rate_mbps:.2f} Mbps per class "
        f"(total configured capacity: {capacity_mbps} Mbps)."
    )
def get_configured_capacity(interface="veth-test"):
    result = subprocess.run(
        ["sudo", "-n", "tc", "class", "show",
         "dev", interface],
        capture_output=True,
        text=True,
        check=True,
    )

    for line in result.stdout.splitlines():
        if "class htb 1:1 root" in line:
            for i, word in enumerate(line.split()):
                if word == "rate" and i + 1 < len(line.split()):
                    value = line.split()[i + 1]
                    if value.endswith("Mbit"):
                        return float(value[:-4])
                    if value.endswith("Kbit"):
                        return float(value[:-4]) / 1000

    raise RuntimeError("Could not detect HTB root capacity")
