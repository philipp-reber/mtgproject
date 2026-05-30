import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

data_path = "./data/dataframe/card_price_dataframe.parquet"

df = pd.read_parquet(data_path)
df = df.copy() # safety copy against errors

# clean up target value
df["target_price_eur"] = pd.to_numeric(df["target_price_eur"], errors="coerce")
df = df.dropna(subset=["target_price_eur"])

# convert finish to boolean
df["is_foil"] = df["finish"].eq("foil")

# Drop unnecessary columns
drop_columns = ["card_id", "card_name", "oracle_text", "finish", "release_date", "set_code", "type_line", "set_name", "keywords", "artists", "mana_cost"]

df = df.drop(columns=[col for col in drop_columns if col in df.columns])

# convert legalities to booleans
legality_columns = ['standard_legal', 'future_legal',
       'historic_legal', 'timeless_legal', 'gladiator_legal', 'pioneer_legal',
       'explorer_legal', 'modern_legal', 'legacy_legal', 'pauper_legal',
       'vintage_legal', 'penny_legal', 'commander_legal', 'oathbreaker_legal',
       'standardbrawl_legal', 'brawl_legal', 'alchemy_legal',
       'paupercommander_legal', 'duel_legal', 'oldschool_legal',
       'premodern_legal', 'predh_legal']

for col in legality_columns:
    if col in df.columns:
        df[col] = df[col].eq("legal")

# convert list-like columns to strings
list_columns = [
    "colors",
    "games",
]

def list_to_string(value):
    if isinstance(value, (list, tuple, np.ndarray)):
        return "|".join(sorted(str(item) for item in value))
    if value is None or pd.isna(value):
        return ""
    return str(value)

for col in list_columns:
    if col in df.columns:
        df[col] = df[col].apply(list_to_string)

# Split Features and Target -> Convert to machine readable values

X = df.drop("target_price_eur", axis=1)
y = df["target_price_eur"]

numeric_features = ["edhrec_rank", "penny_rank"]

boolean_features = [
    "reserved",
    "booster",
    "digital",
    "reprint",
    "full_art",
    "textless",
    "is_foil",
] + [col for col in legality_columns if col in X.columns]

categorical_features = [
    "language",
    "set_type",
    "rarity",
    "border_color",
    "frame",
    "layout",
    "colors",
    "games",
    "power",
    "toughness",
    "loyalty",
]

# Keep only columns that actually exist in X (safety guard against unwanted columns)
numeric_features = [col for col in numeric_features if col in X.columns]
boolean_features = [col for col in boolean_features if col in X.columns]
categorical_features = [col for col in categorical_features if col in X.columns]


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

# Safety copying for Pandas Errors
X_train = X_train.copy()
X_test = X_test.copy()

# Numeric preprocessing

numeric_imputer = SimpleImputer(strategy="median")
scaler = StandardScaler()

X_train[numeric_features] = numeric_imputer.fit_transform(X_train[numeric_features])
X_test[numeric_features] = numeric_imputer.transform(X_test[numeric_features])

X_train[numeric_features] = scaler.fit_transform(X_train[numeric_features])
X_test[numeric_features] = scaler.transform(X_test[numeric_features])

# Boolean preprocessing

X_train[boolean_features] = X_train[boolean_features].fillna(False).astype(int)
X_test[boolean_features] = X_test[boolean_features].fillna(False).astype(int)

# Categorical preprocessing

categorical_imputer = SimpleImputer(strategy="constant", fill_value="missing")

X_train_cat = categorical_imputer.fit_transform(X_train[categorical_features])
X_test_cat = categorical_imputer.transform(X_test[categorical_features])

oneh = OneHotEncoder(handle_unknown="infrequent_if_exist", drop="first", sparse_output=False, min_frequency=50)

X_train_cat = oneh.fit_transform(X_train_cat)
X_test_cat = oneh.transform(X_test_cat)

cat_encoded_columns = oneh.get_feature_names_out(categorical_features)

print("Number of original categorical columns:", len(categorical_features))
print("Number of encoded categorical columns:", len(cat_encoded_columns))

X_train_cat = pd.DataFrame(X_train_cat, columns=cat_encoded_columns, index=X_train.index)

X_test_cat = pd.DataFrame(X_test_cat, columns=cat_encoded_columns, index=X_test.index) # type: ignore

# Combine categorical features

X_train_processed = X_train.drop(columns=categorical_features)
X_test_processed = X_test.drop(columns=categorical_features)

X_train_processed = pd.concat([X_train_processed, X_train_cat], axis=1)
X_test_processed = pd.concat([X_test_processed, X_test_cat], axis=1)

print("Training shape:", X_train_processed.shape)
print("Test shape:", X_test_processed.shape)

output_dir = Path("./data/dataframe")
output_dir.mkdir(parents=True, exist_ok=True)

y_train_path = output_dir / "card_price_dataframe_train_y.parquet"
y_test_path = output_dir / "card_price_dataframe_test_y.parquet"
X_train_path = output_dir / "card_price_dataframe_train_x.parquet"
X_test_path = output_dir / "card_price_dataframe_test_x.parquet"

X_train_processed.to_parquet(
    X_train_path,
    index=False,
    engine="pyarrow",
)

X_test_processed.to_parquet(
    X_test_path,
    index=False,
    engine="pyarrow",
)

y_train.to_frame(name="target_price_eur").to_parquet(
    y_train_path,
    index=False,
    engine="pyarrow",
)

y_test.to_frame(name="target_price_eur").to_parquet(
    y_test_path,
    index=False,
    engine="pyarrow",
)

print(f"Saved X_train to: {X_train_path}")
print(f"Saved X_test to: {X_test_path}")
print(f"Saved y_train to: {y_train_path}")
print(f"Saved y_test to: {y_test_path}")