# Compound Engineering Plugin - Complete Reference Guide

> **Version:** 2.35.2 | **Author:** Kieran Klaassen (Every, Inc.) | **License:** MIT
>
> *"Each unit of engineering work should make subsequent units of work easier — not harder."*

---

## Table of Contents

1. [Philosophy & Core Idea](#1-philosophy--core-idea)
2. [The Master Workflow Loop](#2-the-master-workflow-loop)
3. [Workflow Commands (The Big 5)](#3-workflow-commands-the-big-5)
4. [Power Commands](#4-power-commands)
5. [All 29 Agents — Detailed](#5-all-29-agents--detailed)
6. [All 19 Skills — Detailed](#6-all-19-skills--detailed)
7. [MCP Server: Context7](#7-mcp-server-context7)
8. [Configuration & Setup](#8-configuration--setup)
9. [Recipes: Common Task Patterns](#9-recipes-common-task-patterns)
10. [Automation Playbook](#10-automation-playbook)
11. [Cheat Sheet](#11-cheat-sheet)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Philosophy & Core Idea

Compound Engineering is built on one principle: **knowledge compounds**. Every problem you solve and document makes the next problem faster. Every review agent that catches an issue prevents the same class of bug from ever reaching production again.

The plugin gives you:
- **Structured workflows** so you never forget a step
- **Specialized agents** that review code from 15+ different angles simultaneously
- **Institutional memory** through documented solutions that are automatically searched in future work
- **Parallel execution** so reviews, research, and work happen concurrently

**The compounding loop:**
```
Build → Test → Find Issue → Research → Improve → Document → Validate → Deploy
  ^                                                                        |
  └────────────────────────────────────────────────────────────────────────┘
```

First time solving "N+1 query in briefs" = 30 min research. Document it = 5 min. Next occurrence = 2 min lookup. Knowledge compounds.

---

## 2. The Master Workflow Loop

This is the golden path. Learn this flow and you'll use the plugin to its full potential:

```
/workflows:brainstorm  →  /workflows:plan  →  /workflows:work  →  /workflows:review  →  /workflows:compound
      (WHAT)                  (HOW)              (BUILD)             (VERIFY)              (REMEMBER)
```

### When to use each step:

| Step | When to Use | When to Skip |
|------|-------------|--------------|
| **brainstorm** | Unclear requirements, multiple approaches, exploring ideas | Requirements already crystal clear |
| **plan** | Any non-trivial feature, bug fix, or refactor | Single-line fix, obvious change |
| **work** | Executing any plan or spec | Already built it manually |
| **review** | Before merging any PR | Trivial typo fix |
| **compound** | After solving any non-trivial problem | Simple typo or obvious error |

### Shortcut: Full Autonomous Mode

If you want the entire loop automated end-to-end:

```
/lfg [feature description]     # Sequential: plan → deepen → work → review → resolve → test → video
/slfg [feature description]    # Same but with parallel swarm agents for max speed
```

---

## 3. Workflow Commands (The Big 5)

### 3.1 `/workflows:brainstorm`

**Purpose:** Answer WHAT to build through collaborative dialogue. Precedes planning.

**What it does:**
1. **Phase 0 — Assess clarity:** If requirements are already clear, offers to skip straight to planning
2. **Phase 1 — Understand the idea:** Runs lightweight repo research, then asks questions one at a time using multiple choice when possible
3. **Phase 2 — Explore approaches:** Proposes 2-3 concrete approaches with pros/cons, recommends one, applies YAGNI
4. **Phase 3 — Capture design:** Writes brainstorm doc to `docs/brainstorms/YYYY-MM-DD-<topic>-brainstorm.md`
5. **Phase 4 — Handoff:** Offers to refine, proceed to planning, ask more questions, or stop

**Output:** `docs/brainstorms/YYYY-MM-DD-<topic>-brainstorm.md`

**Key rule:** NEVER codes. Only explores and documents decisions.

**Usage:**
```
/workflows:brainstorm Add user authentication with social login
/workflows:brainstorm Our checkout flow is too slow
/workflows:brainstorm                                          # Will ask what to explore
```

---

### 3.2 `/workflows:plan`

**Purpose:** Transform a feature description into a structured, actionable plan.

**What it does:**
1. **Step 0 — Idea Refinement:** Checks for existing brainstorm docs in `docs/brainstorms/`. If found, uses it as the foundation and skips questions. If not, refines the idea through Q&A.
2. **Step 1 — Local Research (Parallel):** Runs `repo-research-analyst` + `learnings-researcher` to find existing patterns and past solutions
3. **Step 1.5 — Research Decision:** Decides if external research is needed based on risk level. Security/payments = always research. Strong local patterns = skip.
4. **Step 1.5b — External Research (Conditional):** Runs `best-practices-researcher` + `framework-docs-researcher` in parallel
5. **Step 2 — Issue Planning:** Drafts title, categorization, stakeholder analysis
6. **Step 3 — SpecFlow Analysis:** Runs `spec-flow-analyzer` to find gaps and edge cases
7. **Step 4 — Choose Detail Level:**
   - **MINIMAL** — Problem statement + acceptance criteria + context (simple bugs, small changes)
   - **MORE** — Adds background, technical considerations, system-wide impact, success metrics (most features)
   - **A LOT** — Adds implementation phases, alternatives considered, risk analysis, resource needs (major features, architecture changes)
8. **Step 5 — Write plan** to `docs/plans/YYYY-MM-DD-<type>-<name>-plan.md`
9. **Post-generation options:** Open in editor, deepen plan, technical review, start work, create GitHub/Linear issue

**Output:** `docs/plans/YYYY-MM-DD-feat-user-authentication-flow-plan.md`

**Key rule:** NEVER codes. Just researches and writes the plan.

**Plan frontmatter:**
```yaml
---
title: feat: Add User Authentication
type: feat|fix|refactor
status: active           # Changed to "completed" when work finishes
date: 2026-02-28
origin: docs/brainstorms/2026-02-28-auth-brainstorm.md  # If originated from brainstorm
---
```

**Usage:**
```
/workflows:plan Add real-time notifications using WebSockets
/workflows:plan docs/brainstorms/2026-02-28-notifications-brainstorm.md
/workflows:plan Fix race condition in checkout when two tabs submit simultaneously
```

---

### 3.3 `/workflows:work`

**Purpose:** Execute a plan efficiently. The "do the actual building" command.

**What it does:**

#### Phase 1: Quick Start
1. Read plan completely, ask clarifying questions
2. Set up environment: create feature branch, worktree, or continue on current branch
3. Break plan into TodoWrite tasks with dependencies

#### Phase 2: Execute
1. **Task execution loop** for each task:
   - Mark as in_progress
   - Read referenced files from plan
   - Look for similar patterns in codebase
   - Implement following existing conventions
   - Write tests
   - **Run System-Wide Test Check** (5 questions):
     - What callbacks/middleware fire when this runs?
     - Do my tests exercise the real chain (not just mocked isolation)?
     - Can failure leave orphaned state?
     - What other interfaces expose this same behavior?
     - Do error strategies align across layers?
   - Run tests after changes
   - Mark task completed + check off in plan file (`[ ]` → `[x]`)
   - Create incremental commit if logical unit is complete

2. **Incremental commits** — Commit when a logical unit is complete and tests pass. Never commit WIP or failing tests.

3. **Follow existing patterns** — Read referenced files first, match naming, reuse components

4. **Test continuously** — Don't wait until the end

#### Phase 3: Quality Check
1. Run full test suite + linting
2. Optionally run configured review agents (from `compound-engineering.local.md`)
3. Final validation: all tasks done, tests pass, lint passes, patterns followed
4. **Prepare Post-Deploy Monitoring & Validation plan** (required for every PR)

#### Phase 4: Ship It
1. Create commit with conventional format + attribution
2. Capture screenshots for UI changes (using agent-browser)
3. Create PR with summary, testing notes, monitoring plan, screenshots, badge
4. Update plan status from `active` to `completed`

**Optional: Swarm Mode** — For plans with 5+ independent tasks, enable swarm mode to launch parallel agents:
```
"Use swarm mode for this work"
```

**Usage:**
```
/workflows:work docs/plans/2026-02-28-feat-user-auth-plan.md
/workflows:work                                                  # Will ask for plan path
```

**Key principles:**
- Start fast, execute faster
- The plan is your guide — don't reinvent
- Test as you go, not at the end
- Ship complete features — don't leave things 80% done

---

### 3.4 `/workflows:review`

**Purpose:** Exhaustive multi-agent code review before merging.

**What it does:**
1. **Determine review target:** PR number, GitHub URL, branch name, or current branch
2. **Load review agents** from `compound-engineering.local.md` (or run `/setup` to create one)
3. **Run all configured review agents in parallel** — Each agent inspects the PR from its specialized angle
4. **Always-run agents** (regardless of config):
   - `agent-native-reviewer` — Verify new features are agent-accessible
   - `learnings-researcher` — Search `docs/solutions/` for past issues related to this PR
5. **Conditional agents** (auto-triggered when applicable):
   - If PR has migrations: `schema-drift-detector` + `data-migration-expert` + `deployment-verification-agent`
6. **Ultra-thinking deep dive** — Stakeholder perspectives (developer, ops, user, security, business) + scenario exploration (happy path, invalid inputs, boundaries, concurrency, scale, network, security)
7. **Code simplicity review** — Run `code-simplicity-reviewer` for YAGNI pass
8. **Synthesize findings** — Categorize by severity:
   - P1 (CRITICAL) — Blocks merge. Security vulns, data corruption, breaking changes
   - P2 (IMPORTANT) — Should fix. Performance, architecture, reliability
   - P3 (NICE-TO-HAVE) — Enhancements, cleanup, optimization
9. **Create todo files** for all findings using `file-todos` skill
10. **Offer end-to-end testing** — Browser tests (`/test-browser`) or iOS tests (`/xcode-test`) based on project type

**Protected artifacts:** Agents will NOT flag `docs/plans/*.md` or `docs/solutions/*.md` for deletion.

**Usage:**
```
/workflows:review 42                  # Review PR #42
/workflows:review latest              # Review the latest PR
/workflows:review feature/auth        # Review a branch
/workflows:review                     # Review current branch
```

**After review, resolve findings:**
```
/triage                     # Categorize and prioritize findings interactively
/resolve_todo_parallel      # Fix all approved findings in parallel
```

---

### 3.5 `/workflows:compound`

**Purpose:** Document a solved problem to build institutional knowledge.

**What it does:**

#### Phase 1: Parallel Research (5 subagents)
1. **Context Analyzer** — Extracts problem type, component, symptoms → YAML frontmatter
2. **Solution Extractor** — Analyzes investigation steps, root cause, working fix → Solution content
3. **Related Docs Finder** — Searches `docs/solutions/` for related docs → Cross-references
4. **Prevention Strategist** — Develops prevention strategies, test cases → Prevention content
5. **Category Classifier** — Determines category, suggests filename → File path

#### Phase 2: Assembly
- Collects all Phase 1 results
- Assembles single markdown file with validated YAML frontmatter
- Writes to `docs/solutions/[category]/[filename].md`

#### Phase 3: Optional Enhancement
- Auto-triggers specialized agents based on problem type:
  - Performance issue → `performance-oracle`
  - Security issue → `security-sentinel`
  - Database issue → `data-integrity-guardian`
  - Code-heavy → `kieran-rails-reviewer` + `code-simplicity-reviewer`

**Output categories:**
- `build-errors/`, `test-failures/`, `runtime-errors/`, `performance-issues/`
- `database-issues/`, `security-issues/`, `ui-bugs/`, `integration-issues/`, `logic-errors/`

**Auto-triggers** on phrases like "that worked", "it's fixed", "working now", "problem solved"

**Why this matters:** The `learnings-researcher` agent (used in `/workflows:plan` and `/workflows:review`) searches these docs automatically. The more you document, the smarter future planning and reviews become.

**Usage:**
```
/workflows:compound                         # Document most recent fix
/workflows:compound Fixed N+1 in briefs    # With context hint
```

---

## 4. Power Commands

### `/lfg` — Full Autonomous Workflow (Sequential)

Runs the complete pipeline end-to-end without stopping:

```
plan → deepen-plan → work → review → resolve_todo_parallel → test-browser → feature-video
```

Best for: Features where you want maximum automation and trust the pipeline.

### `/slfg` — Full Autonomous Workflow (Swarm/Parallel)

Same as `/lfg` but uses agent swarms for parallel task execution during the work phase. Faster for plans with many independent tasks.

### `/deepen-plan`

Takes an existing plan and runs parallel research agents on each section to add:
- Best practices and industry patterns
- Performance optimizations
- UI/UX improvements (if applicable)
- Quality enhancements and edge cases
- Real-world implementation examples

Also discovers and runs ALL review agents. The result is a deeply grounded, production-ready plan.

```
/deepen-plan docs/plans/2026-02-28-feat-auth-plan.md
```

### `/changelog`

Creates engaging changelogs for recent merges to the main branch. Supports daily/weekly summaries with analysis of new features, bug fixes, breaking changes, and contributor shoutouts.

### `/resolve_parallel`

Resolves all TODO comments in the codebase using parallel processing. Spawns parallel `pr-comment-resolver` agents for each item, then commits and pushes.

### `/resolve_pr_parallel`

Resolves all PR review comments in parallel. Spawns agents for each review thread, commits changes, resolves threads via GraphQL.

### `/resolve_todo_parallel`

Resolves all pending CLI todos in `todos/` directory using parallel processing.

### `/triage`

Interactive triage of findings — presents them one by one for categorization (P1/P2/P3), updates todo files with status transitions, generates summary of approved todos ready for work.

### `/test-browser`

Browser testing using `agent-browser` CLI. Maps changed files to routes, tests affected pages, handles failures, creates todos for issues.

Requires: `npm install -g agent-browser && agent-browser install`

### `/xcode-test`

iOS app testing using XcodeBuildMCP. Builds for simulator, installs, launches, takes screenshots, captures logs for errors.

### `/feature-video`

Records professional video walkthroughs using agent-browser for screenshots and ffmpeg for video creation. Uploads via rclone and embeds in PR description.

### `/agent-native-audit`

Comprehensive audit against 8 agent-native principles. Launches 8 parallel sub-agents, produces scored report:
- Action Parity, Tools as Primitives, Context Injection, Shared Workspace
- CRUD Completeness, UI Integration, Capability Discovery, Prompt-Native Features

### `/create-agent-skill`

Creates or edits Claude Code skills with expert guidance. Routes to `create-agent-skills` skill.

### `/generate_command`

Meta-command for creating new custom slash commands.

### `/heal-skill`

Fixes incorrect SKILL.md files when skills have wrong instructions or outdated API references.

### `/sync`

Sync Claude Code personal config across machines.

### `/report-bug` / `/reproduce-bug`

Report and reproduce bugs in the plugin or your project.

---

## 5. All 29 Agents — Detailed

Agents are specialized sub-processes that run autonomously. They are automatically invoked by workflow commands, but you can also reference them directly via the `Agent` tool.

### Review Agents (15)

| Agent | What It Reviews | Key Focus Areas | When It Runs |
|-------|----------------|-----------------|--------------|
| **agent-native-reviewer** | Feature parity | Can agents do everything users can? Action parity, context parity, tool design | Always during `/workflows:review` |
| **architecture-strategist** | Design integrity | Component dependencies, SOLID principles, microservice boundaries, architectural violations | Configurable |
| **code-simplicity-reviewer** | Over-engineering | YAGNI violations, premature abstractions, redundant code, unnecessary complexity | Always (final pass) |
| **data-integrity-guardian** | Database safety | Migration reversibility, constraints, transaction boundaries, referential integrity, GDPR/CCPA | Configurable |
| **data-migration-expert** | Data transformations | ID mapping validation against production, swapped values, rollback safety, dual-write patterns | When PR has migrations |
| **deployment-verification-agent** | Deploy readiness | Go/No-Go checklists, SQL verification queries, rollback procedures, monitoring plans | When PR has migrations |
| **dhh-rails-reviewer** | Rails conventions | DHH perspective: REST purity, fat models, thin controllers, JS framework contamination | Configurable (Rails projects) |
| **julik-frontend-races-reviewer** | Race conditions | Hotwire/Turbo compatibility, DOM event handling, promises, timers, concurrent operations | Configurable (JS projects) |
| **kieran-rails-reviewer** | Rails quality | High bar: conventions, clarity, maintainability. Strict on existing code, pragmatic on new | Configurable (Rails projects) |
| **kieran-python-reviewer** | Python quality | Pythonic patterns, type safety, comprehensive type hints. Strict on existing code | Configurable (Python projects) |
| **kieran-typescript-reviewer** | TypeScript quality | Type safety, modern patterns, never allows `any` without justification, explicit imports | Configurable (TS projects) |
| **pattern-recognition-specialist** | Pattern compliance | Design patterns, anti-patterns (god objects, circular deps), naming conventions, duplication | Configurable |
| **performance-oracle** | Performance | O(n^2) patterns, N+1 queries, memory management, caching, network optimization, scalability | Configurable |
| **schema-drift-detector** | Schema changes | Cross-references `schema.rb` diff against PR migrations to catch unrelated changes | When PR has migrations |
| **security-sentinel** | Security | SQL injection, XSS, auth/authz, hardcoded secrets, OWASP compliance, sensitive data exposure | Configurable |

### Research Agents (5)

| Agent | Purpose | How It Works |
|-------|---------|--------------|
| **repo-research-analyst** | Understand a codebase | Analyzes architecture docs, issue patterns, templates, codebase patterns |
| **best-practices-researcher** | Industry standards | Checks local skills first (dhh-rails-style, frontend-design, etc.), then goes online. Mandatory API deprecation check |
| **framework-docs-researcher** | Official documentation | Uses Context7 MCP for official docs, explores source code, provides version-specific constraints. Mandatory deprecation check |
| **git-history-analyzer** | Code archaeology | Git log, blame, shortlog to trace why code patterns exist |
| **learnings-researcher** | Past solutions | Searches `docs/solutions/` using grep-first strategy for relevant past fixes. Always runs in review and planning |

### Design Agents (3)

| Agent | Purpose | How It Works |
|-------|---------|--------------|
| **design-implementation-reviewer** | Figma comparison | Uses agent-browser + Figma MCP to compare live UI against Figma designs |
| **design-iterator** | UI refinement | N cycles of: screenshot → analyze → improve. Loads design skills for consistency |
| **figma-design-sync** | Fix visual diffs | Systematic comparison of layout, typography, colors, spacing, responsive behavior |

### Workflow Agents (5)

| Agent | Purpose | How It Works |
|-------|---------|--------------|
| **bug-reproduction-validator** | Validate bug reports | Classifies as: Confirmed Bug, Cannot Reproduce, Not a Bug, Environmental, Data Issue, User Error |
| **pr-comment-resolver** | Fix review comments | Analyzes comments, plans resolution, implements changes, verifies, reports |
| **spec-flow-analyzer** | Find spec gaps | Maps all user flows, identifies permutations, discovers gaps, formulates clarifying questions |
| **lint** | Code linting | Runs `standardrb` (Ruby), `erblint` (ERB), `brakeman` (security). Uses `model: haiku` for cost |
| **every-style-editor** | Editorial compliance | Reviews text for Every's style guide: title case, grammar, punctuation, mechanics |

### Docs Agents (1)

| Agent | Purpose | How It Works |
|-------|---------|--------------|
| **ankane-readme-writer** | Ruby gem READMEs | Ankane-style: imperative voice, 15 words max per sentence, strict section ordering |

---

## 6. All 19 Skills — Detailed

Skills provide deep domain knowledge and process guidance. They load automatically when relevant or can be invoked with `skill: <name>`.

### Architecture & Design

#### `agent-native-architecture`
Build apps where agents are first-class citizens. Core principles:
- **Parity** — Agent can do anything the user can do
- **Granularity** — Atomic primitives, not workflow tools
- **Composability** — New features = new prompts, not new code

15 reference documents covering: architecture patterns, tool design, dynamic context injection, action parity, shared workspaces, mobile patterns, testing, system prompt design, and more.

**Anti-patterns to avoid:** Context Starvation, Orphan Features, Sandbox Isolation, Silent Actions, Capability Hiding, Static Tool Mapping, Incomplete CRUD

### Development Tools

#### `dhh-rails-style`
Ruby/Rails code in DHH's 37signals philosophy:
- REST purity, fat models, thin controllers
- Current attributes, Hotwire patterns
- "Clarity over cleverness"
- Reference docs: controllers, models, frontend, architecture, gems

#### `andrew-kane-gem-writer`
Ruby gems following Andrew Kane's patterns:
- Entry point structure, class macro DSL
- Rails integration without coupling
- Minitest testing patterns

#### `dspy-ruby`
Type-safe LLM applications with DSPy.rb v0.34.3:
- Signatures, modules, tools, type system
- Optimization, Rails integration, testing, observability
- Events system, lifecycle callbacks, fiber-local LM context

#### `frontend-design`
Production-grade, distinctive frontend interfaces:
- Bold aesthetic direction, typography, color, motion
- Avoids generic AI aesthetics
- Spatial composition principles

#### `create-agent-skills`
Expert guidance for creating Claude Code skills:
- Skill vs command differences
- YAML frontmatter reference
- Dynamic features: arguments, context injection
- Progressive disclosure: keep SKILL.md under 500 lines

#### `skill-creator`
Step-by-step guide for creating effective skills (6-step process)

### Content & Workflow

#### `brainstorming`
Process knowledge for effective brainstorming:
- Phase 0-4: Assess clarity → Understand idea → Explore approaches → Capture design → Handoff
- Question techniques, YAGNI principles

#### `document-review`
Structured self-review for brainstorm or plan documents:
- Assesses clarity, completeness, specificity
- Applies YAGNI principles

#### `compound-docs`
Auto-capture solved problems as documentation:
- 7-step process with YAML validation gates
- Cross-referencing and critical pattern detection
- Categories: build-errors, test-failures, runtime-errors, performance-issues, etc.

#### `file-todos`
File-based todo tracking in `todos/` directory:
- YAML frontmatter: status, priority, tags, dependencies
- Naming: `{id}-{status}-{priority}-{description}.md`
- Statuses: pending → ready → complete

#### `every-style-editor`
Style guide review for Every's writing conventions

#### `resolve-pr-parallel`
Resolve all PR comments using parallel agent processing

#### `setup`
Interactive configurator for review agents:
- Auto-detects project type (Rails, Python, TypeScript, etc.)
- Two paths: "Auto-configure" or "Customize"
- Writes `compound-engineering.local.md` in project root

#### `git-worktree`
Manage git worktrees for isolated parallel development:
- Create, list, switch, cleanup
- Auto-copies `.env` files, manages `.gitignore`

### Multi-Agent Orchestration

#### `orchestrating-swarms`
Guide to multi-agent swarm orchestration:
- Primitives: Agent, Team, Teammate, Leader, Task, Inbox, Message, Backend
- 13 TeammateTool operations
- Patterns: Parallel Specialists, Pipeline, Self-Organizing Swarm
- Backends: in-process, tmux, iterm2

### File Transfer

#### `rclone`
Upload/sync files to cloud storage:
- Supports: S3, Cloudflare R2, Backblaze B2, Google Drive, Dropbox, S3-compatible

### Browser Automation

#### `agent-browser`
Browser automation using Vercel's agent-browser CLI:
- Uses ref-based element selection (@e1, @e2) from accessibility snapshots
- Navigate, click, fill forms, take screenshots
- Headed or headless mode

**Installation:**
```bash
npm install -g agent-browser
agent-browser install  # Downloads Chromium
```

### Image Generation

#### `gemini-imagegen`
Image generation/editing using Google's Gemini API:
- Text-to-image, image editing, multi-turn refinement
- Multiple reference images (up to 14)
- Custom resolutions and aspect ratios

**Requires:** `GEMINI_API_KEY` env var + Python packages (`google-genai`, `pillow`)

---

## 7. MCP Server: Context7

Automatically included with the plugin. Provides real-time documentation lookup for 100+ frameworks.

**Tools:**
- `resolve-library-id` — Find the Context7 library ID for a framework
- `query-docs` — Get up-to-date documentation and code examples

**Supported frameworks:** Rails, React, Next.js, Vue, Django, Laravel, Express, and 100+ more.

**Usage:** Automatically used by `framework-docs-researcher` agent. Can also be used directly in conversations.

**If not auto-loading**, add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

---

## 8. Configuration & Setup

### First-Time Project Setup

Run the setup skill to configure which review agents are active for your project:

```
/setup
```

This creates `compound-engineering.local.md` in your project root with:
- Detected project stack
- Configured review agents for `/workflows:review` and `/workflows:work`
- Custom review context

### Global Settings

**Plugin location:** `~/.claude/plugins/cache/every-marketplace/compound-engineering/2.35.2/`

**Global config:** `~/.claude/settings.json`
```json
{
  "enabledPlugins": {
    "compound-engineering@every-marketplace": true
  }
}
```

### Project-Level Config: `compound-engineering.local.md`

This file controls which review agents run. Created by the `setup` skill or manually:

```yaml
---
review_agents:
  - kieran-rails-reviewer
  - security-sentinel
  - performance-oracle
  - architecture-strategist
---

## Review Context

Focus on Rails 7.1 patterns. We use Hotwire/Turbo exclusively — no React.
Our API follows JSON:API spec.
```

### Directory Structure Created by the Plugin

```
your-project/
├── compound-engineering.local.md     # Review agent config (per project)
├── docs/
│   ├── brainstorms/                  # /workflows:brainstorm output
│   │   └── 2026-02-28-auth-brainstorm.md
│   ├── plans/                        # /workflows:plan output
│   │   └── 2026-02-28-feat-auth-plan.md
│   └── solutions/                    # /workflows:compound output
│       ├── performance-issues/
│       ├── security-issues/
│       ├── database-issues/
│       ├── runtime-errors/
│       ├── build-errors/
│       ├── test-failures/
│       ├── ui-bugs/
│       ├── integration-issues/
│       └── logic-errors/
└── todos/                            # /workflows:review findings
    ├── 001-pending-p1-security-vuln.md
    ├── 002-pending-p2-perf-issue.md
    └── 003-pending-p3-cleanup.md
```

---

## 9. Recipes: Common Task Patterns

### Recipe 1: New Feature (Full Quality)
```
/workflows:brainstorm Add real-time notifications
# → Answer questions, pick approach
# → Output: docs/brainstorms/2026-02-28-notifications-brainstorm.md

/workflows:plan Add real-time notifications
# → Auto-detects brainstorm, researches, creates plan
# → Output: docs/plans/2026-02-28-feat-notifications-plan.md

/deepen-plan docs/plans/2026-02-28-feat-notifications-plan.md
# → Adds best practices, performance tips, edge cases

/workflows:work docs/plans/2026-02-28-feat-notifications-plan.md
# → Builds feature, tests, creates PR

/workflows:review latest
# → 15+ agents review the PR in parallel

/resolve_todo_parallel
# → Fixes all findings

/workflows:compound
# → Documents any interesting solutions discovered
```

### Recipe 2: Quick Bug Fix
```
/workflows:plan Fix checkout race condition when two tabs submit
# → Skip brainstorm — requirements are clear
# → Select MINIMAL detail level

/workflows:work docs/plans/2026-02-28-fix-checkout-race-plan.md
# → Fix, test, PR

/workflows:review latest
# → Quick review

/workflows:compound
# → Document the race condition fix for future reference
```

### Recipe 3: Full Autopilot
```
/lfg Add user profile page with avatar upload and settings
# → Runs entire pipeline: plan → deepen → work → review → resolve → test → video
```

### Recipe 4: Review an Existing PR
```
/workflows:review 42
# → Reviews PR #42 with all configured agents

/triage
# → Interactively categorize findings

/resolve_todo_parallel
# → Fix approved findings
```

### Recipe 5: Explore Before Building
```
/workflows:brainstorm Should we use WebSockets or SSE for real-time updates?
# → Explores trade-offs collaboratively
# → Documents decision rationale
# → Hands off to planning when ready
```

### Recipe 6: Document a Fix You Just Made
```
# After solving a tricky problem...
/workflows:compound Fixed the N+1 query in brief generation
# → 5 parallel agents analyze and document the fix
# → Stored in docs/solutions/ for future reference
```

### Recipe 7: Refactor with Confidence
```
/workflows:plan Refactor authentication to use JWT
# → Select "A LOT" detail level for comprehensive plan

/deepen-plan docs/plans/2026-02-28-refactor-auth-jwt-plan.md

/workflows:work docs/plans/2026-02-28-refactor-auth-jwt-plan.md
# → Incremental commits, system-wide test checks

/workflows:review latest
# → Full review with architecture-strategist and security-sentinel
```

### Recipe 8: Parallel Development
```
# Use git worktrees to work on multiple features simultaneously
/workflows:work docs/plans/feature-a-plan.md
# → When asked about setup, choose "Use a worktree"
# → Isolated copy of repo, clean main branch preserved
```

---

## 10. Automation Playbook

### Level 1: Manual Workflow (Where You Are Now)
- Run each command yourself
- Choose options at each step
- Learn what each step does

### Level 2: Guided Automation
- Use `/lfg` for standard features
- Use `/slfg` for features with many parallel tasks
- Customize review agents per project via `setup`
- Build up `docs/solutions/` library

### Level 3: Pipeline Automation
- Plans auto-detect brainstorms (no manual linking needed)
- Reviews auto-search past solutions (learnings-researcher)
- Compound docs auto-trigger on "fixed" phrases
- Review agents auto-configured per project type
- Pipeline mode in `/lfg` skips all interactive prompts

### Level 4: Swarm Orchestration
- `/slfg` spawns parallel agent teams
- Independent tasks execute simultaneously
- Specialized agents (implementer, tester, reviewer) coordinate via task system
- Self-organizing task queues pick up work as it becomes available

### Building Toward Full Automation

**Step 1:** Always run `/workflows:compound` after solving problems → builds knowledge base

**Step 2:** Configure `compound-engineering.local.md` per project → reviews auto-configure

**Step 3:** Use `/lfg` for standard features → learn to trust the pipeline

**Step 4:** Use `/slfg` for complex features → leverage parallel execution

**Step 5:** Create custom skills for your project's unique patterns → encode institutional knowledge

**The compounding effect:** The more you use the pipeline, the more `docs/solutions/` fills up. The more solutions exist, the smarter `learnings-researcher` becomes during planning and review. The smarter reviews become, the fewer issues reach production. Your velocity compounds over time.

---

## 11. Cheat Sheet

### Workflow Commands
```
/workflows:brainstorm [idea]          # Explore WHAT to build
/workflows:plan [description]         # Plan HOW to build it
/workflows:work [plan path]           # BUILD it
/workflows:review [PR/branch]         # VERIFY it
/workflows:compound [context]         # REMEMBER the lessons
```

### Power Commands
```
/lfg [description]                    # Full autopilot (sequential)
/slfg [description]                   # Full autopilot (parallel swarms)
/deepen-plan [plan path]              # Enhance plan with research
/triage                               # Categorize review findings
/resolve_todo_parallel                # Fix all approved todos
/resolve_pr_parallel                  # Fix all PR comments
/test-browser                         # Browser test affected pages
/feature-video                        # Record demo video for PR
/changelog                            # Generate changelog
/agent-native-audit                   # Audit agent-native compliance
/create-agent-skill                   # Create new skill
/sync                                 # Sync config across machines
```

### Key File Locations
```
docs/brainstorms/*.md                 # Brainstorm outputs
docs/plans/*.md                       # Plan outputs
docs/solutions/**/*.md                # Documented solutions (knowledge base)
todos/*.md                            # Review findings / work items
compound-engineering.local.md         # Project review agent config
```

### Quick Agent Reference
```
Review:     architecture-strategist, code-simplicity-reviewer, security-sentinel,
            performance-oracle, pattern-recognition-specialist, data-integrity-guardian,
            data-migration-expert, deployment-verification-agent, schema-drift-detector,
            dhh-rails-reviewer, kieran-rails-reviewer, kieran-python-reviewer,
            kieran-typescript-reviewer, julik-frontend-races-reviewer, agent-native-reviewer

Research:   repo-research-analyst, best-practices-researcher, framework-docs-researcher,
            git-history-analyzer, learnings-researcher

Design:     design-implementation-reviewer, design-iterator, figma-design-sync

Workflow:   bug-reproduction-validator, pr-comment-resolver, spec-flow-analyzer, lint,
            every-style-editor

Docs:       ankane-readme-writer
```

### Plan Detail Levels
```
MINIMAL  → Simple bugs, small improvements, clear features
MORE     → Most features, complex bugs, team collaboration (default)
A LOT    → Major features, architectural changes, complex integrations
```

### Finding Severity Levels
```
P1 (CRITICAL)    → Blocks merge. Security, data corruption, breaking changes
P2 (IMPORTANT)   → Should fix. Performance, architecture, reliability
P3 (NICE-TO-HAVE) → Enhancements, cleanup, optimization
```

### Todo File Lifecycle
```
{id}-pending-{priority}-{desc}.md    → New finding
{id}-ready-{priority}-{desc}.md      → Approved, ready to work
{id}-complete-{priority}-{desc}.md   → Done
```

---

## 12. Troubleshooting

### Context7 MCP Not Loading

Add manually to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

### Agent-Browser Not Working
```bash
npm install -g agent-browser
agent-browser install  # Downloads Chromium
```

### Review Agents Not Running
Run `/setup` to create `compound-engineering.local.md` in your project root, or check that the file exists and has valid YAML frontmatter with `review_agents` list.

### `/lfg` or `/slfg` Failing on First Run
The `ralph-wiggum` skill is optional. If it's not installed, the ralph-loop step is skipped automatically (fixed in v2.35.0).

### Plans Not Auto-Detecting Brainstorms
Brainstorm documents must be:
- In `docs/brainstorms/` directory
- Created within the last 14 days
- Have a topic matching the feature description (filename or YAML frontmatter)

### Plugin Not Installed / Not Found
```bash
claude /plugin install compound-engineering
```

Verify in `~/.claude/plugins/installed_plugins.json` and `~/.claude/settings.json` that it's enabled.

---

## Appendix: Version History Highlights

| Version | Key Addition |
|---------|-------------|
| 2.35.2 | Brainstorm integration in `/workflows:plan` with `origin:` frontmatter |
| 2.35.0 | Fixed LFG/SLFG first-run failures, plan file writing |
| 2.34.0 | Gemini CLI converter target |
| 2.33.0 | Setup skill, learnings-researcher in review, schema-drift-detector |
| 2.31.0 | Document-review skill, /sync command, 79% context token optimization |
| 2.30.0 | Orchestrating-swarms skill, /slfg command |
| 2.28.0 | /workflows:brainstorm command |
| 2.27.0 | Interactive Q&A in plan, incremental commits in work |
| 2.26.0 | /lfg command |
| 2.25.0 | Agent-browser skill (replaced Playwright MCP) |
| 2.22.0 | Rclone skill for cloud uploads |
| 2.18.0 | Agent-native-architecture major expansion |
| 2.17.0 | 5 new agent-native reference docs from building Every Reader iOS |
| 2.16.0 | DHH-rails-style major expansion from 37signals coding style guide |

---

*This guide covers Compound Engineering Plugin v2.35.2. For the latest changes, check the [CHANGELOG](https://github.com/EveryInc/compound-engineering-plugin).*
