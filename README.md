# Claude Code Novel Writer v3.3

Autonomous novel-writing platform with intelligent monitoring, adaptive quality control, self-healing capabilities, and a Web management dashboard. Built for Claude Code.

[![Version](https://img.shields.io/badge/Version-3.3-blue)]() [![AI](https://img.shields.io/badge/AI-Claude%20Code-orange)]()

## Overview

Claude Code Novel Writer v3.3 is an autonomous writing platform that generates complete novels through intelligent agent orchestration. It features adaptive quality control, smart error recovery, a project-agnostic tool chain, and a full-featured Web dashboard for real-time management.

### Key Features

- **Fully Autonomous**: Generates novels through intelligent agent coordination
- **Adaptive Quality**: Real-time quality monitoring with automatic standards adjustment
- **Smart Planning**: Story analysis and adaptive chapter planning
- **Self-Healing**: Automatic error detection, diagnosis, and recovery
- **Web Dashboard v3**: Browser-based progress tracking, chapter reading, online editing, foreshadowing tracking, issue tracking, and reference file management
- **8 Specialized Agents**: Each handling a specific aspect of novel creation
- **Cross-Project Migration**: One-command tool chain migration to new projects
- **Reference Auditor**: Automated cross-file consistency checking across all project data

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/forsonny/Claude-Code-Novel-Writer.git
cd Claude-Code-Novel-Writer
```

### 2. Initialize Project Data

Edit these files with your novel settings:

| File | Content |
|------|---------|
| `planning/plot-progress.json` | Title, target words, volumes |
| `planning/project-context.json` | Genre, settings, enum values |
| `characters/character-knowledge.json` | Character profiles |
| `worldbuilding/world-state.json` | World, politics, geography |

### 3. Launch Web Dashboard (optional but recommended)
```bash
python automation/web_dashboard.py
# Open http://127.0.0.1:8080 in browser
```

### 4. Start Autonomous Writing
```bash
claude --dangerously-skip-permissions
```

## Architecture

```
Web Dashboard (v3)  ←  Visual Management Layer
       │ HTTP API
Claude Code Layer   ←  Intelligent Engine
  Master Orchestrator decision loop
  8 specialized agents in parallel
  Hooks: auto-reminders + quality checks
       │
Data Layer (JSON + Markdown)  ←  Persistent Storage
  planning/     Progress + quality tracking
  manuscript/   Chapter files
  characters/   Character profiles
  worldbuilding/ World state
```

### Master Orchestrator

Central intelligence coordinating the entire creation flow:
```
Context Injection → Health Check → State Sync → Quality Analysis →
Smart Planning → Content Generation → Quality Monitoring → Continuous Optimization → Loop
```

### 8 Specialized Agents

| Agent | Purpose |
|-------|---------|
| **chapter-writer** | Complete chapter generation (2000-4000 words) with quality metrics |
| **plot-architect** | Story structure & pacing design with progress analysis |
| **worldbuilder** | Fantasy world & system construction with rule tracking |
| **character-developer** | Character psychology & arc design with relationship tracking |
| **continuity-editor** | Cross-chapter consistency maintenance |
| **error-recovery** | System diagnosis & automatic repair |
| **smart-planner** | Adaptive story planning & pacing optimization |
| **reference-auditor** | Cross-file consistency audit (characters, foreshadowing, chapters, config) |

## Web Dashboard v3

Open `http://127.0.0.1:8080` in browser. Five main tabs:

| Tab | Features |
|-----|----------|
| **Chapter Management** | Progress bar, chapter grid (200 chapters, color-coded), chapter list with filtering/sorting, full-content reading modal |
| **Foreshadowing Tracking** | Timeline visualization, card list, create/edit/delete threads, chapter association |
| **Issue Tracking** | Sortable table, severity badges (critical/major/minor), resolve/delete operations, chapter association |
| **Character Overview** | Core character profile cards |
| **Outlines & References** | Sidebar file browser, markdown viewer/editor (14 reference files), Ctrl+S to save |

### Chapter Modal (3 tabs)
- **Read**: Full chapter content with markdown rendering
- **Edit**: In-browser markdown editor
- **Metadata**: Edit hook_type, system_option, parent_child_phase, foreshadowing associations, issue associations — all dropdowns populated from `project-context.json` `_config`

## Quality Standards

### Real-Time Metrics
- **Word Count**: Chapter length 2000-4000 Chinese characters
- **Dialogue Ratio**: 30-40% conversation
- **Paragraph Length**: Optimized for mobile reading (3 lines max)
- **Hook Density**: Every chapter ends with a hook (action/reversal/sensory/time/emotion/cognition)

### Adaptive Quality Modes
| Mode | Trigger | Strategy |
|------|---------|----------|
| **Excellence** (90+) | Near completion | Publication-ready polish |
| **High Performance** (80+) | Good quality, fast velocity | Maintain standards, keep momentum |
| **Standard** (60-79) | Normal state | Balance quality and progress |
| **Quality Focus** (<60) | Quality decline | Raise standards, prioritize revision |

## Project Structure

```
Claude-Code-Novel-Writer/
├── CLAUDE.md                       # Master orchestrator configuration
├── README.md                       # English documentation (this file)
├── README_CN.md                    # Chinese documentation
├── .claude/
│   ├── agents/                     # 8 specialized agent definitions
│   │   ├── chapter-writer.md
│   │   ├── plot-architect.md
│   │   ├── worldbuilder.md
│   │   ├── character-developer.md
│   │   ├── continuity-editor.md
│   │   ├── error-recovery.md
│   │   ├── smart-planner.md
│   │   └── reference-auditor.md
│   ├── skills/                     # Quick-command skills
│   ├── settings.json               # Automated hooks configuration
│   └── context-injection.txt       # Dynamic system reminders
├── manuscript/chapters/            # Generated novel chapters (.md)
├── planning/                       # Progress & quality tracking
│   ├── plot-progress.json          # Current story position
│   ├── chapter-status.json         # Per-chapter completion status
│   ├── project-context.json        # Project-specific parameters & _config enums
│   ├── foreshadow-tracking.json    # Foreshadowing thread lifecycle
│   ├── issue-tracker.json          # Issue tracking & resolution
│   ├── quality-metrics.json        # Real-time quality data
│   ├── system-health.json          # System component monitoring
│   ├── novel-outline.json          # Story outline structure
│   ├── scene-tracker.json          # Scene-level tracking
│   └── style-guide.json            # Writing style parameters
├── automation/                     # Tooling
│   ├── web_dashboard.py            # Web dashboard v3 (main UI)
│   ├── dashboard.py                # Terminal dashboard
│   ├── start-web-dashboard.bat     # Windows launcher
│   ├── quality-check.sh            # Automated quality analysis
│   ├── system-health-check.sh      # System health check
│   └── auto-backup.sh              # Automatic backup
├── characters/                     # Character data
│   └── character-knowledge.json
├── worldbuilding/                  # World state data
│   └── world-state.json
├── migrate-to-new-project.sh       # Migration script (Linux/Mac)
├── migrate-to-new-project.bat      # Migration script (Windows)
└── Documentation/                  # System documentation
    ├── README.md
    ├── User-Guide.md
    └── System-Architecture.md
```

## Migration to New Project

One command to migrate the complete tool chain:

**Windows:**
```cmd
migrate-to-new-project.bat D:\my-new-novel
```

**Linux/Mac:**
```bash
./migrate-to-new-project.sh ~/my-new-novel
```

All JSON templates are auto-generated. Edit the 5 core config files and start writing.

## Troubleshooting

### System Won't Start
- Verify CLAUDE.md and .claude/agents/ are intact
- System auto-diagnoses missing components and attempts repair

### Quality Issues
- Real-time feedback identifies problems immediately
- Adaptive suggestions provide context-aware improvements

### Chapter Duplication
```bash
ls manuscript/chapters/
python automation/dashboard.py --sync-report
```

### Performance Issues
- Continuous speed and efficiency monitoring
- Auto-triggered performance optimization

## What's New in v3.3

**Web Dashboard v3**: Foreshadowing tracking panel, issue tracking panel, outlines & references tab with 14 editable reference files, chapter metadata editor

**Reference Auditor Agent**: Automated cross-file consistency checking across 8 categories (character consistency, foreshadowing sync, chapter status sync, file existence, issue cross-referencing, config validation, stale data detection, orphaned references)

**Data Layer Expansion**: `foreshadow-tracking.json`, `issue-tracker.json`, `_config` section in `project-context.json` for project-agnostic enum management

**Chapter Metadata**: All 26 chapters extended with hook_type, system_option, parent_child_phase, foreshadowing_buried/resolved, and issue_ids fields

---

**Claude Code Novel Writer v3.3** — autonomous novel creation with intelligent monitoring, self-healing architecture, and comprehensive Web-based management.
