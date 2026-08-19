from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Load dataset
df = pd.read_csv("dataset/HR_Data_MNC_Data Science Lovers.csv",nrows=50000)

# Remove unnecessary columns
df = df.drop(["Unnamed: 0", "Employee_ID","Full_Name" ,"Hire_Date"], axis=1,errors="ignore")

# Convert text columns to numbers
encoders = {}

for col in df.select_dtypes(include="object").columns:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col])
    encoders[col] = le

    os.makedirs("model",exist_ok=True)
joblib.dump(encoders,"model/encoders.pkl")

print(df.head())
print(df.info())
print("ML code started")

print("Creating X and y")
y = df["Performance_Rating"]
X = df.drop("Performance_Rating", axis=1)
print("X and y created")



# Target Column
y = df["Performance_Rating"]

# Features

X = df.drop("Performance_Rating", axis=1)

print(X.columns.tolist())

# Ye lines yahan add karo
print(df["Department"].unique())
print(df["Job_Title"].unique())
print(df["Location"].unique())
print(df["Status"].unique())
print(df["Work_Mode"].unique())

print(X.shape)
print(y.shape)



# Split Dataset
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print("split completed")

# Train Model
model = RandomForestClassifier(n_estimators=10,max_depth=10,random_state=42)
model.fit(X_train, y_train)
print("Model training completed")

# Prediction
y_pred = model.predict(X_test)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)
print("Model Accuracy:", accuracy)

# Save Model
joblib.dump(model, "model/model.pkl")
print("Model saved successfully!")

joblib.dump(encoders, "model/encoders.pkl")
print("Encoders saved successfully!")