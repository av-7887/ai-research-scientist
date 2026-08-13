"""
AI Research Scientist - Capstone Project
Full pipeline: 6 agents, chained with real handoffs (OpenAI Agents SDK + Gemini)

Pipeline flow:
Literature Review -> Research Gap Analysis -> Experiment Planning
-> Data Interpretation -> Citation Manager -> Scientific Writer -> saves final report

Setup before running:
1. pip install openai-agents requests
2. Paste your Gemini key below (from https://aistudio.google.com/apikey)
3. Run:  python main.py
"""

import os
import requests
from pydantic import BaseModel
from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool, set_tracing_disabled
from openai import AsyncOpenAI

# --- PASTE YOUR KEY HERE ---
GEMINI_API_KEY = "your_api_key"     # from https://aistudio.google.com/apikey
# ----------------------------

os.environ["OPENAI_API_KEY"] = "not-needed-but-required"  # SDK just checks this exists
set_tracing_disabled(True)  # stop SDK from trying to log traces to OpenAI's servers

# ---------------------------------------------------------
# Connect to Gemini using its OpenAI-compatible endpoint
# ---------------------------------------------------------
gemini_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

gemini_model = OpenAIChatCompletionsModel(
    model="gemini-3.5-flash-lite",  # correct current lite model name, higher free-tier limits
    openai_client=gemini_client,
)


# ===========================================================
# TOOLS  (5 total, spread across the agents below)
# ===========================================================

@function_tool
def search_arxiv(query: str) -> str:
    """Search arXiv.org for academic papers matching a query."""
    url = (
        "http://export.arxiv.org/api/query"
        f"?search_query=all:{query}&start=0&max_results=5"
    )
    response = requests.get(url, timeout=15)
    return response.text


@function_tool
def search_semantic_scholar(query: str) -> str:
    """Search Semantic Scholar for papers and their citation counts.
    Useful for judging how well-studied a topic already is."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": 5, "fields": "title,year,citationCount,abstract"}
    response = requests.get(url, params=params, timeout=15)
    return response.text


@function_tool
def analyze_data(numbers: list[float]) -> str:
    """Run basic statistical analysis (mean, min, max, std dev) on a list of numbers.
    Use this to interpret experiment results or simulated data."""
    if not numbers:
        return "No data provided."
    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = variance ** 0.5
    return (
        f"count={len(numbers)}, mean={mean:.3f}, "
        f"min={min(numbers)}, max={max(numbers)}, std_dev={std_dev:.3f}"
    )


@function_tool
def format_citation(title: str, author: str, year: str) -> str:
    """Look up a paper on CrossRef by title and return a formatted APA-style citation."""
    url = "https://api.crossref.org/works"
    params = {"query.bibliographic": title, "rows": 1}
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        item = data["message"]["items"][0]
        doi = item.get("DOI", "N/A")
        return f"{author} ({year}). {title}. DOI: {doi}"
    except Exception:
        return f"{author} ({year}). {title}. (DOI lookup failed)"


@function_tool
def save_report(content: str, filename: str = "final_report.md") -> str:
    """Save the final research report to a markdown file on disk.
    Pauses for human approval before writing anything - this is the
    project's Human Approval Gate."""
    print("\n" + "=" * 60)
    print("HUMAN APPROVAL REQUIRED")
    print("=" * 60)
    print(content[:1500])
    if len(content) > 1500:
        print(f"\n...[{len(content) - 1500} more characters not shown]...")
    print("=" * 60)
    choice = input("\nApprove saving this report to disk? (y/n): ").strip().lower()
    if choice != "y":
        return "Report was NOT saved - rejected by human reviewer."
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Report approved by human reviewer and saved to {filename}"


# ===========================================================
# STRUCTURED OUTPUT MODELS
# These force agents to return clean, predictable data shapes
# instead of loose free-form text - this is what your assignment
# calls "Structured outputs".
# ===========================================================

class Citation(BaseModel):
    author: str
    year: str
    title: str
    formatted: str  # the full formatted reference string


class CitationList(BaseModel):
    citations: list[Citation]


class ReportSummary(BaseModel):
    title: str
    sections_included: list[str]
    file_saved: bool
    filename: str


# ===========================================================
# AGENTS
# Defined in REVERSE order so each one can hand off to the
# next agent, which must already exist as a Python object.
# ===========================================================

