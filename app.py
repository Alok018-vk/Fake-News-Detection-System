import json
import os
import joblib
import pandas as pd
import streamlit as st

from train_helpers import clean_text, is_news_text, classify_text_type
from news_graph import analyze_news_structure
from credibility_scorer import greedy_credibility_score
from fact_checker import (extract_claims, csp_check_claims,
                          check_with_gemini, fetch_india_news,
                          compare_with_current_news)


st.set_page_config(page_title="Fake News Detector", page_icon="📰", layout="wide")


@st.cache_resource
def load_model():
    vectorizer = joblib.load("model/vectorizer.pkl")
    model = joblib.load("model/model.pkl")
    with open("model/results.json") as f:
        results = json.load(f)
    clusters = {}
    if os.path.exists("model/clusters.json"):
        with open("model/clusters.json") as f:
            clusters = json.load(f)
    return vectorizer, model, results, clusters


try:
    vectorizer, model, results, clusters = load_model()
except FileNotFoundError:
    st.error("Model files not found. Please run  python train_model.py  first.")
    st.stop()


st.sidebar.title("📰 Fake News Detector")
st.sidebar.write("Enhanced AI Course Project")

page = st.sidebar.radio("Go to", [
    "🔍 Detect News",
    "📊 Model Comparison",
    "🌐 India News Check",
    "🧠 How It Works",
    "ℹ️ About"
])

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Gemini API (Optional)")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password",
                                 help="Needed for AI fact-checking and India news. "
                                      "Get it free from ai.google.dev")


