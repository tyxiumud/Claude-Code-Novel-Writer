# Claude Code 小说写作系统 v3.3

自主小说生成平台 — 集成智能监控、自适应质量控制、自愈能力，支持 Web 可视化管理，工具链可跨项目迁移。

[![Version](https://img.shields.io/badge/版本-3.3-blue)]() [![AI](https://img.shields.io/badge/AI-Claude%20Code-orange)]()

## 概述

Claude Code 小说写作系统 v3.3 是一个智能自主写作平台，通过多 Agent 编排自动生成完整小说。配备自适应质量控制、智能错误恢复、项目无关的工具链迁移方案，以及功能完备的 Web 管理看板。

### 核心功能

- **全自主运行**：智能 Agent 协同，无需人工干预
- **自适应质量**：实时质量监控，自动调整标准
- **智能规划**：故事分析和自适应章节规划
- **自愈能力**：自动错误检测、诊断和恢复
- **Web 看板 v3**：浏览器实时查看进度、阅读章节、在线编辑、伏笔追踪、问题跟踪、大纲参考文件管理
- **8 个专业 Agent**：各司其职，协同创作
- **跨项目迁移**：一条命令将完整工具链迁移到新项目
- **参考审核 Agent**：自动跨文件一致性检查，覆盖 8 类审核维度

## 快速开始

### 1. 克隆并设置
```bash
git clone https://github.com/forsonny/Claude-Code-Novel-Writer.git
cd Claude-Code-Novel-Writer
```

### 2. 初始化项目数据

编辑以下文件，填入你的小说设定：

| 文件 | 内容 |
|------|------|
| `planning/plot-progress.json` | 书名、目标字数、卷数 |
| `planning/project-context.json` | 类型、设定、枚举值配置 |
| `characters/character-knowledge.json` | 主角和核心角色档案 |
| `worldbuilding/world-state.json` | 世界观、政治体系、地理 |

### 3. 启动 Web 看板（可选但推荐）
```bash
python automation/web_dashboard.py
# 浏览器打开 http://127.0.0.1:8080
```

### 4. 启动自主写作
```bash
claude --dangerously-skip-permissions
```

## 系统架构

```
Web 看板 v3         ←  可视化管理层
       │ HTTP API
Claude Code 编排层   ←  智能引擎
  Master Orchestrator 决策循环
  8 个专业 Agent 并行协作
  Hooks 自动提醒 + 质量检查
       │
数据层 (JSON + Markdown)  ←  持久存储
  planning/     进度 + 质量追踪
  manuscript/   章节文件
  characters/   角色档案
  worldbuilding/ 世界观
```

### Master Orchestrator（主编排器）

中央智能，通过增强型决策矩阵协调整个创作流程：
```
上下文注入 → 健康检查 → 状态同步 → 质量分析 → 智能规划 → 内容生成 → 质量监控 → 持续优化 → 循环
```

### 8 个专业 Agent

| Agent | 职责 | 特点 |
|-------|------|------|
| **chapter-writer** | 生成完整章节 (2000-4000字) | 质量感知，指标反馈 |
| **plot-architect** | 故事结构 & 节奏设计 | 上下文感知，进度分析 |
| **worldbuilder** | 幻想世界 & 体系构建 | 一致性感知，规则追踪 |
| **character-developer** | 人物心理 & 弧线设计 | 弧线感知，关系追踪 |
| **continuity-editor** | 跨章一致性维护 | 智能错误检测 |
| **error-recovery** | 系统诊断 & 修复 | 自动问题解决和预防 |
| **smart-planner** | 自适应故事规划 | 进度响应式优化 |
| **reference-auditor** | 跨文件一致性审核 | 8 类检查维度，自动发现修复 |

## Web 看板 v3

浏览器访问 `http://127.0.0.1:8080`，五大功能面板：

| 面板 | 功能 |
|------|------|
| **章节管理** | 百分比进度条、200 章色块总览（颜色区分状态）、章节列表筛选排序、弹窗阅读完整内容 |
| **伏笔追踪** | 时间线可视化、卡片列表、新增/编辑/删除伏笔、章节关联 |
| **问题跟踪** | 可排序表格、严重度徽标 (严重/重要/次要)、解决/删除操作、章节关联 |
| **角色速览** | 核心角色档案卡片一览 |
| **大纲与参考** | 侧边栏文件浏览器、Markdown 查看器/编辑器（14 个参考文件）、Ctrl+S 保存 |

### 章节弹窗（3 个标签页）
- **阅读**：完整章节内容，支持 Markdown 渲染
- **编辑**：浏览器内 Markdown 编辑器
- **元数据**：编辑 hook_type、system_option、parent_child_phase、伏笔关联、问题关联 — 所有下拉框从 `project-context.json` 的 `_config` 段读取

## 质量标准

### 实时质量指标
- **字数分析**：章节长度 2000-4000 中文字符
- **对话比例**：30-40% 对话平衡
- **段落长度**：适合手机阅读（≤3行）
- **钩子密度**：每章结尾必有钩子（行动/反转/感官/时间/情绪/认知）

### 自适应质量模式
| 模式 | 触发条件 | 策略 |
|------|----------|------|
| **卓越模式** (90+) | 接近完稿 | 出版级标准，精雕细琢 |
| **高性能模式** (80+) | 质量好速度快 | 保持标准，注重动量 |
| **标准模式** (60-79) | 正常状态 | 平衡质量与进度 |
| **质量聚焦** (<60) | 质量下滑 | 提升标准，修订优先 |

## 项目结构

```
Claude-Code-Novel-Writer/
├── CLAUDE.md                       # 主编排器配置
├── README.md                       # 英文说明
├── README_CN.md                    # 中文说明（本文件）
├── .claude/
│   ├── agents/                     # 8 个专业 Agent 定义
│   │   ├── chapter-writer.md       # 章节写作
│   │   ├── plot-architect.md       # 情节架构
│   │   ├── worldbuilder.md         # 世界观构建
│   │   ├── character-developer.md  # 角色开发
│   │   ├── continuity-editor.md    # 连续性编辑
│   │   ├── error-recovery.md       # 错误恢复
│   │   ├── smart-planner.md        # 智能规划
│   │   └── reference-auditor.md    # 参考审核
│   ├── skills/                     # 快捷指令
│   ├── settings.json               # 自动化 Hooks 配置
│   └── context-injection.txt       # 动态系统提醒
├── manuscript/chapters/            # 生成的小说章节 (.md)
├── planning/                       # 进度 & 质量追踪
│   ├── plot-progress.json          # 当前故事位置
│   ├── chapter-status.json         # 逐章完成状态（含元数据）
│   ├── project-context.json        # 项目专属参数 & _config 枚举
│   ├── foreshadow-tracking.json    # 伏笔生命周期追踪
│   ├── issue-tracker.json          # 问题追踪与解决
│   ├── quality-metrics.json        # 实时质量数据
│   ├── system-health.json          # 系统组件监控
│   ├── novel-outline.json          # 故事大纲结构
│   ├── scene-tracker.json          # 场景级追踪
│   └── style-guide.json            # 写作风格参数
├── automation/                     # 自动化工具
│   ├── web_dashboard.py            # Web 看板 v3（主推）
│   ├── dashboard.py                # 终端看板
│   ├── start-web-dashboard.bat     # Windows 一键启动
│   ├── quality-check.sh            # 自动质量分析
│   ├── system-health-check.sh      # 系统健康检查
│   └── auto-backup.sh              # 自动备份
├── characters/                     # 角色数据
│   └── character-knowledge.json
├── worldbuilding/                  # 世界观数据
│   └── world-state.json
├── migrate-to-new-project.sh       # 迁移脚本 (Linux/Mac)
├── migrate-to-new-project.bat      # 迁移脚本 (Windows)
└── Documentation/                  # 完整文档
    ├── README.md
    ├── User-Guide.md
    └── System-Architecture.md
```

## 迁移到新项目

一键将完整工具链迁移到其他小说项目：

**Windows：**
```cmd
migrate-to-new-project.bat D:\my-new-novel
```

**Linux / Mac：**
```bash
./migrate-to-new-project.sh ~/my-new-novel
```

自动生成所有 JSON 模板文件，只需修改 5 个核心配置文件即可启动。

## 故障排除

### 系统不启动
- 检查 `CLAUDE.md` 和 `.claude/agents/` 是否完整
- 系统会自动诊断缺失组件并尝试修复

### 质量下降
- 实时反馈即时识别质量问题
- 自适应建议提供上下文感知的改进方案

### 章节重复
```bash
ls manuscript/chapters/
python automation/dashboard.py --sync-report
```

## v3.3 更新内容

**Web 看板 v3**：新增伏笔追踪面板、问题跟踪面板、大纲与参考 tab（14 个可编辑参考文件）、章节元数据编辑器

**参考审核 Agent (reference-auditor)**：自动跨文件一致性检查，覆盖角色一致性、伏笔同步、章节状态同步、文件存在性、问题交叉引用、配置验证、过期数据检测、孤立引用 8 个维度

**数据层扩展**：新增 `foreshadow-tracking.json`、`issue-tracker.json`；`project-context.json` 新增 `_config` 段实现项目无关的枚举值管理

**章节元数据**：全部 26 章已扩展 hook_type、system_option、parent_child_phase、foreshadowing_buried/resolved、issue_ids 字段

---

**Claude Code 小说写作系统 v3.3** — 自主创意写作，智能监控，自愈架构，Web 可视化管理。
