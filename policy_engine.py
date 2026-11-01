def choose_policy(user_intent, congestion_level):
    policies = {
        "video_call": {
            "interactive": 65,
            "streaming": 25,
            "bulk": 10
        },
        "gaming": {
            "interactive": 70,
            "streaming": 20,
            "bulk": 10
        },
        "streaming": {
            "interactive": 20,
            "streaming": 70,
            "bulk": 10
        },
        "download": {
            "interactive": 20,
            "streaming": 20,
            "bulk": 60
        }
    }

    if user_intent not in policies:
        raise ValueError("Unknown user intent")

    adjustments = {
        "low": 0,
        "moderate": 5,
        "high": 10,
        "critical": 15
    }

    if congestion_level not in adjustments:
        raise ValueError("Unknown congestion level")

    allocation = policies[user_intent].copy()
    adjustment = adjustments[congestion_level]

    target = {
        "video_call": "interactive",
        "gaming": "interactive",
        "streaming": "streaming",
        "download": "bulk"
    }[user_intent]

    donors = {
        "video_call": ["bulk", "streaming"],
        "gaming": ["bulk", "streaming"],
        "streaming": ["bulk", "interactive"],
        "download": ["streaming", "interactive"]
    }[user_intent]

    remaining = adjustment

    for donor in donors:
        available = max(0, allocation[donor] - 5)
        transfer = min(remaining, available)

        allocation[donor] -= transfer
        allocation[target] += transfer
        remaining -= transfer

        if remaining == 0:
            break

    return allocation
