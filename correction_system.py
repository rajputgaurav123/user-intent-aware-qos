
import csv
import os
from datetime import datetime
from collections import Counter

FEEDBACK_FILE = "classifier_feedback.csv"

CLASSES = ["interactive", "streaming", "bulk"]


def get_confidence_level(confidence):
    if confidence >= 0.85:
        return "High"
    elif confidence >= 0.60:
        return "Medium"
    return "Low"


def save_feedback(predicted_class, confidence,
                  corrected_class, reason):

    file_exists = os.path.exists(FEEDBACK_FILE)

    with open(FEEDBACK_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "predicted_class",
                "confidence",
                "confidence_level",
                "corrected_class",
                "was_corrected",
                "reason",
                "feedback_status"
            ])

        writer.writerow([
            datetime.now().isoformat(),
            predicted_class,
            confidence,
            get_confidence_level(confidence),
            corrected_class,
            predicted_class != corrected_class,
            reason,
            "pending_review"
        ])

    print("\nFeedback saved successfully!")


def review_prediction():

    print("\n=== TRAFFIC CLASSIFICATION REVIEW ===")

    predicted_class = input(
        "Enter ML predicted class (interactive/streaming/bulk): "
    ).strip().lower()

    if predicted_class not in CLASSES:
        print("Invalid predicted class!")
        return

    try:
        confidence = float(
            input("Enter model confidence (0 to 1): ")
        )

        if not 0 <= confidence <= 1:
            print("Confidence must be between 0 and 1.")
            return

    except ValueError:
        print("Please enter a valid number.")
        return

    print("\nModel Prediction:", predicted_class)
    print("Confidence:", round(confidence * 100, 2), "%")
    print("Confidence Level:", get_confidence_level(confidence))

    print("\nSelect the correct traffic class:")

    for number, traffic_class in enumerate(CLASSES, start=1):
        print(f"{number}. {traffic_class}")

    try:
        choice = int(input("\nEnter choice (1-3): "))

        if choice not in [1, 2, 3]:
            print("Invalid choice!")
            return

    except ValueError:
        print("Please enter a valid number.")
        return

    corrected_class = CLASSES[choice - 1]

    reason = input("Reason for correction (or press Enter): ")

    save_feedback(
        predicted_class,
        confidence,
        corrected_class,
        reason
    )

    if predicted_class == corrected_class:
        print("Result: Prediction confirmed by operator.")
    else:
        print("Result: Model prediction corrected by operator.")


def show_feedback_report():

    if not os.path.exists(FEEDBACK_FILE):
        print("\nNo feedback records found.")
        return

    with open(FEEDBACK_FILE, "r", newline="") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        print("\nNo feedback records found.")
        return

    total = len(rows)
    corrections = sum(
        row["was_corrected"] == "True" for row in rows
    )

    errors = Counter(
        f'{row["predicted_class"]} -> {row["corrected_class"]}'
        for row in rows
        if row["was_corrected"] == "True"
    )

    print("\n=== FEEDBACK IMPACT REPORT ===")
    print("Total reviewed predictions:", total)
    print("Corrections made:", corrections)
    print("Predictions confirmed:", total - corrections)
    print("Correction rate:", round(corrections / total * 100, 2), "%")

    print("\nMost common classification errors:")

    if errors:
        for mistake, count in errors.most_common():
            print(f"{mistake}: {count} times")
    else:
        print("No corrections recorded.")

    pending = sum(
        row["feedback_status"] == "pending_review"
        for row in rows
    )

    print("\nFeedback awaiting verification:", pending)


def main():

    while True:
        print("\n================================")
        print(" USER-INTENT-AWARE QoS")
        print(" CLASSIFIER CORRECTION SYSTEM")
        print("================================")
        print("1. Review a prediction")
        print("2. View feedback report")
        print("3. Exit")

        choice = input("\nChoose option: ").strip()

        if choice == "1":
            review_prediction()

        elif choice == "2":
            show_feedback_report()

        elif choice == "3":
            print("Correction system closed.")
            break

        else:
            print("Invalid option! Try again.")


if __name__ == "__main__":
    main()

