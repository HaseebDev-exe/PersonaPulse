# ⚡ PersonaPulse — Grounded Customer Simulation Engine

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" alt="Streamlit UI" />
  <img src="https://img.shields.io/badge/Cohere-Command--R-6B21A8?style=for-the-badge&logo=cohere&logoColor=white" alt="Cohere AI" />
  <img src="https://img.shields.io/badge/Tavily-Live_Search-0052CC?style=for-the-badge" alt="Tavily Search" />
  <img src="https://img.shields.io/badge/ChromaDB-Vector_Store-FF6600?style=for-the-badge" alt="ChromaDB" />
  <img src="https://img.shields.io/badge/License-MIT-green.style=for-the-badge" alt="License" />
</p>

---

## 📌 Executive Overview

**PersonaPulse** is a RAG-grounded multi-persona decision stress-testing engine. It allows product managers, founders, and executives to test strategic business changes (price hikes, feature sunsets, policy updates) against **real grounded customer sentiment** before rollout.

Unlike standard LLM prompts that invent reactions, PersonaPulse retrieves exact customer feedback from an in-memory ChromaDB vector store and grounds persona simulations directly on retrieved snippets—preventing hallucinations and providing audit-trail verification.

---

## 📐 System Architecture

```
                               ┌────────────────────────────────────────┐
                               │           User Strategic Query         │
                               │   "15% price hike + 5-day return"      │
                               └──────────────────┬─────────────────────┘
                                                  │
                                                  ▼
                        ┌──────────────────────────────────────────────────┐
                        │                Mode Selection (UI)               │
                        └─────────┬──────────────────────────────┬─────────┘
                                  │                              │
                    ┌─────────────┴────────────┐   ┌─────────────┴────────────┐
                    │ Mode 1: Customer Base    │   │ Mode 2: Live Web Search  │
                    │ (.csv / .json / Presets) │   │  (Tavily API / Domains)  │
                    └─────────────┬────────────┘   └─────────────┬────────────┘
                                  │                              │
                                  └──────────────┬───────────────┘
                                                 │
                                                 ▼
                                ┌──────────────────────────────────┐
                                │   Sentence-Transformers Embed    │
                                │    (all-MiniLM-L6-v2, Cosine)    │
                                └────────────────┬─────────────────┘
                                                 │
                                                 ▼
                                ┌──────────────────────────────────┐
                                │   ChromaDB Ephemeral Vector Store│
                                │   - Out-of-Distribution Check   │
                                └────────────────┬─────────────────┘
                                                 │
                                                 ▼
                                ┌──────────────────────────────────┐
                                │  Grounding Context & Audit Trail │
                                └────────────────┬─────────────────┘
                                                 │
                                                 ▼
                                ┌──────────────────────────────────┐
                                │   Cohere Multi-Persona Engine    │
                                │  (Price-Sensitive vs Loyalist)   │
                                └────────────────┬─────────────────┘
                                                 │
                                                 ▼
                                ┌──────────────────────────────────┐
                                │    Executive Executive Dashboard │
                                │ (Churn Risk, Objections, Audit)  │
                                └──────────────────────────────────┘
```

---

## ✨ Key Features & Capability Matrix

| Feature | Mode 1: Custom Dataset / Presets | Mode 2: Live Web Review Search |
| :--- | :--- | :--- |
| **Data Source** | Local `.csv` / `.json` upload or historical presets | Real-time live web review crawling via Tavily API |
| **Supported Formats** | CSV (`text`, `review`, `feedback`, `details`, etc.) & JSON lists/objects | Trustpilot, Reddit, G2, Capterra, Sitejabber |
| **Fallback Mechanism** | Falls back to preset industry categories | Falls back to synthetic cold-start archetypes |
| **Audit Trail Badges** | `[Client Verified Data]`, `[Verified Historical RAG]` | `[Live Web: Trustpilot]`, `[Live Web: Reddit]`, etc. |
| **OOD Detection** | Cosine distance boundary thresholding | Cosine distance boundary thresholding |
| **LLM Provider** | Cohere Command API (with heuristic fallback) | Cohere Command API (with heuristic fallback) |

---

## 🚀 Getting Started

### 1. Prerequisites & Installation

Clone the repository and set up a virtual environment:

```bash
git clone https://github.com/HaseebDev-exe/PersonaPulse.git
cd PersonaPulse

# Create virtual environment
python -m venv venv

# Activate on Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables (Optional)

Create a `.env` file or export your keys in the terminal:

```bash
# Cohere API Key (for Generative Multi-Persona Simulation)
export CO_API_KEY="your_cohere_api_key_here"

# Tavily API Key (for Live Web Review Search)
export TAVILY_API_KEY="your_tavily_api_key_here"
```

*Note: You can also paste your API keys directly into the Streamlit sidebar.*

### 3. Launching the App

Run the Streamlit application locally:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 📊 Usage Guide

### Mode 1: Custom Dataset Upload & Presets
1. Select **Mode 1** in the sidebar.
2. Drag and drop your company's customer review CSV (`.csv`) or JSON (`.json`). The engine automatically detects columns named `text`, `review`, `feedback`, `comment`, `details`, `description`, or `notes` (or defaults to the first non-numeric string column).
3. If no file is uploaded, pick a pre-loaded industry dataset (e.g. *SaaS - Enterprise Workflow*, *E-Commerce - Fashion & Apparel*).
4. Enter your proposed change and click **⚡ Run Customer Simulation**.

### Mode 2: Live Web Review Search
1. Select **Mode 2** in the sidebar.
2. Enter the business name or domain (e.g. `Daraz Pakistan`, `Notion`, `Shopify`).
3. Enter your Tavily API Key.
4. PersonaPulse will crawl review snippets across Trustpilot, Reddit, G2, Capterra, and Sitejabber, vector-index them into ChromaDB, and simulate persona reactions grounded on live web sentiment.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
