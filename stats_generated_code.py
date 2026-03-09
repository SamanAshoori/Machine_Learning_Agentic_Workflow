import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import LabelEncoder
import json
import os

def main():
    # 1. Load data
    file_path = 'data/cleaned_fraud.csv'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    df = pd.read_csv(file_path)

    # Encode ALL string/object columns using LabelEncoder
    # No string columns should remain in the dataset
    le = LabelEncoder()
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype == 'string':
            df[col] = le.fit_transform(df[col].astype(str))
    
    # Save the fully encoded dataframe back to the csv as per instructions
    df.to_csv(file_path, index=False)

    target = 'is_fraud'
    X = df.drop(columns=[target])
    y = df[target]

    # 2. Compute correlation matrix and flag features > 0.85
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    high_corr_features = [column for column in upper.columns if any(upper[column] > 0.85)]

    # 3. Run chi-squared tests for categorical/binary features vs target
    # We treat columns with low unique counts or specific types as categorical
    p_values = {}
    for col in X.columns:
        # Create contingency table
        contingency_table = pd.crosstab(X[col], y)
        chi2, p, dof, ex = chi2_contingency(contingency_table)
        p_values[col] = p

    # 4. Compute VIF using sklearn only
    vif_data = {}
    for col in X.columns:
        X_others = X.drop(columns=[col])
        X_feature = X[col]
        # vif = 1 / (1 - R^2)
        r_squared = LinearRegression().fit(X_others, X_feature).score(X_others, X_feature)
        if r_squared >= 1.0:
            vif = float('inf')
        else:
            vif = 1 / (1 - r_squared)
        vif_data[col] = vif

    # 5. Rank features using mutual_info_classif
    mi_scores = mutual_info_classif(X, y, random_state=42)
    mi_ranking = pd.Series(mi_scores, index=X.columns).sort_values(ascending=False)

    # 6. Exclusion logic
    # - One from each highly correlated pair
    # - Features with p-value > 0.05
    # - Features with VIF > 5
    final_features = []
    excluded_reason = {}

    for col in X.columns:
        if col in high_corr_features:
            excluded_reason[col] = "High Correlation (>0.85)"
            continue
        if p_values[col] > 0.05:
            excluded_reason[col] = f"Statistically Insignificant (p={p_values[col]:.4f})"
            continue
        if vif_data[col] > 5:
            excluded_reason[col] = f"High Multicollinearity (VIF={vif_data[col]:.2f})"
            continue
        
        final_features.append(col)

    # Sort final features by their Mutual Info rank
    final_features = [f for f in mi_ranking.index if f in final_features]

    # 7. Save recommended feature list
    output_path = 'data/selected_features.json'
    os.makedirs('data', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_features, f, indent=4)

    # 8. Print Summary Report
    print("--- STATISTICAL VALIDATION REPORT ---")
    print(f"Initial features: {len(X.columns)}")
    print(f"Features excluded: {len(excluded_reason)}")
    for feat, reason in excluded_reason.items():
        print(f" - {feat}: {reason}")
    
    print("\n--- SELECTED FEATURES (Ranked by Mutual Information) ---")
    for i, feat in enumerate(final_features, 1):
        print(f"{i}. {feat} (MI: {mi_ranking[feat]:.4f}, VIF: {vif_data[feat]:.2f}, p: {p_values[feat]:.4f})")
    
    print(f"\nFinal feature list saved to: {output_path}")

if __name__ == "__main__":
    main()