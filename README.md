# Fake News Detection System (Enhanced)

A Machine Learning + AI project that detects fake news using multiple techniques from our AI course.
Made as an AI course project using Python, scikit-learn, Streamlit, and Google Gemini API.

## Course Topics Used

| Week | Topic | How We Used It |
|------|-------|---------------|
| W2 | BFS & DFS (Uninformed Search) | Build keyword graph from article, run BFS/DFS to analyze structure |
| W3 | Heuristics & Greedy Search | 4 heuristic functions score credibility (clickbait, sources, tone, structure) |
| W5 | CSP (Constraint Satisfaction) | Extract claims and check for internal contradictions |
| W6 | Reinforcement Learning | Model selection treated as multi-armed bandit problem |
| W7 | ML - Classification | Logistic Regression, Naive Bayes, Random Forest on TF-IDF features |
| W7 | ML - Clustering | K-Means groups articles into 5 topic clusters |
| W8 | LLMs | Google Gemini API for fact-checking and India news |
| W9 | Deployment | Streamlit web app with multiple pages |

## Features

- **Text Type Detection** - checks if input is news, opinion, social media, or other text
- **ML Prediction** - Fake/Real classification with confidence scores
- **Graph Analysis** - BFS and DFS on keyword graph to check article structure
- **Credibility Scoring** - heuristic functions check clickbait, sources, tone, structure
- **Claim Consistency** - CSP checks if claims in the article contradict each other
- **AI Fact Check** - Gemini API analyzes the article (optional, needs API key)
- **India News** - fetch current India news and compare articles against real events
- **Model Comparison** - compare 3 ML models with accuracy, confusion matrix, and RL explanation

## Dataset

ISOT Fake and Real News Dataset from Kaggle:
https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset

Download and put `Fake.csv` and `True.csv` inside the `data/` folder.

## How to Run

### Option 1: Brutalist Web Frontend (Default / Recommended)
Inspired by [designmd.app/library/brutalist-web-design](https://designmd.app/library/brutalist-web-design):
```bash
pip install -r requirements.txt
python server.py
```
Open **`http://localhost:8501`** in your browser.

### Option 2: Legacy Streamlit Frontend
```bash
streamlit run app.py
```

## Gemini API Key (Optional)

For AI fact-checking and India news features:
1. Go to [ai.google.dev](https://ai.google.dev)
2. Get a free API key
3. Enter it in the sidebar of the app

The app works without the key too - just the ML and heuristic features.

## Files

| File | What it does |
|------|-------------|
| `train_model.py` | Trains 3 ML models, runs K-Means clustering, saves everything |
| `train_helpers.py` | Text cleaning + text type detection functions |
| `news_graph.py` | BFS/DFS graph analysis of article structure |
| `credibility_scorer.py` | Heuristic credibility scoring (Greedy approach) |
| `fact_checker.py` | CSP claim checking + Gemini API fact-checking |
| `app.py` | Streamlit web app with 5 pages |

## Limitations

- The ML model was trained on US political news (2016-2017), so it may not work perfectly on Indian or recent news
- Heuristic and graph analysis are rule-based, not perfect
- Gemini features need internet + API key
- CSP only finds internal contradictions, not factual errors
- This is a student project - always verify news from trusted sources!
