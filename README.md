# Financial News Knowledge Graph (Relatiq AI)

Relatiq AI is a powerful tool designed to analyze financial news by constructing a Knowledge Graph. It leverages advanced AI and graph database technologies to extract entities, relationships, and insights from unstructured text, enabling users to visualize connections, track timelines, and perform deep analysis of companies and market trends.

## Key Features

### 1. Article Selection & Filtering
- **Dedicated Landing View**: Start by browsing and selecting relevant articles from a rich grid view.
- **Smart Filters**: Filter news by **Date Range**, **Publisher Tier** (A, B, C), **News Status** (Confirmed, Speculation, Analysis), **Sector**, and **Entity**.
- **News Cards**: Quickly assess article importance with visual badges for Tier and Status.

### 2. Knowledge Graph Visualization
- **Interactive Network**: Visualize connections between Companies, Persons, Products, and Sectors.
- **Dynamic Graph Filters**: Filter the graph by Sector and Entity to focus on specific market segments.
- **Reading Mode**: A focused mode to read article content alongside the graph context.

### 3. AI-Powered Analysis
- **Sentiment Analysis**: Automatically extracts and aggregates sentiment (Positive, Neutral, Negative) for companies mentioned in the news.
- **Publisher Tiering**: Automatically categorizes news sources into Tiers (A: Major Global, B: Tech/Business, C: General) for credibility assessment.
- **News Status Classification**: Distinguishes between "Confirmed News", "Speculation", and "Analysis/Outlook".
- **Agentic Insights**: Ask natural language questions to the AI Agent to query the knowledge graph (e.g., "What companies are investing in AI?").

### 4. Company Deep Dive
- **Sentiment Cards**: View aggregated sentiment distribution for specific companies.
- **Connection Analysis**: Explore paths and relationships between any two entities.

## Tech Stack

- **Backend**: Python, FastAPI, LangChain
- **Frontend**: Next.js, React, Tailwind CSS
- **Database**: Neo4j (Graph Database)
- **AI/LLM**: Google Gemini (via `google-genai` and `langchain-google-genai`)
- **Visualization**: `react-force-graph-2d`

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python** (>= 3.12)
- **Node.js** (>= 20)
- **Neo4j Database** (Local or AuraDB)
- **Google Gemini API Key**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/iristap/Relatiq-AI.git
cd Relatiq-AI
```

### 2. Backend Setup

It is recommended to use `uv` or `venv` for Python environment management.

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the root directory and add your configuration:

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
GOOGLE_API_KEY=your_gemini_api_key
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Usage

### Running the API Server

The FastAPI backend serves the data to the frontend.

```bash
# From the root directory
uvicorn src.api.main:app --reload --port 8000
```

### Running the Frontend Application

```bash
# From the frontend directory
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Ingesting Data

To populate the graph with new data:

```bash
python src/ingest.py
```

## Project Structure

```
mind-ai/
├── frontend/           # Next.js Frontend application
├── src/
│   ├── api/            # FastAPI backend routes and logic
│   ├── ingest.py       # Data ingestion script (Metadata, Graph, Sentiment)
│   ├── graph_db.py     # Neo4j database connection handler
│   └── ...
├── data/               # Data storage
├── pyproject.toml      # Python project configuration
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```