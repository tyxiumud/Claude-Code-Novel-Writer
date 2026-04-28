# Claude Code Novel Writer v3.3 — Documentation

## Autonomous Novel Generation Platform

Claude Code Novel Writer v3.3 is an autonomous writing platform that generates complete novels through intelligent agent orchestration. Built with Claude Code best practices, it leverages 8 specialized sub-agents, adaptive quality control, and a comprehensive Web dashboard to create consistent, high-quality fiction.

## Architecture Overview

### Core Design Principles

1. **Agent Specialization**: Each agent handles a specific aspect (writing, planning, world-building, continuity, auditing)
2. **Adaptive Quality Control**: Real-time monitoring with automatic standards adjustment based on performance
3. **Self-Healing**: Automatic error detection, diagnosis, and recovery without human intervention
4. **Project-Agnostic Tool Chain**: All enums and configuration driven by `project-context.json` `_config` section
5. **Visual Management**: Full-featured Web dashboard for real-time progress, editing, and metadata management

### Master Orchestrator

The system centers around a **Master Orchestrator** (`CLAUDE.md`) that:
- Continuously assesses story progress and system health
- Determines next logical actions via an enhanced decision matrix
- Delegates work to 8 specialized sub-agents with rich context
- Maintains state consistency across all data files
- Incorporates quality feedback and performance data into decisions

### 8 Specialized Sub-Agents

#### chapter-writer
- Creates complete chapters (2000-4000 words) in a single task
- Quality-aware generation with metrics feedback
- Includes all planned scenes, dialogue, and sensory details
- Returns manuscript-ready content

#### plot-architect
- Structures compelling narratives with proper pacing
- Manages subplots, foreshadowing threads, and story beats
- Creates detailed chapter outlines with context-aware planning
- Balances action, character development, and world-building

#### worldbuilder
- Creates consistent, detailed settings with rule tracking
- Designs magic systems, cultures, and histories
- Ensures internal logic and authenticity
- Provides plot hooks and story opportunities

#### character-developer
- Builds psychologically complex characters with authentic voices
- Manages character relationships, growth arcs, and knowledge states
- Ensures consistent personality development across chapters

#### continuity-editor
- Maintains consistency across all story elements
- Tracks timeline, character knowledge, and world rules
- Identifies and resolves contradictions with specific correction instructions
- Runs automatically every 3 chapters

#### error-recovery
- Self-diagnoses system and story issues
- Implements automatic correction and file repair
- Provides alternative approach exploration when stuck
- Ensures continuous progress without human intervention

#### smart-planner
- Analyzes story progress and recommends pacing adjustments
- Adapts planning based on quality metrics and performance data
- Provides progress-responsive chapter optimization
- Runs at major milestones (every 5 chapters)

#### reference-auditor (NEW in v3.3)
- Cross-file consistency audit across 8 categories:
  - Character consistency (names, traits, knowledge)
  - Foreshadowing sync (tracking JSON vs. markdown vs. chapter content)
  - Chapter status sync (status JSON vs. actual files vs. plot-progress)
  - File existence verification (referenced files vs. actual filesystem)
  - Issue cross-referencing (tracker JSON vs. chapter-status links)
  - Config validation (enum values match between `_config` and actual data)
  - Stale data detection (outdated timestamps, orphaned references)
  - Orphaned reference detection (unreferenced files, dead links)
- Triggered every 5 chapters, when editing references, adding foreshadowing, or starting new volumes

## System Components

### Web Dashboard v3 (`automation/web_dashboard.py`)

Single-file Python HTTP server (stdlib only) providing a full SPA. Five main panels:

1. **Chapter Management** — Progress bar, 200-chapter color-coded grid, filterable/sortable chapter list, chapter modal with 3 tabs (Read/Edit/Metadata)
2. **Foreshadowing Tracking** — Timeline visualization, card list, CRUD operations, chapter association via multi-select
3. **Issue Tracking** — Sortable table, severity badges, resolve/delete operations, chapter association
4. **Character Overview** — Core character profile cards from `character-knowledge.json`
5. **Outlines & References** — Sidebar file browser for 14 reference files from the main project, markdown viewer with edit mode, Ctrl+S to save

All dropdowns for enums (hook_types, phases, severities, etc.) are driven by `project-context.json` `_config` — change the JSON, the UI adapts.

### State Management

| File | Purpose |
|------|---------|
| `planning/plot-progress.json` | Current chapter, volume, word count, phase, milestones |
| `planning/chapter-status.json` | Per-chapter status, word count, hook_type, system_option, parent_child_phase, foreshadowing links, issue links |
| `planning/project-context.json` | Genre, settings, character list, volume planning, `_config` enum values |
| `planning/foreshadow-tracking.json` | 8 foreshadowing threads with buried/recovery chapters, status, related characters |
| `planning/issue-tracker.json` | Issues with severity, category, affected chapters, resolution status |
| `planning/quality-metrics.json` | Quality scores, per-chapter reviews, detected issues |
| `planning/system-health.json` | Component health status, overall score, last check timestamp |
| `planning/novel-outline.json` | Full outline structure across all volumes |
| `planning/scene-tracker.json` | Scene-level breakdown per chapter |
| `planning/style-guide.json` | Writing style parameters and rules |
| `characters/character-knowledge.json` | Character profiles, relationships, knowledge states |
| `worldbuilding/world-state.json` | World rules, locations, political systems, history |

