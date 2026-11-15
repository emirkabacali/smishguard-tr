"""Streamlit demo for SmishGuard-TR.

Run:
    pip install -e ".[demo]"
    streamlit run app/streamlit_app.py

The UI reuses the same Analyzer class as the REST API, so both always give identical results.
"""

from __future__ import annotations

import streamlit as st

from smishguard import config
from smishguard.analyzer import AnalysisResult, Analyzer

# Defanged examples: links are never clickable and are only analyzed as text.
EXAMPLES = {
    "Fake cargo notice (smishing)": (
        "PTT: Kargonuz adres eksikligi nedeniyle bekliyor. 24 saat icinde guncelleyin: "
        "hxxps://ptt-kargo-takip[.]xyz"
    ),
    "Fake bank alert (smishing)": (
        "Ziraat Bankasi: Hesabiniz guvenlik nedeniyle askiya alinmistir. Sifrenizi girerek "
        "aktif edin: hxxps://ziraat-guvenlik-dogrulama[.]xyz"
    ),
    "Toll fine with URL shortener (smishing)": (
        "HGS: Odenmemis gecis ihlaliniz bulunmaktadir. Ceza almamak icin hemen odeyin: "
        "hxxps://bit[.]ly/hgsOdeme"
    ),
    "Prize claim (smishing)": (
        "TEBRIKLER! Cekiliste iPhone kazandiniz. Hediyenizi almak icin kargo ucreti 29 TL: "
        "hxxps://hediye-teslim[.]shop"
    ),
    "Official cargo notice (legitimate)": (
        "Yurtici Kargo: 7G2K91 nolu gonderiniz bugun dagitima cikmistir. "
        "Takip: hxxps://www[.]yurticikargo[.]com"
    ),
    "One-time password (legitimate)": (
        "Dogrulama kodunuz 482913. Bu kodu kimseyle paylasmayin. "
        "Banka calisanlari bu kodu asla istemez."
    ),
    "Personal message (legitimate)": "Aksam yemege geliyor musun? Annem seni de soruyor.",
}

LEVEL_STYLE = {
    "low": ("#1a7f37", "LOW RISK"),
    "medium": ("#bf8700", "MEDIUM RISK"),
    "high": ("#cf222e", "HIGH RISK"),
}


@st.cache_resource(show_spinner="Loading model...")
def load_analyzer() -> Analyzer:
    """Load the model once per server process (shared by all sessions)."""
    return Analyzer.from_files()


def render_result(result: AnalysisResult) -> None:
    """Show the risk level, the score breakdown and the reasons."""
    color, label = LEVEL_STYLE[result.risk_level]
    st.markdown(
        f"<div style='background:{color};color:white;padding:0.8rem 1rem;border-radius:0.5rem;"
        f"font-size:1.3rem;font-weight:600'>{label} &nbsp;·&nbsp; score {result.risk_score:.2f}"
        "</div>",
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, result.risk_score))

    col_ml, col_rules, col_alpha = st.columns(3)
    col_ml.metric("Text model probability", f"{result.ml_probability:.2f}")
    col_rules.metric("Rule score", f"{result.rule_score:.2f}")
    col_alpha.metric("Model weight (alpha)", f"{load_analyzer().params.alpha:.1f}")

    st.subheader("Why?")
    if not result.reasons:
        st.write("No rule fired. The score comes from the text model only.")
    for reason in result.reasons:
        st.markdown(f"- **{reason.code}** (weight {reason.weight:.2f}): {reason.message}")


def main() -> None:
    """Page layout."""
    st.set_page_config(page_title="SmishGuard-TR", page_icon="🛡️", layout="centered")
    st.title("SmishGuard-TR")
    st.caption("Explainable smishing (SMS phishing) risk analysis for Turkish messages.")

    try:
        analyzer = load_analyzer()
    except FileNotFoundError:
        st.error(
            "No trained model found. Run `python scripts/train.py` "
            "(or `python scripts/train_demo_model.py --output models` for a demo model)."
        )
        st.stop()

    example = st.selectbox("Try an example", list(EXAMPLES))
    text = st.text_area(
        "SMS text",
        value=EXAMPLES[example],
        height=120,
        max_chars=config.API_MAX_TEXT_LENGTH,
        help="Paste a message. Links are analyzed as text and never opened.",
    )
    if st.button("Analyze", type="primary") or text:
        if text.strip():
            render_result(analyzer.analyze(text))
        else:
            st.warning("Please enter a message.")

    st.divider()
    st.caption(
        f"Model version {analyzer.model_version}. Research / portfolio project, "
        "**not a security product**. Do not rely on it to decide whether a message is safe."
    )


main()
