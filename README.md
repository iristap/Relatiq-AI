# Financial News Knowledge Graph (Relatiq AI)

Relatiq AI is a powerful tool designed to analyze financial news by constructing a Knowledge Graph. It leverages advanced AI and graph database technologies to extract entities, relationships, and insights from unstructured text, enabling users to visualize connections, track timelines, and perform deep analysis of companies and market trends.

## Key Features

- **Graph Visualization**: Interactive network visualization of companies, persons, and topics, showing how they are connected through news articles.
- **Timeline View**: A chronological display of news articles to track events over time.
- **Company Analysis**: Deep dive into specific companies to see their connections, mentioned articles, and relationship paths to other entities.
- **Advanced Search**: Search for specific entities and filter by node/relationship types.
- **Data Ingestion**: Automated pipeline to ingest news articles and build the knowledge graph using LLMs.

## Tech Stack

- **Backend**: Python, FastAPI, LangChain
- **Frontend**: Next.js, React, Tailwind CSS, Streamlit (for rapid prototyping/dashboard)
- **Database**: Neo4j (Graph Database)
- **AI/LLM**: Google Gemini (via `google-genai` and `langchain-google-genai`)
- **Visualization**: `react-force-graph-2d` (Frontend), `streamlit-agraph` (Streamlit)

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python** (>= 3.12)
- **Node.js** (>= 20)
- **Neo4j Database** (Local or AuraDB)
- **Google Gemini API Key**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/iristap/mind-ai.git
cd mind-ai
```

### 2. Backend Setup

It is recommended to use `uv` or `venv` for Python environment management.

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# OR if using uv/hatch
uv sync
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

### Running the Streamlit Dashboard

For a quick view of the data and graph capabilities:

```bash
streamlit run src/app.py
```

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
│   ├── app.py          # Streamlit dashboard application
│   ├── ingest.py       # Data ingestion script
│   ├── graph_db.py     # Neo4j database connection handler
│   └── ...
├── data/               # Data storage (if applicable)
├── pyproject.toml      # Python project configuration
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```