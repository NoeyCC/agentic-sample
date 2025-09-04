# Agentic Research & Brief Generator

A Python-based implementation of an agentic system that generates research briefs using three key design patterns:
1. **Routing** - Dynamically selects appropriate workers based on query intent
2. **Orchestrator-Worker** - Coordinates specialized workers to complete tasks
3. **Evaluator-Optimizer** - Ensures quality and completeness of generated briefs

## Features

- **Modular Architecture**: Clean separation of concerns with dedicated components for routing, orchestration, and evaluation
- **Parallel Processing**: Uses asyncio for efficient parallel execution of workers
- **Extensible Design**: Easy to add new workers and tools
- **Quality Assurance**: Built-in evaluation and optimization of generated content
- **Offline Capable**: Includes stub implementations for web search when offline

## Project Structure

```
agentic-sample/
├── app/
│   └── main.py              # FastAPI application and endpoints
├── core/
│   ├── types.py            # Core data types and models
│   └── patterns.md          # Documentation of design patterns
├── agents/
│   ├── orchestrator.py      # Main orchestrator implementation
│   ├── router.py            # Intent-based routing
│   └── evaluator.py         # Quality evaluation and optimization
├── workers/
│   ├── web_search.py       # Web search worker
│   ├── code_read.py        # Code analysis worker (stub)
│   └── data_query.py       # Data query worker (stub)
├── tools/
│   ├── web_search_tool.py  # Web search implementation
│   └── summarizer.py       # Text summarization utilities
└── tests/
    └── test_orchestrator.py # Unit tests
```

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Python package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/agentic-sample.git
   cd agentic-sample
   ```

2. Install dependencies using uv:
   ```bash
   uv pip install -e .
   ```

   For development, install with test dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

### Running the API

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## Usage

### Example API Request

```bash
curl -X 'POST' \
  'http://localhost:8000/run' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Summarize the latest trends in AI and include 3 reference links",
    "max_workers": 3,
    "timeout": 30
  }'
```

### Example Response

```json
{
  "success": true,
  "brief": {
    "title": "Brief: Summarize the latest trends in AI...",
    "content": "## Web Search\n\n### 1. Latest AI Trends 2024\n**URL:** https://example.com/ai-trends-2024\n**Snippet:** Overview of the latest trends in AI including generative AI, multimodal models, and AI ethics.\n\n### 2. AI Market Analysis\n**URL:** https://example.com/ai-market-analysis\n**Snippet:** Analysis of the current AI market trends and future predictions.",
    "references": [
      {
        "title": "AI Trends 2024",
        "url": "https://example.com/ai-trends-2024"
      },
      {
        "title": "AI Market Report",
        "url": "https://example.com/ai-market-analysis"
      }
    ],
    "generated_at": "2024-03-21T14:30:00Z"
  },
  "metadata": {
    "evaluation_score": 0.85,
    "is_complete": true,
    "worker_count": 2,
    "generated_at": "2024-03-21T14:30:01Z"
  }
}
```

## Design Patterns

### 1. Routing Pattern
- **Implementation**: `agents/router.py`
- **Purpose**: Analyzes the user's query to determine intent and selects appropriate workers
- **Key Features**:
  - Intent detection using regex patterns
  - Worker selection based on intent
  - Fallback to default workers when intent is unclear

### 2. Orchestrator-Worker Pattern
- **Implementation**: `agents/orchestrator.py` + `workers/`
- **Purpose**: Coordinates the execution of specialized workers
- **Key Features**:
  - Parallel execution of workers
  - Result aggregation
  - Error handling and retries

### 3. Evaluator-Optimizer Pattern
- **Implementation**: `agents/evaluator.py`
- **Purpose**: Ensures quality and completeness of generated briefs
- **Key Features**:
  - Quality scoring
  - Feedback generation
  - Automatic optimization suggestions

## Extending the System

### Adding a New Worker

1. Create a new worker class in the `workers/` directory
2. Implement the worker interface with a `process` method
3. Update the `WorkerType` enum in `core/types.py`
4. Register the worker in the `Orchestrator.__init__` method

### Adding a New Tool

1. Create a new tool class in the `tools/` directory
2. Implement the required functionality
3. Update the relevant workers to use the new tool

## Testing

Run the test suite:

```bash
uv pip install -e ".[dev]"
pytest -v
```

## Limitations

- Web search uses a stub implementation by default (no internet required)
- Limited number of worker types in the initial implementation
- Basic text summarization (can be enhanced with LLMs)

## Future Improvements

- Add more worker types (e.g., database queries, API integrations)
- Implement more sophisticated intent detection (e.g., using ML/NLP)
- Add support for different output formats (PDF, DOCX, etc.)
- Implement caching for frequently requested queries
- Add authentication and rate limiting

## License

MIT
