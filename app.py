import json
import os
from datetime import datetime

import joblib
import pandas as pd
import streamlit as st
from PIL import Image

import ui
from i18n import LANGUAGES, TranslationError, detect_script, translate_to_english
from ocr import OCRUnavailable, extract_text
from translations import TRANSLATIONS
from utils import clean_text

st.set_page_config(page_title="Fake News Detector", page_icon="\U0001F4F0", layout="wide")

# ---------- Interface strings (English originals; other languages in translations.py) ----------
UI_EN = {
    "title": "Fake News Detector",
    "subtitle": "Paste a news article in English or an Indian language. A machine-learning model "
                "estimates whether it looks Real or Fake and shows which words influenced the decision.",
    "tab_check": "Check an article",
    "tab_batch": "Batch check (CSV)",
    "tab_history": "History",
    "tab_perf": "Model performance",
    "tab_about": "About",
    "try_example": "Try an example:",
    "sample1": "Sample 1",
    "sample2": "Sample 2",
    "sample3": "Sample 3 (Hindi)",
    "upload_txt": "...or upload a .txt file",
    "text_label": "News text (headline + article)",
    "input_lang": "Language of the article",
    "auto": "Auto-detect",
    "check_btn": "Check article",
    "too_short": "Please enter at least 10 words for a reliable result.",
    "looks_real": "Looks REAL",
    "looks_fake": "Looks FAKE",
    "uncertain": "Uncertain",
    "confidence": "Model confidence",
    "leaning": "leaning",
    "prob_real": "Probability of being real",
    "words": "Words",
    "excl": "Exclamations",
    "caps": "CAPS %",
    "why": "Why this result? Words with the strongest influence (from the English text):",
    "toward_real": "Pushing toward REAL",
    "toward_fake": "Pushing toward FAKE",
    "none": "None found",
    "info_wait": "Paste or upload an article, then click Check article.",
    "disclaimer": "This model learns writing patterns from a labelled dataset. It does not verify facts, "
                  "so treat the result as a hint, not proof.",
    "translated_note": "Translated to English before checking",
    "translated_exp": "Text sent to the model (English translation)",
    "translation_failed": "Translation failed. Please check your internet connection and try again.",
    "batch_intro": "Upload a CSV file with a column containing article text and check every row at once. "
                   "Non-English rows are translated automatically.",
    "csv_file": "CSV file",
    "which_col": "Which column holds the news text?",
    "run_batch": "Run batch check",
    "batch_progress": "Checking articles...",
    "checked": "Articles checked",
    "pred_fake": "Predicted fake",
    "pred_real": "Predicted real",
    "dl_results": "Download results (CSV)",
    "hist_empty": "Articles you check will be listed here for this session.",
    "dl_history": "Download history (CSV)",
    "clear_history": "Clear history",
    "perf_missing": "Run python train.py to generate model metrics.",
    "perf_trained": "Training articles",
    "perf_tested": "Test articles",
    "best_model": "Best model by F1",
    "acc_compare": "Accuracy comparison",
    "cm_title": "Confusion matrix (model used by this app)",
    "about_how": "How it works",
    "about_1": "1. Non-English text is translated to English (the model is trained on English news).",
    "about_2": "2. The text is cleaned and TF-IDF turns it into numbers that reflect how important each word is.",
    "about_3": "3. A Logistic Regression classifier turns those numbers into a Real/Fake probability.",
    "about_4": "4. The explanation chart multiplies each word's TF-IDF value by the model's weight for that word.",
    "about_models": "Models compared in training: Logistic Regression, Naive Bayes, Linear SVM.",
    "about_lim": "Limitations",
    "lim_1": "Trained on one English dataset, so it may be less accurate on news from other sources or topics.",
    "lim_2": "It detects writing style, not factual truth.",
    "lim_3": "Non-English results depend on translation quality, and translation needs an internet connection.",
    "lim_4": "Short texts give less reliable predictions.",
    "sidebar_note": "Articles can be written in English or any language listed here.",
    "upload_img": "...or upload an image of the article (screenshot or photo)",
    "extract_btn": "Extract text from image",
    "ocr_working": "Reading text from the image...",
    "ocr_done": "Text extracted. You can edit it below before checking.",
    "ocr_empty": "No text could be read from this image. Try a clearer or larger image, or choose the article's language.",
    "ocr_missing": "Reading text from images needs the free Tesseract OCR program. See the README for setup.",
    "image_caption": "Uploaded image",
    "hero_headline": "Is this news real? Find out in seconds.",
    "chip_langs": "13 languages",
    "chip_ocr": "Reads text from images",
    "chip_why": "Explains every verdict",
    "input_heading": "Add the article",
    "result_heading": "Verdict",
    "mode_text": "Paste text",
    "mode_image": "Upload image",
    "mode_file": "Upload .txt",
}

