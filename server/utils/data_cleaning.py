import pandas as pd

def clean(df):
    df.dropna(inplace=True)  # Drop missing values
    df = df.apply(lambda x: x.strip() if isinstance(x, str) else x)  # Clean up strings
    return df