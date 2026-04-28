#!/bin/bash
# ═══════════════════════════════════════════════════════
# Claude-Code-Novel-Writer 迁移脚本
# 将完整工具链迁移到新项目目录
# 用法: ./migrate-to-new-project.sh <目标项目路径>
# ═══════════════════════════════════════════════════════

set -e

if [ -z "$1" ]; then
  echo "用法: ./migrate-to-new-project.sh <目标项目路径>"
  echo "示例: ./migrate-to-new-project.sh ~/my-new-novel"
  exit 1
fi

TARGET="$1"
SOURCE="$(cd "$(dirname "$0")/.." && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║  Novel-Writer 工具链迁移                ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "源: $SOURCE"
echo "目标: $TARGET"
echo ""

# ──── 1. 创建目录结构 ────
echo "[1/8] 创建目录结构..."
mkdir -p "$TARGET/.claude/agents"
mkdir -p "$TARGET/.claude/skills/novel-writer-workflow-guide"
mkdir -p "$TARGET/.claude/skills/pre-write-checklist"
mkdir -p "$TARGET/.claude/skills/getting-started-guide"
mkdir -p "$TARGET/.claude/output-styles"
mkdir -p "$TARGET/manuscript/chapters"
mkdir -p "$TARGET/planning"
mkdir -p "$TARGET/worldbuilding"
mkdir -p "$TARGET/characters"
mkdir -p "$TARGET/automation"

# ──── 2. 复制通用组件（不含项目数据） ────
echo "[2/8] 复制 Agent 定义..."
cp "$SOURCE/.claude/agents/"*.md "$TARGET/.claude/agents/"

echo "[3/8] 复制 Skills..."
cp "$SOURCE/../.claude/skills/novel-writer-workflow-guide/SKILL.md" "$TARGET/.claude/skills/novel-writer-workflow-guide/" 2>/dev/null || true
cp "$SOURCE/../.claude/skills/pre-write-checklist/SKILL.md" "$TARGET/.claude/skills/pre-write-checklist/" 2>/dev/null || true
cp "$SOURCE/../.claude/skills/getting-started-guide/SKILL.md" "$TARGET/.claude/skills/getting-started-guide/" 2>/dev/null || true

echo "[4/8] 复制 Web 看板..."
cp "$SOURCE/automation/web_dashboard.py" "$TARGET/automation/"
cp "$SOURCE/automation/start-web-dashboard.bat" "$TARGET/automation/" 2>/dev/null || true

echo "[5/8] 复制 Output Styles..."
cp "$SOURCE/output-styles/autonomous-novelist.md" "$TARGET/.claude/output-styles/" 2>/dev/null || true

# ──── 3. 生成项目专属文件（模板） ────
echo "[6/8] 生成基础模板数据文件..."

# project-context.json 模板 (含 _config 段)
cat > "$TARGET/planning/project-context.json" << 'EOF'
{
  "_config": {
    "chapter_statuses": ["not_started", "draft", "published"],
    "hook_types": ["行动钩子","反转钩子","感官钩子","时间钩子","情绪钩子","认知钩子"],
    "parent_child_phases": ["怀疑期","试探期","合作期","明牌期","依赖期","传承期"],
    "issue_severities": ["critical", "major", "minor", "suggestion"],
    "issue_categories": ["逻辑矛盾","人物一致性","世界观违反","节奏问题","字数不足","其他"],
    "foreshadowing_statuses": ["active", "resolved", "abandoned"],
    "system_option_types": ["basic", "high_risk", "hidden"],
    "volume_phases": [],
    "target_chapter_chars": "2000-4000"
  },
  "project": "新小说",
  "platform": "",
  "genre": "",
  "style": {},
  "structure": {
    "total_volumes": 8,
    "chapters_per_volume": 25,
    "total_chapters": 200,
    "target_total_chars": 1000000,
    "target_chapter_chars": "2000-4000"
  }
}
EOF

# plot-progress.json 模板
cat > "$TARGET/planning/plot-progress.json" << 'EOF'
{
  "novel_title": "新小说",
  "target_words": 1000000,
  "total_chapters_target": 200,
  "current_chapter": 1,
  "current_scene": 1,
  "current_volume": 1,
  "total_volumes": 8,
  "chapter_status": "not_started",
  "volume_title": "卷1",
  "total_chinese_chars": 0,
  "chapters_completed": [],
  "chapters_published": [],
  "chapters_draft": [],
  "parent_child_phase": "怀疑期",
  "last_action": "project_initialized",
  "next_milestone": "chapter_1",
  "last_sync_time": "",
  "active_foreshadowing": [],
  "tech_lines_active": []
}
EOF

# chapter-status.json 模板
cat > "$TARGET/planning/chapter-status.json" << 'EOF'
{
  "chapter_1": {"status": "not_started", "title": "", "chinese_chars": 0, "words_estimated": 0, "file_exists": false, "volume": 1, "volume_phase": "", "hook_type": null, "system_option": null, "parent_child_phase": null, "foreshadowing_buried": [], "foreshadowing_resolved": [], "issue_ids": []}
}
EOF

# world-state.json 模板
cat > "$TARGET/worldbuilding/world-state.json" << 'EOF'
{
  "world": {"setting": "", "location": "", "dynasty": "", "tech_level": "", "magic_system": ""},
  "political": {"system": "", "key_institutions": [], "power_factions": []},
  "geography": {"capital": "", "key_locations": []},
  "history_timeline": {},
  "rules_and_constraints": []
}
EOF