SAMPLES = {
    "sample1": (
        "Government announces new infrastructure plan. The finance ministry said on Tuesday "
        "that it will invest in roads, railways and digital networks over the next five years, "
        "according to a statement released after a cabinet meeting. Officials said the plan "
        "would be funded through a mix of public borrowing and private partnerships."
    ),
    "sample2": (
        "SHOCKING!!! You will not believe what they are hiding from you. Anonymous insiders "
        "reveal the truth that the mainstream media refuses to show. Share this before it gets "
        "deleted, because they do not want you to know what is really going on behind closed doors."
    ),
    "sample3": (
        "सरकार ने मंगलवार को घोषणा की कि अगले पांच वर्षों में सड़कों, रेलवे और डिजिटल नेटवर्क में निवेश "
        "किया जाएगा। वित्त मंत्रालय के अनुसार यह योजना सार्वजनिक उधार और निजी भागीदारी के माध्यम से "
        "पूरी की जाएगी। अधिकारियों ने कहा कि कैबिनेट की बैठक के बाद इसकी जानकारी दी गई।"
    ),
}



def get_ui(lang_code: str) -> dict:
    """Interface text for a language. Built in (see translations.py), so no internet is needed.
    Any key missing from a language falls back to English."""
    return {**UI_EN, **TRANSLATIONS.get(lang_code, {})}


@st.cache_data(show_spinner=False)
def cached_translate(text: str, source: str) -> str:
    return translate_to_english(text, source)


