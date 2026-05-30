from __future__ import annotations

import numpy as np
import pandas as pd

from dataclasses import dataclass
from pathlib import Path
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import paths


DATAFRAME_PATH = paths.data_dir / "dataframe" / "card_price_dataframe.parquet"
MODEL_BUNDLE_PATH = paths.model_dir / "card_price_model_bundle.joblib"

LEGALITY_COLUMNS = [
    "standard_legal",
    "future_legal",
    "historic_legal",
    "timeless_legal",
    "gladiator_legal",
    "pioneer_legal",
    "explorer_legal",
    "modern_legal",
    "legacy_legal",
    "pauper_legal",
    "vintage_legal",
    "penny_legal",
    "commander_legal",
    "oathbreaker_legal",
    "standardbrawl_legal",
    "brawl_legal",
    "alchemy_legal",
    "paupercommander_legal",
    "duel_legal",
    "oldschool_legal",
    "premodern_legal",
    "predh_legal",
]


DROP_COLUMNS = [
    "card_id",
    "card_name",
    "oracle_text",
    "finish",
    "release_date",
    "set_code",
    "type_line",
    "set_name",
    "keywords",
    "artists",
    "mana_cost",
]


LIST_COLUMNS = [
    "colors",
    "games",
]


NUMERIC_FEATURES = [
    "edhrec_rank",
    "penny_rank",
]


BASE_BOOLEAN_FEATURES = [
    "reserved",
    "booster",
    "digital",
    "reprint",
    "full_art",
    "textless",
    "is_foil",
]


CATEGORICAL_FEATURES = [
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


@dataclass(frozen=True)
class ModelMetrics:
    train_r2: float
    test_r2: float
    test_mae: float
    test_rmse: float


@dataclass(frozen=True)
class PreprocessingResult:
    X_train_processed: pd.DataFrame
    X_test_processed: pd.DataFrame
    encoded_categorical_columns: list[str]
    numeric_imputer: SimpleImputer
    scaler: StandardScaler
    categorical_imputer: SimpleImputer
    onehot_encoder: OneHotEncoder
    numeric_features: list[str]
    boolean_features: list[str]
    categorical_features: list[str]
    final_feature_columns: list[str]


@dataclass(frozen=True)
class ModelResult:
    model: RandomForestRegressor
    metrics: ModelMetrics
    train_rows: int
    test_rows: int
    feature_count: int
    encoded_categorical_count: int
    model_bundle_path: Path


def _list_to_string(value) -> str:
    if isinstance(value, (list, tuple, np.ndarray)):
        return "|".join(sorted(str(item) for item in value))

    if value is None or pd.isna(value):
        return ""

    return str(value)


def _existing_columns(columns: list[str], df: pd.DataFrame) -> list[str]:
    return [column for column in columns if column in df.columns]


def load_model_dataframe(data_path: Path = DATAFRAME_PATH) -> pd.DataFrame:
    if not data_path.exists():
        raise FileNotFoundError(
            f"Model dataframe not found at {data_path}. "
            "Run exportdf before building the ML model."
        )

    return pd.read_parquet(data_path).copy()


def prepare_model_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["target_price_eur"] = pd.to_numeric(
        df["target_price_eur"],
        errors="coerce",
    )

    df = df.dropna(subset=["target_price_eur"])

    df["is_foil"] = df["finish"].eq("foil")

    df = df.drop(
        columns=[column for column in DROP_COLUMNS if column in df.columns]
    )

    for column in LEGALITY_COLUMNS:
        if column in df.columns:
            df[column] = df[column].eq("legal")

    for column in LIST_COLUMNS:
        if column in df.columns:
            df[column] = df[column].apply(_list_to_string)

    return df


def split_model_dataframe(
    df: pd.DataFrame,
    test_size: float = 0.25,
    random_state: int = 42,
):
    X = df.drop("target_price_eur", axis=1)
    y = df["target_price_eur"]

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
    )


