from __future__ import annotations

import pathlib

import pandas as pd
from sklearn.model_selection import train_test_split


def main() -> None:
 
    data_dir = pathlib.Path(__file__).parent 
    df = pd.read_csv(data_dir / "hidden" /"master.csv")

    train, test = train_test_split(df, test_size=0.3, random_state=42)

    train.to_csv(data_dir / "data" /"train.csv", index=False)
    test.to_csv(data_dir / "hidden" / "test.csv", index=False)

    print(f"Split complete: {len(train)} train rows, {len(test)} test rows")
    print("Train and test datasets created.")

if __name__ == "__main__":
    main()