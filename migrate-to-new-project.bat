@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

if "%~1"=="" (
  echo 用法: migrate-to-new-project.bat ^<目标项目路径^>
  echo 示例: migrate-to-new-project.bat D:\my-new-novel
  exit /b 1
)

set "TARGET=%~1"
set "SOURCE=%~dp0"

echo ╔══════════════════════════════════════════╗
echo ║  Novel-Writer 工具链迁移 (Windows)     ║
echo ╚══════════════════════════════════════════╝
echo.
echo 源: %SOURCE%
echo 目标: %TARGET%
echo.

echo [1/8] 创建目录结构...
mkdir "%TARGET%\.claude\agents" 2>nul
mkdir "%TARGET%\.claude\skills\novel-writer-workflow-guide" 2>nul
mkdir "%TARGET%\.claude\skills\pre-write-checklist" 2>nul
mkdir "%TARGET%\.claude\skills\getting-started-guide" 2>nul
mkdir "%TARGET%\.claude\output-styles" 2>nul
mkdir "%TARGET%\manuscript\chapters" 2>nul
mkdir "%TARGET%\planning" 2>nul
mkdir "%TARGET%\worldbuilding" 2>nul
mkdir "%TARGET%\characters" 2>nul
mkdir "%TARGET%\automation" 2>nul

echo [2/8] 复制 Agent 定义...
xcopy /Y /Q "%SOURCE%.claude\agents\*.md" "%TARGET%\.claude\agents\" >nul

echo [3/8] 复制 Skills...
if exist "%SOURCE%..\..\.claude\skills\novel-writer-workflow-guide\SKILL.md" (
  copy /Y "%SOURCE%..\..\.claude\skills\novel-writer-workflow-guide\SKILL.md" "%TARGET%\.claude\skills\novel-writer-workflow-guide\" >nul
)
if exist "%SOURCE%..\..\.claude\skills\pre-write-checklist\SKILL.md" (
  copy /Y "%SOURCE%..\..\.claude\skills\pre-write-checklist\SKILL.md" "%TARGET%\.claude\skills\pre-write-checklist\" >nul
)
if exist "%SOURCE%..\..\.claude\skills\getting-started-guide\SKILL.md" (
  copy /Y "%SOURCE%..\..\.claude\skills\getting-started-guide\SKILL.md" "%TARGET%\.claude\skills\getting-started-guide\" >nul
)

echo [4/8] 复制 Web 看板...
copy /Y "%SOURCE%automation\web_dashboard.py" "%TARGET%\automation\" >nul

echo [5/8] 复制 Output Styles...
if exist "%SOURCE%output-styles\autonomous-novelist.md" (
  copy /Y "%SOURCE%output-styles\autonomous-novelist.md" "%TARGET%\.claude\output-styles\" >nul
)

echo [6/8] 生成基础模板数据文件...
(
echo {
echo   "_config": {
echo     "chapter_statuses": ["not_started", "draft", "published"],
echo     "hook_types": ["行动钩子","反转钩子","感官钩子","时间钩子","情绪钩子","认知钩子"],
echo     "parent_child_phases": ["怀疑期","试探期","合作期","明牌期","依赖期","传承期"],
echo     "issue_severities": ["critical", "major", "minor", "suggestion"],
echo     "issue_categories": ["逻辑矛盾","人物一致性","世界观违反","节奏问题","字数不足","其他"],
echo     "foreshadowing_statuses": ["active", "resolved", "abandoned"],
echo     "system_option_types": ["basic", "high_risk", "hidden"],
echo     "volume_phases": [],
echo     "target_chapter_chars": "2000-4000"
echo   },
echo   "project": "新小说",
echo   "platform": "",
echo   "genre": "",
echo   "style": {},
echo   "structure": {
echo     "total_volumes": 8,
echo     "chapters_per_volume": 25,
echo     "total_chapters": 200,
echo     "target_total_chars": 1000000,
echo     "target_chapter_chars": "2000-4000"
echo   }
echo }
) > "%TARGET%\planning\project-context.json"

(
echo {
echo   "novel_title": "新小说",
echo   "target_words": 1000000,
echo   "total_chapters_target": 200,
echo   "current_chapter": 1,
echo   "current_scene": 1,
echo   "current_volume": 1,
echo   "total_volumes": 8,
echo   "chapter_status": "not_started",
echo   "volume_title": "卷1",
echo   "total_chinese_chars": 0,
echo   "chapters_completed": [],
echo   "chapters_published": [],
echo   "chapters_draft": [],
echo   "parent_child_phase": "怀疑期",
echo   "last_action": "project_initialized",
echo   "next_milestone": "chapter_1",
echo   "last_sync_time": "",
echo   "active_foreshadowing": [],
echo   "tech_lines_active": []
echo }
) > "%TARGET%\planning\plot-progress.json"

