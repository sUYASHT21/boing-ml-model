import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import warnings

warnings.filterwarnings('ignore')

INPUT_FILE = '/Users/suyashtatiya/DataCleaning/V2_model/v2_ml_ready_features.csv'
MODEL_OUTPUT = '/Users/suyashtatiya/DataCleaning/V2_model/v2_rf_model.pkl'

def main():
    print("\n" + "="*50)
    print("STARTING V2 AI MODEL TRAINING")
    print("="*50)

    print("Loading V2 Data...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: Could not find data at {INPUT_FILE}")
        return

    X = df[['Vendor Name - ID', 'Program (MG4)', 'Requested Lead Time', 'Order_Month', 'Vendor_Historical_Avg_Days']]
    y = df['Delivered in Full Days']

    print("Building Machine Learning Pipeline...")
    
    categorical_features = ['Vendor Name - ID', 'Program (MG4)']
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', categorical_transformer, categorical_features)
        ], remainder='passthrough')

    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1))
    ])

    print("Splitting data into Training and Testing sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest Regressor...")
    model.fit(X_train, y_train)

    print("Evaluating Model Accuracy...")
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("-" * 30)
    print("MODEL METRICS:")
    print(f"Mean Absolute Error: {mae:.2f} Days")
    print(f"R-squared Score: {r2:.2f}")
    print("-" * 30)

    print("Saving trained AI model...")
    joblib.dump(model, MODEL_OUTPUT)
    print(f"SUCCESS! Model saved to {MODEL_OUTPUT}")

if __name__ == "__main__":
    main()