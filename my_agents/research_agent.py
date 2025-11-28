# agents/research_agent.py
import asyncio
import time
from typing import List, Dict

from .worker_agents import SearchAgent, FetchAgent, SummarizerAgent, ComparisonAgent
from tools.fetch_tool import fetch_url  # Fallback if agent fetch fails
from observability.logging_metrics import MetricsLogger

class ResearchOrchestrator:
    def __init__(self):
        self.search_agent = SearchAgent()
        self.fetch_agent = FetchAgent()
        self.summarizer_agent = SummarizerAgent()
        self.comparison_agent = ComparisonAgent()
        self.logger = MetricsLogger("ResearchOrchestrator")

    async def run_research(self, topic: str, max_results: int = 3) -> str:
        start_time = time.time()
        self.logger.log(f">>> Running research for: {topic}")

        user_id = "user_1"

        # 1) Run the search agent
        self.logger.log("Running search_agent...")
        search_start = time.time()
        search_results = await self.search_agent.run(topic, user_id)
        search_duration = time.time() - search_start
        self.logger.log(f"Search completed in {search_duration:.2f}s. Extracted {len(search_results)} search result(s).")

        if not search_results:
            self.logger.log("No search results found.")
            return "No search results could be retrieved for the topic."

        # 2) Fetch and summarize each result
        summaries: List[Dict[str, str]] = []
        for i, item in enumerate(search_results[:max_results]):
            link = item.get("link")
            if not link:
                self.logger.log(f"  No link for item {i+1}, skipping.")
                continue

            self.logger.log(f"  Processing item {i+1} (source={link})...")

            # Run fetch agent
            fetch_start = time.time()
            content = await self.fetch_agent.run(link, user_id)
            fetch_duration = time.time() - fetch_start
            self.logger.log(f"  Fetch took {fetch_duration:.2f}s")

            if "Failed to fetch" in content or not content.strip():
                self.logger.log(f"  Fetch failed, falling back to direct fetch.")
                content = fetch_url(link)  # Fallback to direct function

            # Summarize
            sum_start = time.time()
            summary_text = await self.summarizer_agent.run(content, user_id)
            sum_duration = time.time() - sum_start
            self.logger.log(f"  Summarization took {sum_duration:.2f}s")
            summaries.append({"source": link, "summary": summary_text})

        if not summaries:
            self.logger.log("No summaries generated.")
            return "No valid sources to compare."

        # 3) Compare
        self.logger.log("Creating comparison table...")
        compare_start = time.time()
        compare_input = "Compare these sources:\n\n"
        for s in summaries:
            compare_input += f"Source: {s['source']}\nSummary: {s['summary']}\n\n"

        comp_text = await self.comparison_agent.run(compare_input, user_id)
        compare_duration = time.time() - compare_start
        self.logger.log(f"Comparison took {compare_duration:.2f}s")

        total_duration = time.time() - start_time
        self.logger.log(f"Total research completed in {total_duration:.2f}s")

        # Pretty-print results in a human-friendly layout per user request
        def _parse_table_row_for_source(table_text: str, source: str):
            # Find a markdown table row that contains the source URL
            if not table_text:
                return None
            lines = [ln.strip() for ln in table_text.splitlines() if ln.strip()]
            for ln in lines:
                if ln.startswith("|") and source in ln:
                    # Split into columns ignoring leading/trailing pipe
                    cols = [c.strip() for c in ln.strip().strip("|").split("|")]
                    # Expecting: Source, Summary, Pros, Cons
                    if len(cols) >= 4:
                        return {
                            "source": cols[0],
                            "summary": cols[1],
                            "pros": cols[2].replace("<br>", "\n"),
                            "cons": cols[3].replace("<br>", "\n"),
                        }
            return None

        def _pretty_print(summaries_list, table_text):
            out_lines = []
            for s in summaries_list:
                src = s.get("source") or "Unknown source"
                parsed = _parse_table_row_for_source(table_text, src)
                out_lines.append(f"Source: {src}")
                # Summary from parsed table if present, otherwise from summaries_list
                if parsed and parsed.get("summary"):
                    out_lines.append(f"Summary: {parsed.get('summary')}")
                else:
                    out_lines.append(f"Summary: {s.get('summary')[:1000] if s.get('summary') else 'N/A'}")
                if parsed:
                    out_lines.append(f"Pros: {parsed.get('pros') or 'N/A'}")
                    out_lines.append(f"Cons: {parsed.get('cons') or 'N/A'}")
                else:
                    out_lines.append("Pros: N/A")
                    out_lines.append("Cons: N/A")
                out_lines.append("-" * 60)
            return "\n".join(out_lines)

        pretty = _pretty_print(summaries, comp_text)

        print("\n=== Formatted Results ===\n")
        print(pretty)
        print("\n=== End ===\n")

        return pretty