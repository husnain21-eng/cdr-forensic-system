"""Backtest the Markov Chain prediction accuracy across the entire test set."""
import pandas as pd
from data.loader import load_single_file
from data.analyzer.markov import predict_next_call

def main():
    file_path = r'C:\Users\MS\Downloads\New CDR\923076085035.xlsx'
    print(f"Loading data from: {file_path}\n")

    df = load_single_file(file_path).dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    # Split data (80% train, 20% test)
    split_index = int(len(df) * 0.8)

    correct_predictions = 0
    total_predictions = 0

    print(f"Running iterative backtest on {len(df) - split_index} test records...")
    print("(This might take a few seconds)\n")

    # Loop through every hidden record, one by one
    for i in range(split_index, len(df) - 1):
        train_slice = df.iloc[:i]
        actual_next = str(df.iloc[i]["party_b"]).strip()  # <-- Added .strip() to remove spaces!

        preds = predict_next_call(train_slice)
        if not preds.empty:
            predicted_next = str(preds.iloc[0]["Predicted Next Call"]).strip()
            total_predictions += 1
            if predicted_next == actual_next:
                correct_predictions += 1

    if total_predictions > 0:
        accuracy = (correct_predictions / total_predictions) * 100
        print(f"\n--- FINAL ACCURACY SCORE ---")
        print(f"Predictions Made: {total_predictions}")
        print(f"Correct Guesses:  {correct_predictions}")
        print(f"Accuracy:         {accuracy:.2f}%")
    else:
        print("Not enough data to run iterative tests.")

if __name__ == "__main__":
    main()