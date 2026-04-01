# PaperOrchestrator

> An LLM-orchestrated multi-agent pipeline for automated end-to-end scientific paper writing.

<p align="center">
  <img src="figure/1.jpg" alt="PaperOrchestrator overview" width="100%">
</p>

<p align="center">
  <img src="figure/2.jpg" alt="PaperOrchestrator pipeline architecture" width="78%">
</p>

## Overview

**PaperOrchestrator** is a structured academic writing system that turns research materials into a paper draft, a LaTeX manuscript, and a BibTeX reference file.

Instead of relying on a single long-form generation call, the system decomposes paper writing into a controlled multi-stage pipeline with shared context, section-wise generation, length control, consistency polishing, BibTeX drafting, robust section-by-section LaTeX conversion, and journal-template rendering.

The current implementation supports:

- **Gradio-based interactive UI**
- **English and Chinese output**
- **Section-by-section academic paper generation**
- **Best-effort continuation for truncated model outputs**
- **Length control for major sections**
- **Figure/image injection into LaTeX**
- **BibTeX draft generation**
- **Journal LaTeX template ZIP rendering**
- **Export of `paper.md`, `main.tex`, `refs.bib`, and figures as a ZIP bundle**

## Highlights

- **Structured pipeline instead of single-turn generation**
- **Shared state management with `PaperContext`**
- **Continue mechanism for long outputs**
- **Length guard for section balance**
- **Full-paper polishing for consistency**
- **Section-by-section robust LaTeX generation**
- **Template-aware journal rendering**
- **Gradio UI for end-to-end usage**

## Repository Structure

```text
paper-orchestrator/
├── app/
│   └── gradio_app.py
├── core/
│   ├── __init__.py
│   ├── agent.py
│   ├── biblio.py
│   ├── checker.py
│   ├── config.py
│   ├── context.py
│   ├── exporter.py
│   ├── latex.py
│   ├── pipeline.py
│   └── templates/
│       ├── loader.py
│       └── renderer.py
├── figure/
│   ├── 1.jpg
│   ├── 2.jpg
│   ├── 3.jpg
│   ├── 4.jpg
│   ├── 5.jpg
│   └── 6.jpg
├── llm/
│   ├── anthropic_client.py
│   └── prompts.py
├── tools/
│   └── export_requirements.py
└── README.md
