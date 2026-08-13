# AI Research Scientist — Project Documentation

## 1. Problem Analysis

### Business Context
Conducting a thorough research investigation — searching the existing literature,
identifying what hasn't been studied yet, designing an experiment, interpreting
results, and writing everything up with proper citations — is slow and highly
manual. Students, early-stage researchers, and R&D teams routinely spend many
hours on this process before they can even begin real experimentation. As the
volume of published research grows every year, keeping up manually becomes
increasingly impractical.

### Stakeholders
- **Students and early-career researchers** who need to produce literature
  reviews and research proposals as part of coursework or thesis work.
- **Academic researchers / R&D teams** who want to quickly scope out a new
  research direction before committing time to it.
- **Advisors and professors** who review and approve research proposals
  produced by their students.

### Problem Statement
There is no lightweight, automated system that can take a single research
topic and carry it through the full early-stage research workflow —
literature review, gap analysis, experiment design, data interpretation,
citation formatting, and report writing — while still keeping a human in
the loop for final approval before anything is finalized.

### Objectives
1. Automatically search and summarize relevant academic literature on a
   given topic.
2. Identify specific, under-studied research gaps grounded in real citation
   data rather than guesswork.
3. Propose a concrete, testable experiment design to address an identified
   gap.
4. Simulate and statistically interpret plausible experimental results.
5. Generate properly formatted, verifiable citations for all referenced work.
6. Compile all of the above into a single, publication-style report —
   without finalizing anything until a human reviewer explicitly approves it.

---

## 2. Multi-Agent Design

### Agent Architecture
The system uses a **linear handoff chain**: each agent completes its task
and then automatically hands off the full conversation (including everything
prior agents produced) to the next agent in the pipeline. This is a
sequential pipeline rather than a hub-and-spoke orchestrator, since each
stage of a research workflow naturally depends on the output of the stage
before it.

```
Research Topic Input
        |
Literature Review Agent        (tool: search_arxiv)
        |
Research Gap Analysis Agent    (tool: search_semantic_scholar)
        |
Experiment Planning Agent      (no tool - pure reasoning)
        |
Data Interpretation Agent      (tool: analyze_data)
        |
Citation Manager Agent         (tool: format_citation)
        |
Scientific Writer Agent        (tool: save_report + Human Approval Gate)
        |
Final Report (.md file)
```

### Roles of Each Agent
| Agent | Role |
|---|---|
| Literature Review Agent | Searches arXiv for relevant papers and summarizes each one's title, authors, and key contribution. |
| Research Gap Analysis Agent | Cross-checks related work via Semantic Scholar citation counts and identifies 2-3 specific under-studied questions. |
| Experiment Planning Agent | Proposes a concrete experiment (hypothesis, method, variables, expected outcome) to address the identified gap. |
| Data Interpretation Agent | Generates plausible simulated results and runs real statistical analysis (mean, std dev, etc.) on them. |
| Citation Manager Agent | Looks up and formats proper academic citations for every paper referenced earlier in the pipeline. |
| Scientific Writer Agent | Assembles everything into one polished report, and only saves it to disk after explicit human approval. |

### Agent Interaction and Handoff Flow
Each agent (except the last) is configured with `handoffs=[next_agent]`.
When an agent finishes its instructions, the OpenAI Agents SDK automatically
passes the entire conversation history to the next agent — meaning later
agents can see and build on everything earlier agents produced, without any
manual data-passing code. This satisfies both the **handoff** and the
**memory/context management** requirements of the project.

### Tool Integration Overview
| Tool | Used By | External API |
|---|---|---|
| `search_arxiv` | Literature Review Agent | arXiv.org public API |
| `search_semantic_scholar` | Research Gap Analysis Agent | Semantic Scholar Graph API |
| `analyze_data` | Data Interpretation Agent | (local Python computation) |
| `format_citation` | Citation Manager Agent | CrossRef API |
| `save_report` | Scientific Writer Agent | (local file write, gated by human approval) |

### Structured Outputs
The Scientific Writer Agent's final response is constrained to a
`ReportSummary` Pydantic model (`title`, `sections_included`, `file_saved`,
`filename`) rather than free-form text, ensuring the pipeline's final result
is predictable and machine-readable.

### Human Approval
Before the final report is written to disk, `save_report` prints a preview
of the full report and requires the user to explicitly type `y` to approve.
If rejected, nothing is saved. This is the project's Human Approval Gate.
