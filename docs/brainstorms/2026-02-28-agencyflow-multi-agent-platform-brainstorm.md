---
topic: AgencyFlow - Multi-Agent Campaign Automation Platform
date: 2026-02-28
status: active
---

# AgencyFlow — Multi-Agent Campaign Automation Platform

## What We're Building

A multi-agent AI platform that automates repetitive agency workflows for marketing/advertising agencies like Ayzenberg Group. The platform features specialized AI agents — each handling a different part of the campaign lifecycle — orchestrated through a central dashboard.

**Target user:** Marketing agency teams who spend hours on campaign setup, audience research, content calendars, reporting, and brief writing.

**Core agents:**
- **Brief Parser Agent** — Ingests client briefs (PDFs, docs, emails) and extracts structured data: objectives, audience, budget, timelines, KPIs
- **Audience Research Agent** — Takes parsed brief data and generates audience insights, persona summaries, and targeting recommendations
- **Content Calendar Agent** — Generates a content/posting calendar based on campaign goals, audience insights, and channel strategy
- **Performance Reporter Agent** — Takes campaign metrics and produces executive-ready reports with insights and recommendations
- **Creative Brief Generator Agent** — Synthesizes all inputs into a structured creative brief for the creative team

## Why This Approach

- **Directly relevant to Ayzenberg:** They are a social-first brand acceleration agency. Every campaign they run goes through these exact workflows. Showing automation of their daily work demonstrates deep understanding of the business.
- **Complements Soulmates.ai:** Soulmates.ai handles audience testing and digital twins. AgencyFlow handles the upstream workflow — getting from client request to campaign-ready assets. They're complementary, not competing.
- **Multi-agent architecture:** Demonstrates AI engineering skills (agent orchestration, pipeline design, prompt engineering) — exactly what an AI engineer role requires.
- **Practical and demo-able:** Each agent produces tangible, visible output. Easy to demo in a meeting.

## Key Decisions

1. **Tech stack: Python (FastAPI) + React frontend**
   - Python for AI/agent logic — standard for AI engineering roles, best LLM library ecosystem
   - FastAPI for the API layer — modern, fast, auto-docs
   - React for the dashboard — polished UI for demos
   - Rationale: Shows full-stack AI engineering capability. Python is what Ayzenberg would expect from an AI engineer.

2. **AI backend: Google Gemini free tier**
   - Zero cost — generous free tier (15 RPM, 1M tokens/day)
   - Sufficient for demo and development
   - Architecture will be model-agnostic (easy to swap to OpenAI/Anthropic later)
   - Rationale: Cost-efficient development without compromising capability.

3. **Agent orchestration: Custom pipeline with clear interfaces**
   - Each agent is a self-contained module with defined inputs/outputs
   - Agents can run independently or in sequence (brief → audience → calendar → creative brief)
   - Central orchestrator manages the pipeline
   - Rationale: Shows architectural thinking. Clean separation makes it demo-friendly and extensible.

4. **Scope: 5 agents, 1 dashboard, 1 pipeline**
   - Focus on breadth (multiple agents) over depth (one perfect agent)
   - Each agent should produce useful output within its scope
   - Dashboard ties everything together visually
   - Rationale: Multi-agent platform shows more engineering skill than a single deep tool.

5. **Tailored to Ayzenberg's world**
   - Use marketing/agency terminology throughout (briefs, campaigns, flights, placements, KPIs)
   - Design workflows that mirror real agency processes
   - Reference concepts from Soulmates.ai where relevant (audience fidelity, digital twins)
   - Rationale: The goal is for them to think "he understands our business"

## Resolved Questions

1. **Auth system?** No — keep it open, demo-friendly. No login screen, opens straight to dashboard.
2. **Agent communication pattern?** Direct API calls (simple function-call pipeline). No message queue. Clean, debuggable, right-sized. Can explain queue upgrade path if asked about scaling.
3. **Deployment?** Local demo only. Run on laptop during meetings. No hosting costs or deployment complexity.

## Scope Boundaries

**In scope:**
- 5 AI agents with clear inputs/outputs
- React dashboard to visualize agent outputs and trigger workflows
- FastAPI backend with agent orchestration
- Sample data / demo mode with pre-loaded campaign examples
- Clean README and project documentation

**Out of scope (YAGNI):**
- User authentication / multi-tenancy
- Real integrations with ad platforms (Meta Ads, Google Ads)
- Payment / billing
- Production-grade error handling
- Mobile responsiveness (desktop demo is fine)

## Success Criteria

- Can demo the full pipeline: upload brief → parse → research audience → generate calendar → produce creative brief → generate report
- Each agent produces professional, agency-quality output
- Dashboard looks polished enough for a meeting demo
- Codebase demonstrates AI engineering best practices (clean architecture, typed interfaces, tests)
- Built using compound engineering workflow (brainstorm → plan → work → review → compound) to demonstrate mastery of the tooling
