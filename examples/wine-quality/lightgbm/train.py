import argparse
from datetime import datetime
import pandas as pd
import lightgbm as lgb


def train(start_idx, end_idx):
    print("loading data...")
    df = pd.read_csv("winequality-white.csv", sep=";")
    print(df.head())
    print(len(df), "rows")

    # extract training rows from data
    df = df.iloc[start_idx : (end_idx + 1)]
    n_rows = len(df)
    print(n_rows, "rows between start idx", start_idx, "and end idx", end_idx)

    # create lightgbm train and validation datasets
    predict_col = "quality"
    data = df.drop(predict_col, axis=1)
    label = df[predict_col]

    n_valid_rows = int(n_rows / 4)
    train_data = lgb.Dataset(data.iloc[n_valid_rows:], label=label.iloc[n_valid_rows:])
    validation_data = lgb.Dataset(
        data.iloc[:n_valid_rows], label=label.iloc[:n_valid_rows], reference=train_data
    )

    # set lightgbm parameters
    param = {"objective": "multiclass", "num_class": 11}

    # train model with 5 fold cross validation
    print("training model...")
    model = lgb.train(param, train_data, valid_sets=[validation_data])

    print("saving model...")
    model.save_model("model.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train wine quality lightgbm model.")
    parser.add_argument(
        "--start_date",
        help=(
            "Dummy date to convert into first row index to train for. "
            "Should have format idx-%m-%d, where idx is a row index and %m and %d "
            "are valid month and day numbers (that aren't used)."
        ),
        required=True,
    )
    parser.add_argument(
        "--end_date",
        help=(
            "Dummy date to convert into last row index to train for. "
            "Should have format idx-%m-%d, where idx is a row index and %m and %d "
            "are valid month and day numbers (that aren't used)."
        ),
        required=True,
    )
    parser.add_argument(
        "--database",
        help="Dummy placeholder for database to connect to, not used",
        required=False,
    )

    args = parser.parse_args()
    #  Interpret year of dates as row indexes to use for dummy example
    start_idx = datetime.strptime(args.start_date, "%Y-%m-%d").year
    end_idx = datetime.strptime(args.end_date, "%Y-%m-%d").year

    train(start_idx, end_idx)
