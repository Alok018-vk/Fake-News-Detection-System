import json
import pandas as pd
import joblib
import numpy as np

from train_helpers import clean_text
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


print("Loading data...")
fake = pd.read_csv("data/Fake.csv")
real = pd.read_csv("data/True.csv")

fake["label"] = 0
real["label"] = 1

df = pd.concat([fake, real], ignore_index=True)
print("Total rows:", len(df))
print(df["label"].value_counts())

df["content"] = df["title"].fillna("") + " " + df["text"].fillna("")
df["content"] = df["content"].apply(clean_text)
df = df[df["content"].str.len() > 0]
df = df.drop_duplicates(subset="content")
df = df.sample(frac=1, random_state=42)
print("Rows after cleaning:", len(df))

X_train, X_test, y_train, y_test = train_test_split(
    df["content"], df["label"],
    test_size=0.2, random_state=42, stratify=df["label"]
)

vectorizer = TfidfVectorizer(stop_words="english", max_df=0.7,
                             max_features=30000, ngram_range=(1, 2))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Naive Bayes": MultinomialNB(),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42,
                                            n_jobs=-1),
}

results = {}
best_name = ""
best_acc = 0
best_model = None

for name, model in models.items():
    print("\nTraining", name, "...")
    model.fit(X_train_vec, y_train)
    pred = model.predict(X_test_vec)
    acc = accuracy_score(y_test, pred)
    cm = confusion_matrix(y_test, pred)

    print("====", name, "====")
    print("Accuracy:", round(acc * 100, 2), "%")
    print(classification_report(y_test, pred, target_names=["Fake", "Real"]))

    results[name] = {
        "accuracy": round(acc * 100, 2),
        "confusion_matrix": cm.tolist()
    }

    if acc > best_acc:
        best_acc = acc
        best_name = name
        best_model = model

print("Best model:", best_name)

print("\n--- RL-style Model Selection ---")
rewards = {name: results[name]["accuracy"] for name in results if name != "best_model"}
print("Rewards (accuracy) for each arm:")
for name, reward in rewards.items():
    print(f"  {name}: {reward}")
print(f"Greedy policy picks: {best_name} (highest reward = {best_acc*100:.2f}%)")

joblib.dump(vectorizer, "model/vectorizer.pkl")
joblib.dump(best_model, "model/model.pkl")
results["best_model"] = best_name
with open("model/results.json", "w") as f:
    json.dump(results, f)
print("\nSaved model files in model/ folder")

print("\n--- K-Means Clustering ---")
sample = X_train_vec[:5000]
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
kmeans.fit(sample)

words = vectorizer.get_feature_names_out()
print("Top words in each K-Means cluster:")
cluster_info = {}
for i in range(5):
    top_ids = kmeans.cluster_centers_[i].argsort()[-8:][::-1]
    top_words = [words[j] for j in top_ids]
    cluster_info[f"cluster_{i}"] = top_words
    print(f"  Cluster {i}: {top_words}")

with open("model/clusters.json", "w") as f:
    json.dump(cluster_info, f)

print("\nDone! Now run:  streamlit run app.py")
