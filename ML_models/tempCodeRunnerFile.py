from sklearn.ensemble import RandomForestClassifier
model=RandomForestClassifier()
import pandas as pd
data=pd.read_csv("C:/Users/Sahil/EDI_2_digital_twinning/datasets/vitamin_deficiency_disease_dataset_20260123.csv")

from sklearn.preprocessing import LabelEncoder
X = data[[
    'age',
    'gender',
    'bmi',
    'smoking_status',
    'alcohol_consumption',
    'exercise_level',
    'diet_type',
    'sun_exposure',
    'income_level',
    'latitude_region'
    ,'symptoms_list'
]].copy()
encoders = {}
for col in ['gender', 'smoking_status', 'alcohol_consumption', 'exercise_level', 'diet_type', 'sun_exposure', 'income_level', 'latitude_region', 'symptoms_list']:
    encoders[col] = LabelEncoder()
    X[col] = encoders[col].fit_transform(X[col])

le_y = LabelEncoder()
Y = le_y.fit_transform(data['disease_diagnosis'])
model.fit(X,Y)
sample = X.iloc[[1]].copy()
sample['symptoms_list'] = encoders['symptoms_list'].transform(['None'])[0]
prediction=model.predict(sample)
print(le_y.inverse_transform(prediction))
