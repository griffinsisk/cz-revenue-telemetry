# PROJECT_KICKOFF.md

> **This file lives alongside `CLAUDE.md` in the repo root.**
> Claude reads and maintains it. Do not delete it between sessions.

---

## Instructions for Claude

Read this entire file before doing anything else.

1. **Check Current State first.** If a phase and next action are listed, resume from there — don't restart. Skip to that phase in the checklist.
2. **If this is a new project** (Current State is blank), run the Kickoff Interview below — do not skip it.
3. **After the interview or reading a pre-filled brief:** Present a written plan summarizing what you understand and what you intend to do next. Wait for explicit approval before taking any action.
4. **Gate checks are hard stops.** At every gate, list each item and its status, then ask for confirmation before moving to the next phase. Do not self-approve.
5. **End of session:** Update Current State with the active phase, last completed action, any blockers, and the next action. Commit this file if the repo is initialized.
6. **Operate under the checklist.** Each phase below defines your workflow. Follow it in order. Don't skip steps without explicit instruction.

---

## Current State

> *Claude maintains this block. Update it at the end of every session.*

- **Phase:** Phase 1 — Complete. Moving to Phase 2.
- **Last completed:** Spec doc written to docs/spec.md with all sections. Updated with /replace endpoint, date range parameterization, historical backfill vs monthly sync modes.
- **Blockers:** None
- **Next action:** Phase 2 — Project Setup (repo init, .gitignore, CLAUDE.md, docs structure, testing framework)
- **Last updated:** 2026-02-24

---

## Project Brief

> *Claude fills this in during the Kickoff Interview. If you're on Path B (pre-filled), populate the fields you know before starting — Claude will only ask about what's missing.*

```
Mission (1-2 sentences):
Make it easy for CloudZero customers to automate sending revenue data from business systems
into CloudZero's unit metric telemetry API for unit economics analysis.

Target user:
FinOps practitioners and cloud engineers who have access to both Salesforce and CloudZero.

Problem it solves:
No automated bridge between revenue systems (Salesforce, etc.) and CloudZero telemetry.
Customers must manually upload CSVs or go without revenue-based unit economics.

What the product does (UX, workflows, key flows):
Python CLI tool. Customer writes a YAML config (source, query, field mappings, dimensions).
Runs `sync` to pull revenue from source, transform to CZ telemetry format, send via API.
Supports historical backfill (explicit date range) and monthly sync (default: previous month).
Uses /replace endpoint for idempotent re-runs. Fully flexible associated_cost dimensions.

MVP (smallest useful thing):
Salesforce connector that pulls Opportunities via SOQL, transforms to unit metric telemetry
with customer-defined dimensions, and sends to CloudZero API.

V1 additions:
HubSpot connector, Stripe connector, retry logic, Lambda deployment template.

V2 / later:
Connector plugin architecture, Campfire connector, generic REST/DB connectors.

Explicitly out of scope:
Allocation streams, cost splitting, CSV upload, web UI, hosted service, real-time ingestion.

Tech stack:
  - Language: Python 3.10+
  - Frontend: N/A (CLI only)
  - Backend: Click (CLI), simple-salesforce, httpx, pydantic, PyYAML
  - Database: N/A
  - Hosting: Customer-managed (cron, Lambda, GitHub Actions)
  - AI models (if any): None

Constraints or strong preferences:
- Repo shared with customers — clean, well-documented
- No hardcoded dimensions — fully customer-configured
- CZ API limits: 100 records/sec, 5MB/request, max 5 associated_cost dimensions
- Credentials via env vars only, never in config files
```

---

## Kickoff Interview

> **Claude: Run this interview at the start of every new project. Follow the steps in order.**

### Step 1 — Brain Dump

Open with exactly this question and nothing else:

> *"Before we dive in — give me a brain dump of everything you're thinking about this project. Don't worry about structure, just tell me what you want to build, why, who it's for, any ideas you have, concerns, things you've already decided, things you haven't. Everything."*

Wait for the full response. Do not interrupt or ask follow-ups yet.

### Step 2 — Synthesize & Reflect Back

After the brain dump, do the following in a single response:

1. **Summarize** what you heard in 3-5 sentences, framed as your understanding of the project
2. **Map** what was said to the Project Brief fields — note which fields are now filled, partially filled, or still blank
3. **Highlight** anything that stood out: strong ideas, potential risks, scope that might be too broad, things that seem underspecified

