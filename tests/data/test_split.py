import pandas as pd
import pytest

from smishguard import config
from smishguard.data.split import dedup_key, deduplicate, split_dataset


def word(i: int) -> str:
    """Unique letters-only token (dedup_key treats all digits as equal)."""
    return chr(97 + i // 26) + chr(97 + i % 26)


def make_dataset(n_real_per_label: int = 40, n_synthetic: int = 10) -> pd.DataFrame:
    rows = []
    for label in config.LABELS:
        for i in range(n_real_per_label):
            rows.append(
                {
                    "text": f"real message {word(i)} class {'spam' if label else 'ham'}",
                    "label": label,
                    "category": "other",
                    "source": config.SOURCE_TURKISHSMS,
                }
            )
    for i in range(n_synthetic):
        rows.append(
            {
                "text": f"synthetic scam {word(i)}",
                "label": config.LABEL_MALICIOUS,
                "category": "cargo",
                "source": config.SOURCE_SYNTHETIC,
            }
        )
    return pd.DataFrame(rows)


def test_dedup_key_ignores_case_numbers_punctuation_and_turkish_letters() -> None:
    assert dedup_key("ÖDEME: 100 TL!") == dedup_key("odeme 250 tl")


def test_deduplicate_drops_copies_and_prefers_real_source() -> None:
    df = pd.DataFrame(
        {
            "text": ["Kargo bekliyor 12", "kargo bekliyor 99", "farkli mesaj"],
            "label": [1, 1, 0],
            "category": ["cargo", "cargo", "other"],
            "source": [config.SOURCE_SYNTHETIC, config.SOURCE_TURKISHSMS, config.SOURCE_TURKISHSMS],
        }
    )
    out = deduplicate(df)
    assert len(out) == 2
    assert out.loc[out["text"].str.startswith("kargo"), "source"].item() == config.SOURCE_TURKISHSMS


def test_deduplicate_drops_groups_with_conflicting_labels() -> None:
    df = pd.DataFrame(
        {
            "text": ["ayni mesaj", "Ayni mesaj", "baska"],
            "label": [0, 1, 0],
            "category": ["other"] * 3,
            "source": [config.SOURCE_TURKISHSMS] * 3,
        }
    )
    assert deduplicate(df)["text"].tolist() == ["baska"]


@pytest.fixture
def splits() -> dict[str, pd.DataFrame]:
    return split_dataset(deduplicate(make_dataset()))


def test_splits_do_not_overlap(splits: dict[str, pd.DataFrame]) -> None:
    keys = {name: set(part["text"].map(dedup_key)) for name, part in splits.items()}
    assert keys["train"].isdisjoint(keys["val"])
    assert keys["train"].isdisjoint(keys["test"])
    assert keys["val"].isdisjoint(keys["test"])


def test_synthetic_rows_only_in_train(splits: dict[str, pd.DataFrame]) -> None:
    assert (splits["train"]["source"] == config.SOURCE_SYNTHETIC).sum() == 10
    for name in ("val", "test"):
        assert (splits[name]["source"] != config.SOURCE_SYNTHETIC).all()


def test_split_sizes_and_stratification(splits: dict[str, pd.DataFrame]) -> None:
    real_total = 80
    assert len(splits["test"]) == pytest.approx(real_total * config.TEST_RATIO, abs=1)
    assert len(splits["val"]) == pytest.approx(real_total * config.VAL_RATIO, abs=1)
    for name in ("val", "test"):
        assert splits[name]["label"].mean() == pytest.approx(0.5, abs=0.1)


def test_split_is_deterministic() -> None:
    data = deduplicate(make_dataset())
    first, second = split_dataset(data), split_dataset(data)
    for name in config.SPLIT_NAMES:
        pd.testing.assert_frame_equal(first[name], second[name])
