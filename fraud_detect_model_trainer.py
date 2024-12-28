# fraud_detect_model_trainer.py

import random
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

def generate_synthetic_data(n=1000):
    X, y = [], []
    for _ in range(n):
        f1 = random.random() * 10
        f2 = random.random() * 50
        # Simple rule: label = 1 (fraud) if features exceed thresholds
        label = 1 if (f1 > 7 and f2 > 30) else 0
        X.append([f1, f2])
        y.append(label)
    return np.array(X), np.array(y)

def main():
    X, y = generate_synthetic_data(n=1000)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X_train, y_train)
    acc = clf.score(X_test, y_test)
    print("Accuracy:", acc)

    joblib.dump(clf, "fraud_model.pkl")
    print("Saved model to fraud_model.pkl")

if __name__ == "__main__":
    main()