def ensure_theme() -> bool:
    """Create .streamlit/config.toml (the colour theme) if missing. Returns True if just created,
    because Streamlit only reads the theme when it starts."""
    path = os.path.join(".streamlit", "config.toml")
    if os.path.exists(path):
        return False
    try:
        os.makedirs(".streamlit", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(ui.THEME_TOML)
        return True
    except OSError:
        return False


theme_created = ensure_theme()
st.markdown(f"<style>{ui.CSS}\ntextarea{{unicode-bidi:plaintext;}}</style>", unsafe_allow_html=True)

# ---------- Top bar: brand + interface language ----------
bar_left, bar_right = st.columns([3, 1], vertical_alignment="center")
with bar_right:
    ui_choice = st.selectbox("Interface language / भाषा", list(LANGUAGES), key="ui_lang")
T = get_ui(LANGUAGES[ui_choice])
with bar_left:
    st.markdown(ui.brand_html(T["title"]), unsafe_allow_html=True)

if theme_created:
    st.info("Colour theme installed. Stop the app (Ctrl+C) and run it again to see the full design.")

st.markdown(
    ui.hero_html(T["hero_headline"], T["subtitle"], [T["chip_langs"], T["chip_ocr"], T["chip_why"]]),
    unsafe_allow_html=True,
)


# ---------- Model ----------
@st.cache_resource
def load_model():
    if not os.path.exists("model.joblib"):
        return None
    return joblib.load("model.joblib")


model = load_model()
if model is None:
    st.error("model.joblib not found. Run `python train.py` first, then restart the app.")
    st.stop()

vectorizer = model.steps[0][1]
classifier = model.steps[-1][1]
feature_names = vectorizer.get_feature_names_out()


def prepare(text: str, lang_choice: str):
    """Return (english_text, script_name, was_translated). Raises TranslationError."""
    script = detect_script(text)
    if lang_choice == "auto":
        needs, source = script != "Latin", "auto"
    else:
        code = LANGUAGES[lang_choice]
        needs, source = code != "en", code
    if not needs:
        return text, script, False
    return cached_translate(text, source), script, True


def predict(english_text: str):
    """Return (label, confidence %, probability of being real)."""
    proba = model.predict_proba([clean_text(english_text)])[0]
    p_real = float(proba[1])
    label = "Real" if p_real >= 0.5 else "Fake"
    return label, max(p_real, 1 - p_real) * 100, p_real


def explain(english_text: str, top_n: int = 8):
    """Words that pushed the prediction toward Real / Fake (TF-IDF value x model weight)."""
    row = vectorizer.transform([clean_text(english_text)]).multiply(classifier.coef_[0]).tocoo()
    df = pd.DataFrame({"word": feature_names[row.col], "impact": row.data})
    real_words = df.sort_values("impact", ascending=False).head(top_n)
    real_words = real_words[real_words.impact > 0]
    fake_words = df.sort_values("impact").head(top_n)
    fake_words = fake_words[fake_words.impact < 0]
    return real_words, fake_words


def text_stats(text: str, script: str):
    letters = [c for c in text if c.isalpha()]
    caps = sum(c.isupper() for c in letters) / max(len(letters), 1) * 100
    return {
        "words": len(text.split()),
        "excl": text.count("!"),
        "caps": f"{caps:.1f}" if script == "Latin" else "n/a",
    }


for key, default in (("history", []), ("news_text", ""), ("result", None), ("input_mode", "text")):
    if key not in st.session_state:
        st.session_state[key] = default


def load_sample(key):
    st.session_state.news_text = SAMPLES[key]


tab_check, tab_batch, tab_history, tab_perf, tab_about = st.tabs(
    [f"\U0001F50D {T['tab_check']}", f"\U0001F4C2 {T['tab_batch']}", f"\U0001F558 {T['tab_history']}",
     f"\U0001F4CA {T['tab_perf']}", f"\u2139\ufe0f {T['tab_about']}"]
)

# ---------- Tab 1: single article ----------
with tab_check:
    left, right = st.columns([1, 1], gap="large")

    # ----- Step 1: add the article -----
    with left:
        with st.container(key="input_panel"):
            st.markdown(ui.step_html(1, T["input_heading"]), unsafe_allow_html=True)

            st.markdown(ui.label_html(T["try_example"]), unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.button(T["sample1"], key="sample1", on_click=load_sample, args=("sample1",), use_container_width=True)
            c2.button(T["sample2"], key="sample2", on_click=load_sample, args=("sample2",), use_container_width=True)
            c3.button(T["sample3"], key="sample3", on_click=load_sample, args=("sample3",), use_container_width=True)

            lang_choice = st.selectbox(
                T["input_lang"], ["auto"] + list(LANGUAGES),
                format_func=lambda x: T["auto"] if x == "auto" else x,
            )

            mode = st.segmented_control(
                T["input_heading"], ["text", "image", "file"], key="input_mode",
                format_func=lambda m: {"text": T["mode_text"], "image": T["mode_image"], "file": T["mode_file"]}[m],
                label_visibility="collapsed", width="stretch",
            ) or "text"

            if mode == "file":
                uploaded = st.file_uploader(T["upload_txt"], type=["txt"])
                if uploaded is not None:
                    # Load each new file once, so later edits and the sample buttons are not overwritten
                    file_key = f"{uploaded.name}-{uploaded.size}"
                    if st.session_state.get("txt_loaded") != file_key:
                        st.session_state.news_text = uploaded.read().decode("utf-8", errors="ignore")
                        st.session_state.txt_loaded = file_key

            if mode == "image":
                image_file = st.file_uploader(T["upload_img"], type=["png", "jpg", "jpeg", "webp"])
                if image_file is not None:
                    image = Image.open(image_file)
                    st.image(image, caption=T["image_caption"], width=320)
                    if st.button(T["extract_btn"], key="extract_btn"):
                        ocr_code = "auto" if lang_choice == "auto" else LANGUAGES[lang_choice]
                        try:
                            with st.spinner(T["ocr_working"]):
                                extracted = extract_text(image, ocr_code)
                        except OCRUnavailable as exc:
                            st.error(T["ocr_missing"])
                            st.caption(f"Details: {str(exc)[:300]}")
                        except Exception as exc:  # unreadable or damaged image
                            st.error(T["ocr_empty"])
                            st.caption(f"Details: {str(exc)[:200]}")
                        else:
                            if extracted:
                                st.session_state.news_text = extracted
                                st.success(T["ocr_done"])
                            else:
                                st.warning(T["ocr_empty"])

            text = st.text_area(T["text_label"], key="news_text", height=170)
            run = st.button(T["check_btn"], key="check_btn", type="primary", use_container_width=True)

    if run:
        if len(text.split()) < 10:
            st.session_state.result = None
            with left:
                st.warning(T["too_short"])
        else:
            try:
                with st.spinner("..."):
                    english, script, translated = prepare(text, lang_choice)
            except TranslationError as exc:
                english = None
                with right:
                    st.error(T["translation_failed"])
                    st.caption(f"Details: {str(exc)[:300]}")
            if english is not None:
                label, conf, p_real = predict(english)
                real_words, fake_words = explain(english)
                st.session_state.result = {
                    "label": label, "conf": conf, "p_real": p_real,
                    "kind": "unsure" if conf < 60 else label.lower(),
                    "english": english, "script": script, "translated": translated,
                    "lang_name": script if lang_choice == "auto" else lang_choice,
                    "text": text, "stats": text_stats(text, script),
                    "real_df": real_words, "fake_df": fake_words,
                }
                st.session_state.history.append({
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Language": script if script != "Latin" else "English/Latin",
                    "Preview": " ".join(text.split())[:80] + "...",
                    "Prediction": label,
                    "Confidence (%)": round(conf, 1),
                })

    # ----- Step 2: verdict -----
    res = st.session_state.result
    with right:
        with st.container(key=f"result_panel_{res['kind'] if res else 'empty'}"):
            st.markdown(ui.step_html(2, T["result_heading"]), unsafe_allow_html=True)
            if res is None:
                st.markdown(ui.empty_html(T["info_wait"]), unsafe_allow_html=True)
            else:
                kind = res["kind"]
                title = {"real": T["looks_real"], "fake": T["looks_fake"], "unsure": T["uncertain"]}[kind]
                lean = T["looks_real"] if res["label"] == "Real" else T["looks_fake"]
                st.markdown(
                    ui.verdict_html(kind, title, res["conf"], lean, T["confidence"], T["leaning"],
                                    res["p_real"], T["prob_real"]) + ui.quote_html(res["text"]),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    ui.strip_html([(res["stats"]["words"], T["words"]), (res["stats"]["excl"], T["excl"]),
                                   (res["stats"]["caps"], T["caps"])]),
                    unsafe_allow_html=True,
                )
                if res["translated"]:
                    st.caption(f"\U0001F310 {T['translated_note']} ({res['lang_name']})")

                st.markdown(ui.section_title_html(T["why"]), unsafe_allow_html=True)
                st.markdown(
                    ui.legend_html(T["toward_real"], T["toward_fake"])
                    + ui.marked_html(res["english"], res["real_df"]["word"], res["fake_df"]["word"]),
                    unsafe_allow_html=True,
                )
                with st.expander(f"\U0001F4CA {T['toward_real']} / {T['toward_fake']}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        st.caption(T["toward_real"])
                        if len(res["real_df"]):
                            st.bar_chart(res["real_df"].set_index("word"), color="#0B6B40", horizontal=True)
                        else:
                            st.caption(T["none"])
                    with ec2:
                        st.caption(T["toward_fake"])
                        if len(res["fake_df"]):
                            st.bar_chart(res["fake_df"].set_index("word").abs(), color="#B91C1C", horizontal=True)
                        else:
                            st.caption(T["none"])
                if res["translated"]:
                    with st.expander(T["translated_exp"]):
                        st.write(res["english"])

    st.markdown(ui.note_html(T["disclaimer"]), unsafe_allow_html=True)

# ---------- Tab 2: batch ----------
with tab_batch:
    st.write(T["batch_intro"])
    csv_file = st.file_uploader(T["csv_file"], type=["csv"], key="batch_csv")
    if csv_file is not None:
        data = pd.read_csv(csv_file)
        column = st.selectbox(T["which_col"], list(data.columns))
        if st.button(T["run_batch"]):
            texts = data[column].fillna("").astype(str).tolist()
            english_texts, scripts, failed = [], [], False
            bar = st.progress(0.0, text=T["batch_progress"])
            try:
                for i, t_ in enumerate(texts):
                    eng, script, _ = prepare(t_, "auto") if t_.strip() else ("", "Latin", False)
                    english_texts.append(eng)
                    scripts.append(script if script != "Latin" else "English/Latin")
                    bar.progress((i + 1) / len(texts), text=T["batch_progress"])
            except TranslationError as exc:
                failed = True
                st.error(T["translation_failed"])
                st.caption(f"Details: {str(exc)[:300]}")
            if not failed:
                probs = model.predict_proba([clean_text(t_) for t_ in english_texts])[:, 1]
                out = data.copy()
                out["Language"] = scripts
                out["Prediction"] = ["Real" if p >= 0.5 else "Fake" for p in probs]
                out["Confidence (%)"] = [round(max(p, 1 - p) * 100, 1) for p in probs]
                n_fake = int((out["Prediction"] == "Fake").sum())
                b1, b2, b3 = st.columns(3)
                b1.metric(T["checked"], len(out))
                b2.metric(T["pred_fake"], n_fake)
                b3.metric(T["pred_real"], len(out) - n_fake)
                st.dataframe(out)
                st.download_button(T["dl_results"], out.to_csv(index=False).encode("utf-8-sig"),
                                   file_name="predictions.csv", mime="text/csv")

# ---------- Tab 3: history ----------
with tab_history:
    if st.session_state.history:
        hist = pd.DataFrame(st.session_state.history)
        st.dataframe(hist)
        h1, h2 = st.columns(2)
        h1.download_button(T["dl_history"], hist.to_csv(index=False).encode("utf-8-sig"),
                           file_name="history.csv", mime="text/csv")
        if h2.button(T["clear_history"]):
            st.session_state.history = []
            st.rerun()
    else:
        st.info(T["hist_empty"])

# ---------- Tab 4: performance ----------
with tab_perf:
    if os.path.exists("metrics.json"):
        with open("metrics.json") as f:
            metrics = json.load(f)
        res_df = pd.DataFrame(metrics["results"])
        p1, p2 = st.columns(2)
        p1.metric(T["perf_trained"], f"{metrics['n_train']:,}")
        p2.metric(T["perf_tested"], f"{metrics['n_test']:,}")
        best = res_df.sort_values("F1", ascending=False).iloc[0]
        st.metric(T["best_model"], best["Model"], f"{best['F1'] * 100:.2f}% F1")
        st.dataframe(res_df.set_index("Model"))
        st.markdown(ui.section_title_html(T["acc_compare"]), unsafe_allow_html=True)
        st.bar_chart(res_df.set_index("Model")[["Accuracy", "F1"]])
        if os.path.exists("confusion_matrix.png"):
            st.markdown(ui.section_title_html(T["cm_title"]), unsafe_allow_html=True)
            st.image("confusion_matrix.png", width=480)
    else:
        st.info(T["perf_missing"])

# ---------- Tab 5: about ----------
with tab_about:
    st.markdown(ui.section_title_html(T["about_how"]), unsafe_allow_html=True)
    for key in ("about_1", "about_2", "about_3", "about_4"):
        st.write(T[key])
    st.write(T["about_models"])
    st.markdown(ui.section_title_html(T["about_lim"]), unsafe_allow_html=True)
    for key in ("lim_1", "lim_2", "lim_3", "lim_4"):
        st.write(f"- {T[key]}")
