# main.py
from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
from my_agents.research_agent import ResearchOrchestrator

# Sanity check: key loaded
print("GOOGLE_API_KEY loaded:", bool(os.getenv("GOOGLE_API_KEY")))

if __name__ == "__main__":
    topic = input("Enter topic: ").strip() or "agentic AI"
    orchestrator = ResearchOrchestrator()
    asyncio.run(orchestrator.run_research(topic))