Example format:
> *"Here's what I'm taking away: [summary]. Based on what you shared, I have a good sense of [X, Y], but I still need to understand [A, B, C] before we can move forward. A few things I noticed: [observations/suggestions]."*

### Step 3 — Targeted Follow-Up Interview

Ask only about the gaps identified in Step 2. Rules:
- **One question at a time.** Wait for the answer before asking the next.
- **Lead with a suggestion when you can.** Don't ask open questions if you can propose a reasonable default and ask for confirmation. Example: *"For the database, given your stack I'd suggest PostgreSQL — does that work, or did you have something else in mind?"*
- **Group related micro-questions** if they're tightly connected. Example: *"For the MVP scope — are you thinking just the core [X] flow, or does that also need to include [Y]?"*
- **Don't re-ask** anything already answered in the brain dump.
- Continue until all Project Brief fields are filled.

### Step 4 — Fill the Project Brief

Once all gaps are resolved, fill in every field in the Project Brief block above. Then present the completed brief to the user for confirmation before proceeding to Phase 1.

> *"Here's the Project Brief based on everything we discussed. Does this look right, or anything to adjust before I move on?"*

Do not proceed to Phase 1 until the user confirms the brief is correct.

---

## Phase 1: Ideation & Spec

**Claude:** The Project Brief is your source for this phase. It should be fully filled and confirmed before you reach here. Do not re-interview — use what's already captured. Your job now is to expand it into a full spec.

### Define the Project
- [ ] Mission is clear (1-2 sentences)
- [ ] Target user is defined
- [ ] Problem is articulated
- [ ] Product behavior is described in detail (UX, workflows, edge cases)

### Define Milestones
- [ ] **MVP** — Initial core features defined
- [ ] **V1** — Improvements and additions defined
- [ ] **V2** — Extended functionality defined
- [ ] **Later / Nice to have** — Listed
- [ ] **Not in Scope** — Explicitly called out (prevents scope creep)

### Spec Doc
**Claude:** Using the confirmed Project Brief, draft the full spec and save it to `docs/spec.md`. If any engineering details (architecture, schema, API design) need clarification, ask as a single grouped question — don't pepper the user with multiple rounds. Propose sensible defaults wherever you can.

**Product Requirements:**
- [ ] User personas and use cases written
- [ ] UX flow documented (screens, interactions, edge cases)
- [ ] Success criteria defined — how do we know it works?

**Engineering Design:**
- [ ] Tech stack finalized (recommend if not provided)
- [ ] High-level architecture drafted
- [ ] API design outlined (endpoints, data flow)
- [ ] Database schema defined
- [ ] Hosting and deployment plan noted

### ✅ Gate Check — Phase 1
**Claude: Stop here. List each item above and mark it complete or incomplete. Do not proceed to Phase 2 until the user confirms all items are done.**

- [ ] Spec doc written and saved to `docs/spec.md`
- [ ] Milestones clearly defined
- [ ] Tech stack chosen
- [ ] MVP can be described in one sentence

---

## Phase 2: Project Setup

### Repository & Environment
- [ ] GitHub repo created
- [ ] `.gitignore` configured (covers `.env`, `node_modules`, OS files)
- [ ] `.env.example` generated based on stack; real `.env` populated by user
- [ ] Secrets verified as not committed

### CLAUDE.md
**Claude:** Draft a lean `CLAUDE.md` based on the spec. It should cover project goals, folder structure, style guide, constraints, branching rules, frequently used commands, and links to docs. Do not bloat it.

- [ ] Project goals (2-3 sentences)
- [ ] Architecture overview and folder structure
- [ ] Design style guide and UX guidelines
- [ ] Constraints and policies (e.g., "never push to main", "always use env vars")
- [ ] Repo etiquette (branching, PR vs. direct merge, naming conventions)
- [ ] Frequently used commands
- [ ] Links to other doc files

### Documentation Structure
- [ ] `docs/spec.md` — Created in Phase 1
- [ ] `docs/architecture.md` — System design, components, data flow
- [ ] `docs/changelog.md` — What's changed over time
- [ ] `docs/project-status.md` — Current state for re-entry
- [ ] `docs/reference/` — Key feature docs as needed

