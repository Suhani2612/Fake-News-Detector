"""Train and compare fake-news classifiers.

Input : data/Fake.csv(.zip) and data/True.csv(.zip)  (Kaggle "Fake and Real News Dataset")
Output: model.joblib, metrics.json, confusion_matrix.png
"""
import json
import os
import time

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score,
                             f1_score, precision_score, recall_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

from utils import clean_text


def find_file(name):
    """Use the .csv if it exists, otherwise the .zip (pandas reads zips directly)."""
    for path in (f"data/{name}.csv", f"data/{name}.csv.zip"):
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"Could not find data/{name}.csv or data/{name}.csv.zip")


# 1. Load data (label: 0 = Fake, 1 = Real)
fake = pd.read_csv(find_file("Fake")); fake["label"] = 0
real = pd.read_csv(find_file("True")); real["label"] = 1
df = pd.concat([fake, real], ignore_index=True)
df = df.drop_duplicates(subset=["title", "text"]).reset_index(drop=True)
print(f"Loaded {len(df)} articles ({(df.label == 0).sum()} fake, {(df.label == 1).sum()} real)")

# 2. Clean text
df["content"] = (df["title"].fillna("") + " " + df["text"].fillna("")).map(clean_text)

# 3. Split
X_train, X_test, y_train, y_test = train_test_split(
    df["content"], df["label"], test_size=0.2, random_state=42, stratify=df["label"])

# 4. Vectorize once, share it between all models (faster)
vectorizer = TfidfVectorizer(stop_words="english", max_df=0.7, max_features=50000)
Xtr = vectorizer.fit_transform(X_train)
Xte = vectorizer.transform(X_test)

candidates = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Naive Bayes": MultinomialNB(),
    "Linear SVM": LinearSVC(),
}

# 5. Train + evaluate every model
results, fitted, preds = [], {}, {}
for name, clf in candidates.items():
    start = time.time()
    clf.fit(Xtr, y_train)
    pred = clf.predict(Xte)
    fitted[name], preds[name] = clf, pred
    results.append({
        "Model": name,
        "Accuracy": round(accuracy_score(y_test, pred), 4),
        "Precision": round(precision_score(y_test, pred), 4),
        "Recall": round(recall_score(y_test, pred), 4),
        "F1": round(f1_score(y_test, pred), 4),
        "Train time (s)": round(time.time() - start, 2),
    })
    print(results[-1])

# 6. Save the Logistic Regression pipeline: it gives probabilities AND
#    word weights, which the app uses to explain each prediction.
lr = fitted["Logistic Regression"]
pipeline = make_pipeline(vectorizer, lr)
joblib.dump(pipeline, "model.joblib")

with open("metrics.json", "w") as f:
    json.dump({"results": results, "n_train": len(X_train), "n_test": len(X_test)}, f, indent=2)

ConfusionMatrixDisplay.from_predictions(
    y_test, preds["Logistic Regression"], display_labels=["Fake", "Real"], cmap="Blues")
plt.title("Confusion Matrix - Logistic Regression")
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=150)
print("Saved model.joblib, metrics.json, confusion_matrix.png")