if page == "🔍 Detect News":
    st.title("🔍 Fake News Detection")
    st.write("Paste a news article or any text below. The system will analyze it "
             "using multiple AI techniques.")

    user_text = st.text_area("Enter text here", height=200,
                             placeholder="Paste a news headline or article...")

    if st.button("🔎 Analyze", type="primary"):
        if not user_text.strip():
            st.warning("Please enter some text first.")
        else:
            st.markdown("---")
            st.subheader("Step 1: Text Type Detection")

            text_type = classify_text_type(user_text)
            is_news, reason = is_news_text(user_text)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Text Type", text_type.replace("_", " ").title())
            with col2:
                st.metric("Is it News?", "Yes ✅" if is_news else "No ❌")

            st.caption(reason)

            if not is_news and len(user_text.split()) < 20:
                st.warning("This doesn't look like a news article. "
                          "The ML model works best with news text. "
                          "Results may not be accurate.")

            st.markdown("---")
            st.subheader("Step 2: ML Model Prediction")
            st.caption("Using " + results["best_model"] + " (Logistic Regression / Naive Bayes / Random Forest)")

            cleaned = clean_text(user_text)
            vec = vectorizer.transform([cleaned])
            prediction = model.predict(vec)[0]
            probability = model.predict_proba(vec)[0]

            if prediction == 1:
                st.success("✅ The ML model thinks this is REAL news")
            else:
                st.error("❌ The ML model thinks this is FAKE news")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Fake probability:** " + str(round(probability[0] * 100, 1)) + "%")
                st.progress(float(probability[0]))
            with col2:
                st.write("**Real probability:** " + str(round(probability[1] * 100, 1)) + "%")
                st.progress(float(probability[1]))

            st.markdown("---")
            st.subheader("Step 3: Heuristic Credibility Analysis")
            st.caption("Course: W3 - Greedy Best-First Search with heuristics")

            cred_score, breakdown, verdict = greedy_credibility_score(user_text)

            st.metric("Credibility Score", str(cred_score) + " / 100")
            st.write("**Verdict:** " + verdict)

            breakdown_df = pd.DataFrame({
                "Heuristic": ["Clickbait Check", "Source Quality",
                              "Emotional Tone", "Structure Quality"],
                "Score": [breakdown["clickbait_score"],
                          breakdown["source_quality"],
                          breakdown["emotional_tone"],
                          breakdown["structure_quality"]]
            })
            st.bar_chart(breakdown_df.set_index("Heuristic"))

            st.markdown("---")
            st.subheader("Step 4: Graph Analysis (BFS & DFS)")
            st.caption("Course: W2 - Uninformed Search (BFS and DFS)")

            graph_results = analyze_news_structure(user_text)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Keywords Found", graph_results["num_keywords"])
            with col2:
                st.metric("Connections", graph_results["num_connections"])
            with col3:
                st.metric("Structure Score", str(graph_results["structure_score"]) + "/100")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**BFS Traversal Order:**")
                if graph_results["bfs_order"]:
                    st.write(" → ".join(graph_results["bfs_order"]))
                else:
                    st.write("No keywords found to traverse.")
            with col2:
                st.write("**DFS Traversal Order:**")
                if graph_results["dfs_order"]:
                    st.write(" → ".join(graph_results["dfs_order"]))
                else:
                    st.write("No keywords found to traverse.")

            if graph_results["keyword_freq"]:
                with st.expander("📊 Keyword Frequency"):
                    freq_df = pd.DataFrame(
                        list(graph_results["keyword_freq"].items()),
                        columns=["Keyword", "Frequency"]
                    ).sort_values("Frequency", ascending=False)
                    st.bar_chart(freq_df.set_index("Keyword"))

            st.markdown("---")
            st.subheader("Step 5: Claim Consistency (CSP)")
            st.caption("Course: W5 - Constraint Satisfaction Problems")

            claims = extract_claims(user_text)
            if claims:
                claim_results, consistency = csp_check_claims(claims)
                st.metric("Consistency Score", str(consistency) + " / 100")

                for cr in claim_results:
                    icon = "✅" if cr["status"] == "consistent" else "⚠️"
                    st.write(icon + " " + cr["claim"])
                    st.caption("Status: " + cr["status"])
            else:
                st.info("No specific factual claims found to check.")

            if api_key:
                st.markdown("---")
                st.subheader("Step 6: AI Fact Check (Gemini)")
                st.caption("Course: W8 - Large Language Models")

                with st.spinner("Asking Gemini to fact-check..."):
                    ai_result, ai_error = check_with_gemini(user_text, api_key)

                if ai_result:
                    st.write(ai_result)
                else:
                    st.error(ai_error)

                with st.spinner("Comparing with current events..."):
                    compare_result, compare_error = compare_with_current_news(
                        user_text, api_key)

                if compare_result:
                    st.write("**Current Events Comparison:**")
                    st.write(compare_result)
                elif compare_error:
                    st.warning(compare_error)

            st.markdown("---")
            st.subheader("📋 Final Summary")

            ml_score = probability[1] * 100
            final_score = (ml_score * 0.4 +
                          cred_score * 0.3 +
                          graph_results["structure_score"] * 0.15 +
                          (consistency if claims else 50) * 0.15)

            st.metric("Combined Confidence Score",
                     str(round(final_score, 1)) + " / 100")

            if final_score >= 65:
                st.success("📰 Overall: This article appears to be REAL")
            elif final_score >= 40:
                st.warning("⚠️ Overall: This article is UNCERTAIN - verify from trusted sources")
            else:
                st.error("🚫 Overall: This article appears to be FAKE")

            st.caption("⚠️ This is an AI course project. Always verify news "
                      "from multiple trusted sources before sharing.")


