# Research_agent_adk
This a POC project personal research assistant implemented as a small multi-agent pipeline

# Personal Research Assistant (ADK POC)

This is a personal research assistant built as a **multi-agent orchestration** pipeline using Google ADK. It automates research workflows by searching, fetching, summarizing, and comparing web content.

## Architecture

**ResearchOrchestrator** orchestrates four specialized agents:
- **SearchAgent** - Queries Google Search API and returns top results as JSON
- **FetchAgent** - Extracts full-text content from URLs
- **SummarizerAgent** - Generates 3-5 bullet-point summaries of content
- **ComparisonAgent** - Creates markdown comparison tables of multiple sources

## Key Features

- **Multi-agent pipeline**: Sequential + parallel agent execution with asyncio
- **Tools integration**: Google Search, webpage fetching, LLM inference
- **Session management**: InMemoryRunner with session persistence
- **Observability**: Detailed timing metrics and structured logging per operation
- **Modular design**: BaseAgent abstraction with pluggable tools
- **Graceful fallbacks**: Direct fetch fallback if agent fetch fails

## Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv reserv_env
   reserv_env\Scripts\activate  # Windows
   # or: source reserv_env/bin/activate  # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirments.txt
   ```

3. Configure environment variables:
   - Create `.env` file with `GOOGLE_API_KEY` (for Google Search API)

## Usage

Run the research workflow:
```bash
python main.py
```

When prompted, enter a research topic (e.g., "agentic AI", "machine learning in healthcare"):

```
Enter topic: agentic AI
```

The orchestrator will:
1. Search for the topic and retrieve 3 top results
2. Fetch full-text content from each URL
3. Generate bullet-point summaries
4. Create a comparison table with pros/cons
5. Output formatted results to console

## Project Structure

```
├── main.py                      # Entry point
├── adk_client.py               # ADK LLM client stub (TODO: integrate)
├── my_agents/
│   ├── research_agent.py        # ResearchOrchestrator
│   └── worker_agents.py         # SearchAgent, FetchAgent, SummarizerAgent, ComparisonAgent
├── tools/
│   ├── search_tool.py           # Google Search tool
│   └── fetch_tool.py            # URL content fetching
├── session/
│   └── in_memory_session.py     # Session management
├── observability/
│   └── logging_metrics.py       # Metrics and structured logging
└── requirments.txt              # Dependencies
```

## Dependencies

- `google-adk` - Agent framework with runners and tools
- `requests` & `beautifulsoup4` - Web scraping and content extraction
- `readability-lxml` - Article text extraction
- `python-dotenv` - Environment configuration
- `pandas` - Data processing (utilities)

## Development Notes

- **adk_client.py** is a stub; integrate real ADK LLM client as needed
- **InMemoryRunner** persists sessions within a single process
- **MetricsLogger** tracks operation timing for observability
- All agents use `gemini-2.5-flash-lite` model by default
- Summaries truncated to 10K tokens before agent processing
