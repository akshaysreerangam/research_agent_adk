# agents/worker_agents.py
import json
import re
from typing import List, Dict, Any

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from tools.search_tool import google_search_tool
from tools.fetch_tool import fetch_url
async def extract_final_text(events: List[Any]) -> str:
    """
    Extract the final response text from the list of events.
    Accumulates text from content parts and returns text from the final response event.
    """
    full_text = ""
    final_text = ""
    for event in events:
        content = getattr(event, 'content', None)
        parts = getattr(content, 'parts', None) if content is not None else None
        if parts:
            # parts may be a list-like; concatenate any text fields found
            for part in parts:
                text = getattr(part, 'text', None)
                if text:
                    full_text += text
        if hasattr(event, 'is_final_response') and event.is_final_response():
            final_text = full_text
            break
    return final_text.strip() or full_text.strip()

class BaseAgent:
    def __init__(self, name: str, model: str, instruction: str, tools: List[Any]):
        self.agent = Agent(
            name=name,
            model=model,
            instruction=instruction,
            tools=tools,
        )
        self.runner = InMemoryRunner(app_name=f"{name}_app", agent=self.agent)

    async def _run(self, message: str, user_id: str = "user_1") -> str:
        session = await self.runner.session_service.create_session(
            user_id=user_id,
            app_name=f"{self.agent.name}_app"
        )
        session_id = session.id

        events = []
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=Content(parts=[Part(text=message)])
        ):
            events.append(event)

        return await extract_final_text(events)

class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="search_agent",
            model="gemini-2.5-flash-lite",
            instruction="""You are a search agent. For the given query, call the google_search tool to get the top 3 relevant web results. 
            After receiving the results, respond ONLY with a valid JSON array of the top 3 results, formatted as:
            [
                {"title": "page title", "link": "url", "snippet": "brief description"}
            ]
            Do not include any additional text outside the JSON.""",
            tools=[google_search_tool],
        )

    async def run(self, query: str, user_id: str = "user_1") -> List[Dict[str, str]]:
        message = f"Search for: {query}"
        text = await self._run(message, user_id)
        # Debug: show raw agent output so we can see why links may be missing
        print("[SearchAgent] raw response:", text)
        if not text:
            return []
        try:
            results = json.loads(text)
            if isinstance(results, list):
                parsed = []
                for r in results:
                    if not isinstance(r, dict):
                        continue
                    # If link missing, try to find an URL inside any string fields
                    if 'link' not in r or not r.get('link'):
                        combined = ' '.join([str(v) for v in r.values() if isinstance(v, str)])
                        m = re.search(r"https?://\S+", combined)
                        if m:
                            r['link'] = m.group(0).rstrip('.,')
                    parsed.append(r)
                # Return only items that have link (or keep those without link if needed)
                return [r for r in parsed if isinstance(r, dict) and 'link' in r]
        except json.JSONDecodeError:
            # Not JSON — try to extract URLs from the raw text as a fallback
            pass
        # Fallback parsing: look for URLs in the raw text and return as single result
        urls = re.findall(r"https?://\S+", text)
        if urls:
            url = urls[0].rstrip('.,')
            return [{"title": query, "link": url, "snippet": text[:200]}]
        return [{"title": query, "link": None, "snippet": (text or '')[:200]}]

class FetchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="fetch_agent",
            model="gemini-2.5-flash-lite",
            instruction="""You are a fetch agent. Given a URL, call the fetch_url tool to retrieve the full text content of the webpage. 
            After fetching, respond ONLY with the entire fetched text content. Do not summarize or add commentary.""",
            tools=[fetch_url],
        )

    async def run(self, url: str, user_id: str = "user_1") -> str:
        message = f"Fetch the content from this URL: {url}"
        return await self._run(message, user_id) or f"Failed to fetch content from {url}"

class SummarizerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="summarizer_agent",
            model="gemini-2.5-flash-lite",
            instruction="""You are a summarizer agent. Summarize the provided webpage content (which may be long) into 3-5 concise bullet points. 
            Focus on key facts, insights, main arguments, and relevance to the topic of data science in healthcare or similar. 
            Output only the bullet points, no introduction.""",
            tools=[],  # No tools needed
        )

    async def run(self, text: str, user_id: str = "user_1") -> str:
        # Truncate if too long for model
        if len(text) > 10000:
            text = text[:10000] + "\n... (content truncated)"
        message = f"Summarize this content:\n\n{text}"
        return await self._run(message, user_id) or "Unable to summarize the content."

class ComparisonAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="comparison_agent",
            model="gemini-2.5-flash-lite",
            instruction="""You are a comparison agent. Given summaries from multiple sources, create a markdown table comparing them.
            Columns: | Source | Summary | Pros | Cons |
            For each source, briefly extract 1-2 pros and cons based on the summary's content, focusing on strengths/weaknesses in approach, insights, or applicability.
            If only one source, still create the table. Output only the markdown table.""",
            tools=[],  # No tools needed
        )

    async def run(self, input_text: str, user_id: str = "user_1") -> str:
        return await self._run(input_text, user_id) or "| Source | Summary | Pros | Cons |\n|--------|---------|------|------|\n| None | No data | N/A | N/A |"