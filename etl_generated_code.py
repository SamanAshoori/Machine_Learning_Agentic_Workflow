import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight

# Load data
df = pd.read_csv('data/fraudTrain.csv')

# --- Feature Engineering Steps ---

# Pre-requisite for calculations: Convert date columns to datetime
df['trans_date_trans_time'] = pd.to_datetime(df['trans_date_trans_time'])
df['dob'] = pd.to_datetime(df['dob'])

# 1. Distance Calculation (Haversine distance)
def haversine(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    # Haversine formula 
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

df['distance_km'] = haversine(df['lat'], df['long'], df['merch_lat'], df['merch_long'])

# 2. Age Extraction
df['age'] = (df['trans_date_trans_time'] - df['dob']).dt.days // 365

# 3. Temporal Features
df['hour_of_day'] = df['trans_date_trans_time'].dt.hour
df['day_of_week'] = df['trans_date_trans_time'].dt.dayofweek

# 4. Log Transformation
df['amt'] = np.log1p(df['amt'])
df['city_pop'] = np.log1p(df['city_pop'])

# --- Cleaning Plan ---

# 1. Engineered Features (Generated above)

# 2. Drop Columns
cols_to_drop = [
    'Unnamed: 0', 'cc_num', 'trans_num', 'first', 'last', 'street', 
    'city', 'zip', 'job', 'merchant', 'trans_date_trans_time', 
    'unix_time', 'dob', 'lat', 'long', 'merch_lat', 'merch_long'
]
df = df.drop(columns=cols_to_drop)

# 3. Handle Categorical Data
# Convert category, gender, and state into numerical format using One-Hot Encoding
categorical_cols = ['category', 'gender', 'state']
df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

# 4. Feature Scaling
scaler = StandardScaler()
numerical_cols = ['amt', 'city_pop', 'distance_km', 'age']
df[numerical_cols] = scaler.fit_transform(df[numerical_cols])

# 5. Final Verification
# Ensure no null values exist
df = df.dropna()

# --- Save Cleaned Data ---
df.to_csv('data/cleaned_fraud.csv', index=False)

# --- Handle Class Imbalance with Class Weighting ---
classes = np.array([0, 1])
weights = compute_class_weight(
    class_weight='balanced',
    classes=classes,
    y=df['is_fraud']
)

# Create weights dictionary
class_weights_dict = {int(classes[i]): float(weights[i]) for i in range(len(classes))}

# --- Save Class Weights ---
with open('data/class_weights.json', 'w') as f:
    json.dump(class_weights_dict, f)