elif page == "📊 Model Comparison":
    st.title("📊 Model Comparison")
    st.caption("Course: W7 - Machine Learning (Classification)")

    names = [k for k in results.keys() if k != "best_model"]
    acc = [results[n]["accuracy"] for n in names]

    table = pd.DataFrame({"Model": names, "Accuracy (%)": acc})
    st.table(table)

    st.bar_chart(table.set_index("Model"))

    st.write("**Best model used in the app:** " + results["best_model"])

    st.subheader("Confusion Matrix - " + results["best_model"])
    cm = results[results["best_model"]]["confusion_matrix"]
    cm_df = pd.DataFrame(cm, index=["Actual Fake", "Actual Real"],
                         columns=["Predicted Fake", "Predicted Real"])
    st.table(cm_df)

    st.markdown("---")
    st.subheader("🎰 RL-inspired Model Selection")
    st.caption("Course: W6 - Reinforcement Learning (Multi-Armed Bandit)")
    st.write("""
    We treat model selection like a **multi-armed bandit** problem from 
    Reinforcement Learning:
    - Each model is an **arm** (action)
    - The **reward** is the accuracy on test data
    - We use a **greedy policy**: pick the arm with highest reward
    
    This is a simplified version of the explore-exploit tradeoff in RL.
    In a real system, we might try different models on different subsets
    of data (exploration) before committing to the best one (exploitation).
    """)

    reward_data = pd.DataFrame({
        "Model (Arm)": names,
        "Reward (Accuracy %)": acc
    })
    st.table(reward_data)
    st.write("**Greedy policy selected:** " + results["best_model"])

    if clusters:
        st.markdown("---")
        st.subheader("📦 K-Means News Clusters")
        st.caption("Course: W7 - Unsupervised Learning (K-Means)")
        st.write("The model grouped training articles into 5 topic clusters:")

        for name, words in clusters.items():
            cluster_num = name.split("_")[1]
            st.write(f"**Cluster {cluster_num}:** " + ", ".join(words))


elif page == "🌐 India News Check":
    st.title("🌐 Current India News")
    st.caption("Course: W8 - LLMs (using Gemini API)")

    if not api_key:
        st.info("🔑 Enter your Gemini API key in the sidebar to use this feature. "
                "Get a free key from [ai.google.dev](https://ai.google.dev)")
    else:
        st.write("Fetching current news headlines from India using Gemini AI...")

        if st.button("📡 Fetch Latest News"):
            with st.spinner("Asking Gemini for current India news..."):
                news_text, error = fetch_india_news(api_key)

            if news_text:
                st.write(news_text)
            else:
                st.error(error)

        st.markdown("---")
        st.subheader("🔍 Check if Your Article Matches Real News")
        st.write("Paste an article about India below to check if it matches "
                 "real current events.")

        india_text = st.text_area("Paste article about India", height=150,
                                   key="india_check")

        if st.button("Check Against Real News"):
            if india_text.strip():
                with st.spinner("Comparing with real events..."):
                    result, error = compare_with_current_news(india_text, api_key)
                if result:
                    st.write(result)
                else:
                    st.error(error)
            else:
                st.warning("Please enter some text first.")