# 6. Scientific Writer Agent  (final step - no handoff onward)
scientific_writer_agent = Agent(
    name="Scientific Writer Agent",
    instructions=(
        "You are a scientific writer. You will receive the full conversation "
        "history containing: a literature review, a research gap analysis, "
        "an experiment plan, a data interpretation, and formatted citations. "
        "Combine ALL of this into one polished, publication-style report with "
        "these sections: Introduction, Related Work, Proposed Experiment, "
        "Results & Discussion, References. "
        "IMPORTANT: your only available tool is save_report. "
        "Call save_report with the full report text to save it to disk. "
        "Then return a final structured summary of what you produced."
    ),
    tools=[save_report],
    output_type=ReportSummary,
    model=gemini_model,
)

# 5. Citation Manager Agent
citation_manager_agent = Agent(
    name="Citation Manager Agent",
    instructions=(
        "You are a citation formatting specialist. Look at the papers mentioned "
        "earlier in the conversation (from the literature review). For each one, "
        "call format_citation with its title, author, and year to get a properly "
        "formatted reference. List all formatted citations. "
        "IMPORTANT: your only available tool is format_citation. "
        "When finished, hand off to the Scientific Writer Agent."
    ),
    tools=[format_citation],
    handoffs=[scientific_writer_agent],
    model=gemini_model,
)

# 4. Data Interpretation Agent
data_interpretation_agent = Agent(
    name="Data Interpretation Agent",
    instructions=(
        "You are a data analyst. Based on the experiment plan described earlier "
        "in the conversation, invent a small set of plausible simulated result "
        "numbers (e.g. accuracy scores or measurements across 5-10 trials), then "
        "call analyze_data on them to get real statistics. Explain what the "
        "results would mean in plain language. "
        "IMPORTANT: your only available tool is analyze_data. "
        "When finished, hand off to the Citation Manager Agent."
    ),
    tools=[analyze_data],
    handoffs=[citation_manager_agent],
    model=gemini_model,
)

# 3. Experiment Planning Agent
experiment_planning_agent = Agent(
    name="Experiment Planning Agent",
    instructions=(
        "You are a research methodology expert. Based on the research gap "
        "identified earlier in the conversation, propose a concrete experiment "
        "or study design to address it: hypothesis, method, variables, and "
        "expected outcome. You have NO tools available - just reason and write. "
        "When finished, hand off to the Data Interpretation Agent."
    ),
    handoffs=[data_interpretation_agent],
    model=gemini_model,
)

# 2. Research Gap Analysis Agent
research_gap_agent = Agent(
    name="Research Gap Analysis Agent",
    instructions=(
        "You are a research strategist. Look at the literature review earlier "
        "in this conversation (do not search arXiv again - you don't have that "
        "tool). Use search_semantic_scholar to check how well-studied related "
        "angles are (citation counts are a good signal). "
        "Then identify 2-3 specific gaps or understudied questions in this area. "
        "IMPORTANT: your only available tool is search_semantic_scholar. "
        "When finished, hand off to the Experiment Planning Agent."
    ),
    tools=[search_semantic_scholar],
    handoffs=[experiment_planning_agent],
    model=gemini_model,
)

# 1. Literature Review Agent  (entry point of the pipeline)
lit_review_agent = Agent(
    name="Literature Review Agent",
    instructions=(
        "You are an academic literature review assistant. Use the search_arxiv "
        "tool to find recent relevant papers on the user's topic. Summarize each "
        "paper's title, authors, and key contribution. "
        "When finished, hand off to the Research Gap Analysis Agent."
    ),
    tools=[search_arxiv],
    handoffs=[research_gap_agent],
    model=gemini_model,
)


import time
from openai import RateLimitError


def run_with_retry(agent, input_text, max_retries=5, wait_seconds=45):
    """
    Runs the agent pipeline. If we hit a rate limit (free tier allows only
    a few requests per minute), wait and try again instead of crashing.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return Runner.run_sync(agent, input_text, max_turns=30)
        except RateLimitError:
            if attempt == max_retries:
                raise  # give up after max_retries and show the real error
            print(
                f"\nRate limit hit (attempt {attempt}/{max_retries}). "
                f"Waiting {wait_seconds}s before retrying...\n"
            )
            time.sleep(wait_seconds)


# ===========================================================
# RUN THE FULL PIPELINE
# ===========================================================
if __name__ == "__main__":
    topic = input("Enter a research topic to review: ")
    result = run_with_retry(lit_review_agent, topic)
    print("\n--- FINAL STRUCTURED OUTPUT ---\n")
    summary = result.final_output  # this is now a ReportSummary object, not plain text
    print(f"Title: {summary.title}")
    print(f"Sections included: {summary.sections_included}")
    print(f"File saved: {summary.file_saved}")
    print(f"Filename: {summary.filename}")