# Fake News Detector

Classifies news text as Fake or Real using TF-IDF + Logistic Regression, with a multilingual Streamlit web app.

## Features
- Real/Fake prediction with confidence score and probability bar
- Multilingual: write articles in English or Hindi, Gujarati, Marathi, Bengali, Tamil, Telugu,
  Kannada, Malayalam, Punjabi, Urdu, Odia or Assamese (translated to English, then classified)
- Redesigned interface: high-contrast "fact-checker's desk" look, big yellow Check button, a rubber-stamp verdict,
  and the article shown with the influential words highlighted green (Real) / red (Fake)
- Interface language selector (top right) for the same 13 languages. The interface text is built in
  (`translations.py`), so it works offline and is never rate-limited
- Image upload: upload a screenshot or photo of an article, the text is read with OCR (Tesseract),
  shown for editing, then checked like pasted text
- Word-level explanation: which words pushed the result toward Real or Fake
- Text statistics, .txt upload, sample articles (including one in Hindi)
- Batch check: upload a CSV and download predictions
- Session history with CSV download
- Model comparison tab: Logistic Regression vs Naive Bayes vs Linear SVM, plus confusion matrix

## Setup
    pip install -r requirements.txt

Put the Kaggle "Fake and Real News Dataset" files in a `data/` folder
(`Fake.csv` and `True.csv`, or the `.zip` versions - both work).

## Extra setup for image upload (Tesseract OCR)
The Python packages (`pytesseract`, `pillow`) install with `pip install -r requirements.txt`, but the
OCR program itself is separate and free:
1. Download the Windows installer from https://github.com/UB-Mannheim/tesseract/wiki and run it
   (use the folder it suggests; do not install into a folder that already has other files).
2. In the installer, open **Additional language data** and tick every language you want to read:
   Hindi, Gujarati, Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi, Urdu, Odia, Assamese.
   English is always included.
3. Restart the app. The app finds Tesseract in its default folder automatically.
4. Run `python test_ocr.py` to check that it works and see which languages are installed.

For best results, choose the article's language in the dropdown instead of Auto-detect (Auto reads
English plus up to four of the installed Indian languages). Clear, straight, high-resolution images
work best, and you can correct the extracted text before checking it.

## Run
    python train.py                    # trains, compares models, saves model.joblib + metrics.json
    python -m streamlit run app.py     # launches the web app

Article translation uses Google Translate through the `deep-translator` package, so the app needs an
internet connection for non-English articles (the interface language does not need one). If Google
rate-limits your network, articles are translated by the free MyMemory service instead
(optional: set the environment variable MYMEMORY_EMAIL to raise its daily free limit).
`python test_translate.py` checks whether translation works on your computer.

## Files
- `train.py` - training and model comparison
- `app.py`   - Streamlit interface
- `ui.py`    - colours, styles and HTML pieces of the design
- `.streamlit/config.toml` - colour theme (created automatically if missing; restart the app once)
- `i18n.py`  - language detection and article translation
- `ocr.py`   - reads text from images (Tesseract)
- `test_ocr.py` - checks that OCR works on your computer
- `translations.py` - built-in interface text for 12 Indian languages (edit to improve wording)
- `utils.py` - shared text cleaning