(
echo {
echo   "chapter_1": {"status": "not_started", "title": "", "chinese_chars": 0, "words_estimated": 0, "file_exists": false, "volume": 1, "volume_phase": "", "hook_type": null, "system_option": null, "parent_child_phase": null, "foreshadowing_buried": [], "foreshadowing_resolved": [], "issue_ids": []}
echo }
) > "%TARGET%\planning\chapter-status.json"

(
echo {
echo   "world": {"setting": "", "location": "", "dynasty": "", "tech_level": "", "magic_system": ""},
echo   "political": {"system": "", "key_institutions": [], "power_factions": []},
echo   "geography": {"capital": "", "key_locations": []},
echo   "history_timeline": {},
echo   "rules_and_constraints": []
echo }
) > "%TARGET%\worldbuilding\world-state.json"

(
echo {
echo   "protagonist": {"name": "", "identity": {}, "age": 0, "personality": [], "skills": [], "weaknesses": [], "current_status": ""},
echo   "core_characters": {},
echo   "character_relationships": {},
echo   "deceased_characters": [],
echo   "future_antagonists": []
echo }
) > "%TARGET%\characters\character-knowledge.json"

(
echo {
echo   "score": 100, "status": "healthy", "last_check": "",
echo   "components": {"agents": true, "manuscript": true, "planning": true, "worldbuilding": true, "characters": true}
echo }
) > "%TARGET%\planning\system-health.json"

(
echo ^<system_reminder^>PROJECT INITIALIZED: 新小说项目已就绪。修改 planning/ 下 JSON 文件配置项目参数。^</system_reminder^>
echo ^<system_reminder^>PRIORITY: 第1章待写。每章目标2000-4000字。短段落、对话驱动、快节奏、章末钩子。^</system_reminder^>
) > "%TARGET%\.claude\context-injection.txt"

echo [7/8] 生成伏笔追踪模板...
(
echo {
echo   "threads": []
echo }
) > "%TARGET%\planning\foreshadow-tracking.json"

echo [8/8] 生成问题跟踪模板...
(
echo {
echo   "issues": []
echo }
) > "%TARGET%\planning\issue-tracker.json"

(
echo {
echo   "permissions": {
echo     "allow": [
echo       "Bash(ls *)",
echo       "Bash(python automation/web_dashboard.py *)",
echo       "Bash(python automation/web_dashboard.py)",
echo       "WebSearch",
echo       "Skill(novel-writer-workflow-guide)",
echo       "Skill(pre-write-checklist)",
echo       "Skill(getting-started-guide)"
echo     ]
echo   }
echo }
) > "%TARGET%\.claude\settings.local.json"

echo.
echo ╔══════════════════════════════════════════╗
echo ║  迁移完成！                             ║
echo ╚══════════════════════════════════════════╝
echo.
echo 下一步:
echo   1. cd /d "%TARGET%"
echo   2. 编辑 planning\project-context.json — 修改 project、platform、genre、style 等
echo   3. 编辑 planning\plot-progress.json — 修改 novel_title 等
echo   4. 编辑 characters\character-knowledge.json — 填入角色
echo   5. 编辑 worldbuilding\world-state.json — 填入世界观
echo   6. 启动 Web 看板: python automation\web_dashboard.py
echo   7. 启动自主写作: claude --dangerously-skip-permissions
echo.
echo 通用组件 (可直接复用):
echo   ✅ .claude\agents\          (8个 Agent)
echo   ✅ .claude\skills\          (3个 Skill)
echo   ✅ automation\web_dashboard.py
echo   ✅ .claude\settings.local.json
echo   ✅ planning\foreshadow-tracking.json (空模板)
echo   ✅ planning\issue-tracker.json (空模板)
echo.
echo 需手动填写 (项目专属):
echo   ⚠️  planning\project-context.json (_config段可自定义枚举值)
echo   ⚠️  planning\plot-progress.json
echo   ⚠️  planning\chapter-status.json
echo   ⚠️  characters\character-knowledge.json
echo   ⚠️  worldbuilding\world-state.json
echo   ⚠️  .claude\context-injection.txt
