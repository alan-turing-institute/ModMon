
import pandas as pd
import numpy as np


def get_labels(idx):
    df = pd.read_csv("winequality-white.csv", sep=";")
    labels = df.loc[idx, "quality"]
    return labels


def correct_class(predictions, true_values):
    """Fraction of predictions that exactly matched the correct quality score.
    """
    pred_labels = predictions.idxmax(axis=1)
    df = pd.DataFrame({"true": true_values, "predicted": pred_labels})
    return (df["true"] == df["predicted"]).mean()


def mean_log_loss(predictions, true_values):
    labels = range(11)
    scores = []
    for label in labels:
        probabilities = predictions.loc[:, label]
        is_this_label = true_values == label
        probabilities = probabilities[is_this_label]
        scores.append(-np.log(probabilities).mean())
    return scores
    
    
if __name__ == "__main__":
    preds = pd.read_csv("predictions.csv", index_col="idx")
    preds.columns = preds.columns.astype(int)
    labels = get_labels(preds.index)
    
    score = correct_class(preds, labels)
    print("correct_class", score)
    score = mean_log_loss(preds, labels)
    print("log loss", score)