### Automated Hooks (`.claude/settings.json`)
- **PostToolUse**: Injects context reminders after major tool operations
- **SessionStart**: Initializes system state and runs health checks
- **Stop**: Prevents system halting to maintain continuous generation

### Automation Scripts

| Script | Purpose |
|--------|---------|
| `web_dashboard.py` | Web dashboard v3 — main visual management UI |
| `dashboard.py` | Terminal-based progress dashboard |
| `start-web-dashboard.bat` | Windows one-click launcher |
| `quality-check.sh` | Automated quality analysis after chapter completion |
| `system-health-check.sh` | Comprehensive system health monitoring |
| `auto-backup.sh` | Smart backup with intelligent cleanup |
| `migrate-to-new-project.sh` | Cross-project migration (Linux/Mac) |
| `migrate-to-new-project.bat` | Cross-project migration (Windows) |

## Quality Standards

### Automatic Quality Maintenance
- **Chapter Length**: 2000-4000 Chinese characters
- **Dialogue Ratio**: 30-40% of content
- **Paragraph Length**: Optimized for mobile (3 lines max)
- **Chapter Endings**: Always include hooks (action/reversal/sensory/time/emotion/cognition)
- **System Options**: Basic every 2 chapters, high-risk every 5, hidden every 10
- **Continuity Checks**: Every 3 chapters
- **Tech Display**: Must include human-efficiency comparison data

### Story Structure
- **8 Volumes** x **25 Chapters** = **200 Chapters**
- **Target**: ~1,000,000 Chinese characters total
- **Parent-Child Phases**: suspicion (1-3) → testing (4-15) → cooperation (16-50) → open (51-100) → dependence (101-150) → succession (151-200)

### Adaptive Quality Modes
- **Excellence Mode** (90+ score): Publication-ready standards, final polish
- **High Performance Mode** (80+ score): Maintain standards, optimize for momentum
- **Standard Mode** (60-79 score): Balanced quality and progress
- **Quality Focus Mode** (<60 score): Enhanced revision standards, quality prioritized over speed

## Project-Agnostic Configuration

All enum values are centralized in `planning/project-context.json` under `_config`:

```json
{
  "_config": {
    "chapter_statuses": ["not_started", "draft", "published"],
    "hook_types": ["action", "reversal", "sensory", "time", "emotion", "cognition"],
    "parent_child_phases": ["怀疑期", "试探期", "合作期", "明牌期", "依赖期", "传承期"],
    "issue_severities": ["critical", "major", "minor"],
    "issue_categories": ["逻辑矛盾", "人物一致性", "世界观违反", "节奏问题", "字数不足", "其他"],
    "foreshadowing_statuses": ["active", "resolved", "abandoned"],
    "system_option_types": ["basic", "high_risk", "hidden"]
  }
}
```

When migrating to a new project, edit this `_config` — all dashboard dropdowns and validation rules update automatically.

## Cross-Project Migration

```bash
# Linux/Mac
./migrate-to-new-project.sh ~/my-new-novel

# Windows
migrate-to-new-project.bat D:\my-new-novel
```

Generates complete directory structure, all JSON templates (including `_config`), agent definitions, and automation scripts. Edit the 5 core config files and start writing.

## Quick Start

```bash
git clone https://github.com/forsonny/Claude-Code-Novel-Writer.git
cd Claude-Code-Novel-Writer

# Launch Web dashboard (optional)
python automation/web_dashboard.py

# Start autonomous generation
claude --dangerously-skip-permissions
```

## Performance Benchmarks

- **Generation Speed**: 3,000-6,000 words per hour
- **Quality Consistency**: Publication-ready with automatic monitoring
- **Error Rate**: <0.5% requiring manual intervention
- **Self-Healing**: 95%+ automatic issue resolution

## What's New in v3.3

- **Web Dashboard v3**: Foreshadowing tracking, issue tracking, reference files tab, chapter metadata editor
- **Reference Auditor Agent**: 8-category cross-file consistency checking
- **Data Expansion**: `foreshadow-tracking.json`, `issue-tracker.json`, `_config` in `project-context.json`
- **Chapter Metadata**: Per-chapter hook_type, system_option, parent_child_phase, foreshadowing/issue associations

---

**Claude Code Novel Writer v3.3** — Autonomous creative AI, intelligent monitoring, self-healing architecture, comprehensive Web-based management.
