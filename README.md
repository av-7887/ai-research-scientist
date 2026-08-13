# AI Research Scientist

A multi-agent research assistant built with the **OpenAI Agents SDK**
(powered by **Google Gemini**). Given a single research topic, it
autonomously performs a literature review, identifies research gaps,
proposes an experiment, interprets simulated results, formats citations,
and compiles everything into a publication-style report — with a human
approval step before anything is finalized.

## Architecture

```
Research Topic Input
        |
Literature Review Agent        (arXiv)
        |
Research Gap Analysis Agent    (Semantic Scholar)
        |
Experiment Planning Agent
        |
Data Interpretation Agent      (statistical analysis)
        |
Citation Manager Agent         (CrossRef)
        |
Scientific Writer Agent        (Human Approval Gate) -> final_report.md
```

See `PROJECT_DOCUMENTATION.md` for full problem analysis and design details.

## Features
- 6 specialized agents chained via real SDK handoffs
- 5 external tools/APIs (arXiv, Semantic Scholar, CrossRef, stats analysis, file save)
- Shared memory/context automatically passed through the handoff chain
- Structured output (Pydantic model) for the final report summary
- Human-in-the-loop approval gate before saving the final report
- Automatic retry with backoff on API rate limits

## Setup

1. Install dependencies:
   ```
   pip install openai-agents requests pydantic
   ```
2. Get a free Gemini API key: https://aistudio.google.com/apikey
3. Open `main.py` and paste your key into the `GEMINI_API_KEY` variable
   near the top of the file.
   > Note: for a real deployment, use an environment variable instead of
   > hardcoding the key — never commit real API keys to a public repo.

## Usage

```
python main.py
```

You'll be prompted for a research topic. The pipeline will run through all
six agents, then show you a preview of the final report and ask for your
approval before saving it to `final_report.md`.

## Tech Stack
- Python
- OpenAI Agents SDK
- Google Gemini API (via OpenAI-compatible endpoint)
- arXiv API, Semantic Scholar API, CrossRef API

## Project Status
Capstone project for Summer School '26 — OpenAI Agents SDK track.
# ai-research-scientist
# ai-research-scientist