def preprocess_features(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    min_frequency: int = 50,
) -> PreprocessingResult:
    X_train = X_train.copy()
    X_test = X_test.copy()

    numeric_features = _existing_columns(NUMERIC_FEATURES, X_train)

    boolean_features = _existing_columns(
        BASE_BOOLEAN_FEATURES + LEGALITY_COLUMNS,
        X_train,
    )

    categorical_features = _existing_columns(CATEGORICAL_FEATURES, X_train)

    numeric_imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    X_train[numeric_features] = numeric_imputer.fit_transform(
        X_train[numeric_features]
    )
    X_test[numeric_features] = numeric_imputer.transform( # type: ignore
        X_test[numeric_features]
    )

    X_train[numeric_features] = scaler.fit_transform(
        X_train[numeric_features]
    )
    X_test[numeric_features] = scaler.transform(
        X_test[numeric_features]
    )

    X_train[boolean_features] = X_train[boolean_features].fillna(False).astype(int)
    X_test[boolean_features] = X_test[boolean_features].fillna(False).astype(int)

    categorical_imputer = SimpleImputer(
        strategy="constant",
        fill_value="missing",
    )

    X_train_cat = categorical_imputer.fit_transform(
        X_train[categorical_features]
    )
    X_test_cat = categorical_imputer.transform(
        X_test[categorical_features]
    )

    oneh = OneHotEncoder(
        handle_unknown="infrequent_if_exist",
        drop="first",
        sparse_output=False,
        min_frequency=min_frequency,
    )

    X_train_cat = oneh.fit_transform(X_train_cat)
    X_test_cat = oneh.transform(X_test_cat)

    encoded_categorical_columns = list(
        oneh.get_feature_names_out(categorical_features)
    )

    X_train_cat = pd.DataFrame(
        X_train_cat,
        columns=encoded_categorical_columns,
        index=X_train.index,
    )

    X_test_cat = pd.DataFrame(
        X_test_cat, # type: ignore
        columns=encoded_categorical_columns,
        index=X_test.index,
    ) # type: ignore

    X_train_processed = X_train.drop(columns=categorical_features)
    X_test_processed = X_test.drop(columns=categorical_features)

    X_train_processed = pd.concat(
        [X_train_processed, X_train_cat],
        axis=1,
    )

    X_test_processed = pd.concat(
        [X_test_processed, X_test_cat],
        axis=1,
    )

    print("Number of original categorical columns:", len(categorical_features))
    print("Number of encoded categorical columns:", len(encoded_categorical_columns))
    print("Training shape:", X_train_processed.shape)
    print("Test shape:", X_test_processed.shape)

    return PreprocessingResult(
        X_train_processed=X_train_processed,
        X_test_processed=X_test_processed,
        encoded_categorical_columns=encoded_categorical_columns,
        numeric_imputer=numeric_imputer,
        scaler=scaler,
        categorical_imputer=categorical_imputer,
        onehot_encoder=oneh,
        numeric_features=numeric_features,
        boolean_features=boolean_features,
        categorical_features=categorical_features,
        final_feature_columns=list(X_train_processed.columns),
    )


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> RandomForestRegressor:
    model = RandomForestRegressor(
        random_state=42,
        n_estimators=100,
        max_depth=25,
        min_samples_leaf=5,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    return model


def evaluate_model(
    model: RandomForestRegressor,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> ModelMetrics:
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    return ModelMetrics(
        train_r2=r2_score(y_train, train_pred),
        test_r2=r2_score(y_test, test_pred),
        test_mae=mean_absolute_error(y_test, test_pred),
        test_rmse=mean_squared_error(y_test, test_pred) ** 0.5,
    )


def print_metrics(metrics: ModelMetrics) -> None:
    print("Random Forest")
    print("Train R2:", metrics.train_r2)
    print("Test R2:", metrics.test_r2)
    print("Test MAE:", metrics.test_mae)
    print("Test RMSE:", metrics.test_rmse)

def save_model_bundle(
    model: RandomForestRegressor,
    preprocessing_result: PreprocessingResult,
    metrics: ModelMetrics,
    model_bundle_path: Path = MODEL_BUNDLE_PATH,
) -> Path:
    model_bundle_path.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "model": model,
        "numeric_imputer": preprocessing_result.numeric_imputer,
        "scaler": preprocessing_result.scaler,
        "categorical_imputer": preprocessing_result.categorical_imputer,
        "onehot_encoder": preprocessing_result.onehot_encoder,
        "numeric_features": preprocessing_result.numeric_features,
        "boolean_features": preprocessing_result.boolean_features,
        "categorical_features": preprocessing_result.categorical_features,
        "encoded_categorical_columns": preprocessing_result.encoded_categorical_columns,
        "final_feature_columns": preprocessing_result.final_feature_columns,
        "metrics": {
            "train_r2": metrics.train_r2,
            "test_r2": metrics.test_r2,
            "test_mae": metrics.test_mae,
            "test_rmse": metrics.test_rmse,
        },
    }

    joblib.dump(bundle, model_bundle_path)

    print(f"Saved model bundle to: {model_bundle_path}")

    return model_bundle_path

def build_model() -> ModelResult:
    df = load_model_dataframe()
    df = prepare_model_dataframe(df)

    X_train, X_test, y_train, y_test = split_model_dataframe(df)

    preprocessing_result = preprocess_features(
        X_train,
        X_test,
        min_frequency=50,
    )

    model = train_random_forest(
        preprocessing_result.X_train_processed,
        y_train,
    )

    metrics = evaluate_model(
        model,
        preprocessing_result.X_train_processed,
        preprocessing_result.X_test_processed,
        y_train,
        y_test,
    )

    print_metrics(metrics)

    model_bundle_path = save_model_bundle(
        model=model,
        preprocessing_result=preprocessing_result,
        metrics=metrics,
    )

    return ModelResult(
        model=model,
        metrics=metrics,
        train_rows=preprocessing_result.X_train_processed.shape[0],
        test_rows=preprocessing_result.X_test_processed.shape[0],
        feature_count=preprocessing_result.X_train_processed.shape[1],
        encoded_categorical_count=len(
            preprocessing_result.encoded_categorical_columns
        ),
        model_bundle_path=model_bundle_path,
    )

def load_model_bundle(
    model_bundle_path: Path = MODEL_BUNDLE_PATH,
) -> dict:
    if not model_bundle_path.exists():
        raise FileNotFoundError(f"Model bundle not found: {model_bundle_path}")

    return joblib.load(model_bundle_path)

def _prepare_single_card_dataframe(card_features: dict) -> pd.DataFrame:
    """
    Convert one user-provided card dictionary into the same raw-ish structure
    expected by the trained preprocessing bundle.

    This does not fit anything. It only prepares one row.
    """
    df = pd.DataFrame([card_features]).copy()

    if "finish" in df.columns:
        df["is_foil"] = df["finish"].eq("foil")
    elif "is_foil" not in df.columns:
        df["is_foil"] = False

    for column in LEGALITY_COLUMNS:
        if column in df.columns:
            if df[column].dtype == bool:
                df[column] = df[column]
            else:
                df[column] = df[column].eq("legal")

    for column in LIST_COLUMNS:
        if column in df.columns:
            df[column] = df[column].apply(_list_to_string)

    df = df.drop(
        columns=[column for column in DROP_COLUMNS if column in df.columns],
        errors="ignore",
    )

    return df

def predict_card_price(card_features: dict) -> float:
    """
    Predict a EUR price for one card using the saved model bundle.

    The input should be a dictionary with user-provided card features.
    Missing features are allowed; the saved imputers/defaults handle them.
    """
    bundle = load_model_bundle()

    model = bundle["model"]

    numeric_features = bundle["numeric_features"]
    boolean_features = bundle["boolean_features"]
    categorical_features = bundle["categorical_features"]
    final_feature_columns = bundle["final_feature_columns"]

    numeric_imputer = bundle["numeric_imputer"]
    scaler = bundle["scaler"]
    categorical_imputer = bundle["categorical_imputer"]
    onehot_encoder = bundle["onehot_encoder"]

    df = _prepare_single_card_dataframe(card_features)

    required_raw_columns = (
        numeric_features
        + boolean_features
        + categorical_features
    )

    for column in required_raw_columns:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[required_raw_columns]

    df[numeric_features] = numeric_imputer.transform(df[numeric_features])
    df[numeric_features] = scaler.transform(df[numeric_features])

    df[boolean_features] = df[boolean_features].fillna(False).astype(int)

    cat_values = categorical_imputer.transform(df[categorical_features])
    cat_encoded = onehot_encoder.transform(cat_values)

    cat_encoded_columns = onehot_encoder.get_feature_names_out(categorical_features)

    cat_df = pd.DataFrame(
        cat_encoded,
        columns=cat_encoded_columns,
        index=df.index,
    )

    non_cat_df = df.drop(columns=categorical_features)

    processed = pd.concat(
        [non_cat_df, cat_df],
        axis=1,
    )

    processed = processed.reindex(
        columns=final_feature_columns,
        fill_value=0,
    )

    prediction = model.predict(processed)[0]

    return float(prediction)