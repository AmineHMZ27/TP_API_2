import json
import pandas as pd
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

def train_model_from_json(json_path, model_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    df = df[df['customer_rating'].notnull()]
    df = df.select_dtypes(include=["number"])

    if 'customer_rating' not in df.columns:
        raise ValueError("Missing 'customer_rating' in data")

    X = df.drop(columns=['customer_rating'])
    y = df['customer_rating']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = DecisionTreeRegressor()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)

    joblib.dump(model, model_path)

    return {
        "features": list(X.columns),
        "num_rows": len(df),
        "mse": mse
    }
