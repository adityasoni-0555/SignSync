"""
STEP 3 — Train the Classifier

Run this after collect_data.py has produced gesture_data.csv.

Usage: python train_model.py
Output: model.pkl (trained classifier, ready for live_app.py)
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import pickle

CSV_PATH = "gesture_data.csv"
MODEL_OUT = "model.pkl"

def main():
    df = pd.read_csv(CSV_PATH)
    X = df.drop(columns=["label"])
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Test accuracy: {acc:.2%}\n")
    print(classification_report(y_test, preds))

    with open(MODEL_OUT, "wb") as f:
        pickle.dump(clf, f)
    print(f"Model saved to {MODEL_OUT}")

    if acc < 0.90:
        print("\nAccuracy below 90% — consider:")
        print("- Recording more samples per gesture (aim 50-80)")
        print("- Making gestures more visually distinct from each other")
        print("- Checking for mislabeled rows in the CSV")

if __name__ == "__main__":
    main()
