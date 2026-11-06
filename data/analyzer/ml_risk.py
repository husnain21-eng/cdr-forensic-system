"""Machine Learning Risk Engine using Random Forest."""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import numpy as np


class MLRiskEngine:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self._train_model()

    def _train_model(self):
        """Train the model on synthetic historical data."""
        # Features: [Total Calls, Night Call Ratio, Short Call Ratio]
        X_train = np.array([
            [10, 0.05, 0.1],  # Low risk (10 calls, mostly day, long duration)
            [150, 0.8, 0.6],  # High risk (many calls, night, short pings)
            [5, 0.0, 0.0],  # Low risk
            [300, 0.9, 0.8],  # High risk
            [40, 0.2, 0.2],  # Medium/Low
            [90, 0.7, 0.5],  # High risk
        ])

        # Labels: 0 = Low Risk, 1 = High Risk
        y_train = np.array([0, 1, 0, 1, 0, 1])

        self.model.fit(X_train, y_train)

    def predict_risk(self, df: pd.DataFrame) -> tuple[int, str]:
        """Predict the risk score (0-100) and level based on real data."""
        if df.empty:
            return 0, "UNKNOWN"

        total = len(df)

        # Calculate features
        night_calls = len(df[df["hour"].isin([23, 0, 1, 2, 3, 4, 5])]) if "hour" in df.columns else 0
        night_ratio = night_calls / total if total > 0 else 0

        short_calls = len(df[df["duration_sec"] <= 5]) if "duration_sec" in df.columns else 0
        short_ratio = short_calls / total if total > 0 else 0

        # Format the features for the model
        features = np.array([[total, night_ratio, short_ratio]])

        # Predict (0 = Low, 1 = High)
        prediction = self.model.predict(features)[0]

        # Get the probability of being High Risk
        probabilities = self.model.predict_proba(features)[0]
        risk_probability = probabilities[1]  # Probability of class 1

        score = int(risk_probability * 100)

        if score >= 75:
            level = "CRITICAL (AI)"
        elif score >= 40:
            level = "ELEVATED (AI)"
        else:
            level = "LOW (AI)"

        return score, level