import pandas as pd
import pytest

from smishguard import config
from smishguard.data.anonymize import mask_pii
from smishguard.data.loader import load_curated, load_turkishsms, validate_schema
from smishguard.data.normalize import defang


@pytest.fixture(scope="module")
def curated() -> pd.DataFrame:
    return load_curated()


def test_curated_csv_follows_schema(curated: pd.DataFrame) -> None:
    assert tuple(curated.columns) == config.SCHEMA_COLUMNS
    assert len(curated) >= 50


def test_curated_has_both_labels_and_all_scam_categories(curated: pd.DataFrame) -> None:
    assert set(curated["label"]) == set(config.LABELS)
    malicious_categories = set(curated.loc[curated["label"] == 1, "category"])
    expected = set(config.CATEGORIES) - {"generic_spam"}
    assert expected <= malicious_categories


def test_curated_links_are_defanged(curated: pd.DataFrame) -> None:
    for text in curated["text"]:
        assert "http://" not in text.lower() and "https://" not in text.lower(), text
        assert defang(text) == text, text


def test_curated_contains_no_unmasked_pii(curated: pd.DataFrame) -> None:
    for text in curated["text"]:
        assert mask_pii(text) == text, text


def test_validate_schema_rejects_unknown_values() -> None:
    df = pd.DataFrame({"text": ["x"], "label": [1], "category": ["nope"], "source": ["synthetic"]})
    with pytest.raises(ValueError, match="category"):
        validate_schema(df)


def test_validate_schema_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="Missing columns"):
        validate_schema(pd.DataFrame({"text": ["x"]}))


def test_load_turkishsms_maps_labels(tmp_path) -> None:
    names = list(config.TURKISHSMS_FILES)
    pd.DataFrame({"text": ["a", "b"], "label": ["spam", "legitimate"]}).to_parquet(
        tmp_path / names[0]
    )
    pd.DataFrame({"text": ["c"], "label": ["legitimate"]}).to_parquet(tmp_path / names[1])

    df = load_turkishsms(tmp_path)
    assert df["label"].tolist() == [1, 0, 0]
    assert df["category"].tolist() == ["generic_spam", "other", "other"]
    assert (df["source"] == config.SOURCE_TURKISHSMS).all()


def test_load_turkishsms_missing_files_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="download_data.py"):
        load_turkishsms(tmp_path)
