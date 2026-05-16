from sklearn.ensemble import RandomForestClassifier
model=RandomForestClassifier()
import pandas as pd
data=pd.read_csv("C:/Users/Sahil/EDI_2_digital_twinning/datasets/vitamin_deficiency_disease_dataset_20260123.csv")

from sklearn.preprocessing import LabelEncoder
X = data.drop(columns=["disease_diagnosis"])
encoders = {}
categorical_cols = X.select_dtypes(include=["object"]).columns
for col in categorical_cols:
    encoders[col] = LabelEncoder()
    X[col] = encoders[col].fit_transform(X[col])

le_y = LabelEncoder()
Y = le_y.fit_transform(data['disease_diagnosis'])
model.fit(X,Y)
sample = X.iloc[[1]].copy()

prediction=model.predict(sample)
print(le_y.inverse_transform(prediction))



print(data["alcohol_consumption"].unique())