**Claude:** After setup, add a note to `CLAUDE.md`: "Update files in the docs folder after major milestones and feature additions."

### Testing Strategy
- [ ] Testing approach decided: unit, E2E, or both
- [ ] Test framework set up (Jest, Vitest, Playwright, etc.)
- [ ] "Done" criteria for tests defined (e.g., "all API routes have tests")

### MCP Servers
**Claude:** Recommend MCP servers based on the confirmed tech stack. Only suggest what's relevant.

- [ ] Frontend MCP (if applicable)
- [ ] Database MCP (if applicable)
- [ ] Browser testing: Playwright MCP or Puppeteer MCP (for web apps)
- [ ] Deployment: Vercel MCP, Netlify, etc.
- [ ] Analytics: Mixpanel, PostHog, etc. (if applicable)
- [ ] Project management: Linear, GitHub Issues, etc. (if applicable)
- [ ] Each MCP has setup docs referenced in `CLAUDE.md`

### Slash Commands
- [ ] `/commit` — Commit with message
- [ ] `/commit-push-pr` — Commit, push, and open PR
- [ ] `/update-docs` — Update docs folder with changes
- [ ] `/changelog-updater` — Update changelog after features/fixes
- [ ] `/frontend-tester` — Run Playwright E2E tests
- [ ] `/retro-agent` — Reflect on session, update CLAUDE.md and commands
- [ ] `/create-issue` — Log a GitHub issue from a description

### ✅ Gate Check — Phase 2
**Claude: Stop here. List each item above and mark it complete or incomplete. Do not proceed to Phase 3 until the user confirms all items are done.**

- [ ] Repo created, `.env` configured, secrets protected
- [ ] `CLAUDE.md` written and focused
- [ ] Docs folder structure in place
- [ ] MCP servers connected and tested
- [ ] `/commit` and `/update-docs` slash commands working
- [ ] Testing framework set up

---

## Phase 3: Build

### Pre-Build
- [ ] Model selected: Opus (planning, complex tasks) or Sonnet (implementation)
- [ ] Plan mode entered (`/plan`) — Claude explains what it will do before doing it
- [ ] Claude pointed at spec doc with instruction to build MVP (Milestone 1)
- [ ] Parallel subagents identified for independent tasks

### Build Workflow

**Claude:** Choose the appropriate workflow for each task:

| Workflow | When to Use |
|---|---|
| **Single Feature** | One feature at a time, straightforward |
| **Issue-Based** | GitHub Issues are the source of truth |
| **Multi-Agent** | Multiple independent features in parallel |

**Single Feature Flow:** Research → Plan → Implement → Test

1. **Research** — Create a research report. Reference transcripts, docs, or web searches. Save to `docs/`.
2. **Plan** — Use plan mode or `/feature-dev` to break down tasks before coding.
3. **Implement** — Build it. Keep commits small and frequent.
4. **Test** — Run tests. Use `/frontend-tester` for E2E. Fix what breaks.

**Issue-Based Flow:**
1. Log features and tasks as GitHub Issues using `/create-issue`
2. Work specific issues, referencing numbers in commits and PRs

**Multi-Agent Flow (Advanced):**
1. Set up git worktrees so parallel work doesn't conflict
2. Spin up multiple Claude sessions on different features
3. Merge completed work back together, resolve conflicts carefully

---

## Ongoing Practices

**Claude:** These apply throughout every session, not just during setup.

- [ ] **Update CLAUDE.md** when the project evolves
- [ ] **Regression prevention** — When a mistake happens, use `#memorize` so it doesn't repeat
- [ ] **Run retros** — Use `/retro-agent` after dev sessions
- [ ] **Keep docs current** — Use `/update-docs` after milestones
- [ ] **Small commits** — Commit frequently, keep diffs reviewable
- [ ] **Don't skip plan mode** — Always explain before executing on non-trivial tasks

---

## Quick Reference

**Models:**
- Opus 4 — Planning, architecture, complex reasoning
- Sonnet 4 — Day-to-day implementation

**MCP Servers:**
- Vercel MCP — Deployment
- Mixpanel / PostHog — Analytics
- Linear — Project management
- Playwright / Puppeteer — Browser testing

**Plugins:**
- `frontend-design` — Better UI generation
- `feature-dev` — Structured feature development
- `compounding-engineering` — AI-powered dev workflow tools