# character-knowledge.json 模板
cat > "$TARGET/characters/character-knowledge.json" << 'EOF'
{
  "protagonist": {
    "name": "",
    "identity": {"surface": "", "real": "", "revealed": "", "current_title": ""},
    "age": 0,
    "personality": [],
    "skills": [],
    "weaknesses": [],
    "current_status": ""
  },
  "core_characters": {},
  "character_relationships": {},
  "deceased_characters": [],
  "future_antagonists": []
}
EOF

# quality-metrics.json 模板
cat > "$TARGET/planning/quality-metrics.json" << 'EOF'
{
  "last_check": "",
  "overall_score": 0,
  "chapters_reviewed": [],
  "issues": []
}
EOF

# system-health.json 模板
cat > "$TARGET/planning/system-health.json" << 'EOF'
{
  "score": 100,
  "status": "healthy",
  "last_check": "",
  "components": {
    "agents": true,
    "manuscript": true,
    "planning": true,
    "worldbuilding": true,
    "characters": true
  }
}
EOF

# context-injection.txt
cat > "$TARGET/.claude/context-injection.txt" << 'EOF'
<system_reminder>PROJECT INITIALIZED: 新小说项目已就绪。修改 planning/ 下 JSON 文件配置项目参数。开始写作前先 LS manuscript/chapters/ 确认无重复。</system_reminder>
<system_reminder>PRIORITY: 第1章是新内容。写之前先检查 manuscript/chapters/ 确认没有重复。每章目标2000-4000字。风格: 短段落、对话驱动、快节奏、章末钩子。</system_reminder>
EOF

echo "[7/8] 生成伏笔追踪模板..."
cat > "$TARGET/planning/foreshadow-tracking.json" << 'EOF'
{
  "threads": []
}
EOF

echo "[8/8] 生成问题跟踪模板..."
cat > "$TARGET/planning/issue-tracker.json" << 'EOF'
{
  "issues": []
}
EOF

# settings.local.json 模板
cat > "$TARGET/.claude/settings.local.json" << 'EOF'
{
  "permissions": {
    "allow": [
      "Bash(ls *)",
      "Bash(automation/*.py)",
      "Bash(automation/*.py *)",
      "Bash(python automation/web_dashboard.py *)",
      "Bash(python3 automation/web_dashboard.py *)",
      "WebSearch",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:127.0.0.1:8080)",
      "WebFetch(domain:localhost:8080)",
      "Skill(novel-writer-workflow-guide)",
      "Skill(pre-write-checklist)",
      "Skill(getting-started-guide)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "task",
        "hooks": [{
          "type": "command",
          "command": "echo '<system_reminder>TASK COMPLETED: IMMEDIATELY save output, check files with LS, update progress tracking, determine next action. NEVER create duplicate chapters.</system_reminder>' >> .claude/context-injection.txt"
        }]
      },
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "command": "echo '<system_reminder>FILE SAVED: Check completion, update tracking, verify file structure. PREVENT DUPLICATION.</system_reminder>' >> .claude/context-injection.txt"
        }]
      },
      {
        "matcher": "LS",
        "hooks": [{
          "type": "command",
          "command": "echo '<system_reminder>FILES LISTED: Identify highest chapter, check for gaps/duplicates, update tracking. Never duplicate existing content.</system_reminder>' >> .claude/context-injection.txt"
        }]
      }
    ],
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "echo '<system_reminder>SESSION STARTED: Read context injection, sync state via LS manuscript/chapters/, update tracking. CRITICAL: Never duplicate existing chapters.</system_reminder>' >> .claude/context-injection.txt"
      }]
    }]
  }
}
EOF

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  迁移完成！                             ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "下一步:"
echo "  1. cd \"$TARGET\""
echo "  2. 编辑 planning/project-context.json — 修改 project、platform、genre、style 等"
echo "  3. 编辑 planning/plot-progress.json — 修改 novel_title 等参数"
echo "  4. 编辑 characters/character-knowledge.json — 填入角色"
echo "  5. 编辑 worldbuilding/world-state.json — 填入世界观"
echo "  6. 启动 Web 看板: python automation/web_dashboard.py"
echo "  7. 启动自主写作: claude --dangerously-skip-permissions"
echo ""
echo "迁移文件清单:"
echo "  通用组件 (可直接复用):"
echo "    ✅ .claude/agents/          (8个 Agent)"
echo "    ✅ .claude/skills/          (3个 Skill)"
echo "    ✅ automation/web_dashboard.py"
echo "    ✅ .claude/settings.local.json"
echo "    ✅ .claude/output-styles/"
echo "    ✅ planning/foreshadow-tracking.json (空模板)"
echo "    ✅ planning/issue-tracker.json (空模板)"
echo ""
echo "  需手动填写 (项目专属):"
echo "    ⚠️  planning/project-context.json (_config段可自定义枚举值)"
echo "    ⚠️  planning/plot-progress.json"
echo "    ⚠️  planning/chapter-status.json"
echo "    ⚠️  characters/character-knowledge.json"
echo "    ⚠️  worldbuilding/world-state.json"
echo "    ⚠️  .claude/context-injection.txt"