elif page == "🧠 How It Works":
    st.title("🧠 How This System Works")
    st.write("This project uses multiple AI techniques from our course. "
             "Here's how each part works:")

    st.subheader("1. BFS & DFS - Article Structure Analysis")
    st.caption("Week 2: Uninformed Search")
    st.write("""
    We build a **graph** from the news article where:
    - **Nodes** = important keywords (government, election, police, etc.)
    - **Edges** = two keywords appear in the same sentence
    
    Then we run **BFS** (Breadth-First Search) and **DFS** (Depth-First Search):
    - **BFS** tells us how topics spread level by level - real news 
      usually has well-connected topics
    - **DFS** goes deep into one branch - helps find if the article 
      stays on topic or jumps around
    - **Connected components** show if the article has one main story 
      or many disconnected claims
    """)

    st.subheader("2. Heuristic Credibility Scoring")
    st.caption("Week 3: Informed Search - Greedy Best-First Search")
    st.write("""
    Like **Greedy Best-First Search** uses a heuristic function h(n) to 
    decide which node to explore, we use 4 heuristic functions to 
    estimate credibility:
    
    | Heuristic | What it checks |
    |-----------|---------------|
    | h_clickbait | ALL CAPS, exclamation marks, sensational words |
    | h_source_quality | Does it cite sources, names, dates? |
    | h_emotional_tone | Is the language neutral or emotional? |
    | h_structure | Sentence length, quotes, paragraphs |
    
    Each heuristic returns a score 0-100, and we combine them with 
    weights (like how A* combines g(n) + h(n)).
    """)

    st.subheader("3. Constraint Satisfaction - Claim Checking")
    st.caption("Week 5: CSP")
    st.write("""
    We model fact-checking as a **CSP** (Constraint Satisfaction Problem):
    - **Variables** = factual claims found in the article
    - **Domain** = {consistent, inconsistent}
    - **Constraints** = claims should not contradict each other
    
    If the article says "X confirmed" in one place and "X denied" in 
    another, that's a constraint violation → suspicious!
    
    We use **backtracking** to check all claim pairs for contradictions.
    """)

    st.subheader("4. Reinforcement Learning - Model Selection")
    st.caption("Week 6: RL / Multi-Armed Bandit")
    st.write("""
    Model selection is like a **multi-armed bandit** problem:
    - Each ML model is an "arm" we can pull
    - The "reward" is the accuracy on test data
    - We use a **greedy policy** to pick the best model
    
    In a full RL setup, we'd explore different models on different 
    data subsets (exploration vs exploitation tradeoff).
    """)

    st.subheader("5. Machine Learning - Classification & Clustering")
    st.caption("Week 7: ML")
    st.write("""
    **Classification** (Supervised Learning):
    - **Logistic Regression** - learns a decision boundary between fake/real
    - **Naive Bayes** - uses Bayes' theorem P(fake|words) to classify
    - **Random Forest** - ensemble of decision trees voting together
    - All trained on **TF-IDF** features (word frequencies)
    
    **Clustering** (Unsupervised Learning):
    - **K-Means** groups articles into 5 topic clusters
    - Shows what kinds of news topics exist in the dataset
    """)

    st.subheader("6. Large Language Models - Gemini API")
    st.caption("Week 8: LLMs")
    st.write("""
    When an API key is provided, we use **Google Gemini** (a Large Language 
    Model) to:
    - Fact-check the article against real-world knowledge
    - Fetch current India news headlines
    - Compare the article with real events
    
    This shows how LLMs work: they process **tokens** (word pieces), 
    use **attention** to understand context, and generate responses.
    """)

    st.subheader("7. Deployment - Streamlit Web App")
    st.caption("Week 9: Application & Deployment")
    st.write("""
    The whole system is deployed as a **Streamlit** web app:
    - Load trained models with joblib
    - Interactive UI with text input, buttons, charts
    - Multiple pages for different features
    - API key input for optional Gemini features
    """)


else:
    st.title("ℹ️ About This Project")
    st.write("""
    This project is made for our **AI course**. It uses multiple AI 
    techniques to detect fake news.
    
    ### Course Topics Used
    
    | Week | Topic | How We Used It |
    |------|-------|---------------|
    | W2 | BFS & DFS | Graph analysis of article structure |
    | W3 | Heuristics & Greedy | Credibility scoring with heuristic functions |
    | W5 | CSP | Claim consistency checking with constraints |
    | W6 | Reinforcement Learning | Model selection as multi-armed bandit |
    | W7 | ML (Classification) | Logistic Regression, Naive Bayes, Random Forest |
    | W7 | ML (Clustering) | K-Means for topic discovery |
    | W8 | LLMs | Gemini API for fact-checking |
    | W9 | Deployment | Streamlit web app |
    
    ### New Features (Enhanced Version)
    - ✅ Detects if input is actually news or random text
    - ✅ Classifies text type (news, opinion, social media, other)
    - ✅ BFS/DFS graph analysis of article keyword structure
    - ✅ Heuristic-based credibility scoring (clickbait, sources, tone, structure)
    - ✅ CSP-based claim consistency checking
    - ✅ Gemini AI fact-checking (optional)
    - ✅ Current India news comparison
    - ✅ Random Forest added as 3rd model
    - ✅ Combined confidence score from all analyses
    - ✅ Detailed "How It Works" page explaining each AI technique
    
    ### Limitations
    - The ML model was trained on US political news (2016-2017 ISOT dataset), 
      so it may not work perfectly on Indian or recent news
    - The heuristic and graph analysis are rule-based, not ML
    - Gemini API features need an internet connection and API key
    - The CSP checker only finds internal contradictions, not factual errors
    - This is a student project - always verify news from trusted sources!
    
    ### Dataset
    ISOT Fake News Dataset from Kaggle 
    (Fake.csv + True.csv, ~44,000 articles)
    """)
