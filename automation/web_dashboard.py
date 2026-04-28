#!/usr/bin/env python3
"""
Web Dashboard v3 — with metadata editor, foreshadowing tracker, and issue tracker.
Usage: python web_dashboard.py [--port 8080]
"""

import json
import os
import re
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import argparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLANNING = PROJECT_ROOT / "planning"
MANUSCRIPT = PROJECT_ROOT / "manuscript" / "chapters"
WORLDBUILDING = PROJECT_ROOT / "worldbuilding"
CHARACTERS = PROJECT_ROOT / "characters"

# Reference docs from the main project (one level up)
MAIN_PROJECT = PROJECT_ROOT.parent
REFERENCE_DIRS = {
    "大纲与规划": MAIN_PROJECT / "1-大纲与规划",
    "卷细纲": MAIN_PROJECT / "1-大纲与规划" / "卷细纲",
    "原则与检查": MAIN_PROJECT / "3-原则与检查",
    "素材库": MAIN_PROJECT / "2-稿件管理" / "素材库",
    "进度跟踪": MAIN_PROJECT / "4-进度跟踪",
}


def load_json(path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_file_safe(filepath):
    for enc in ("utf-8-sig", "utf-8", "gbk", "gb2312", "latin-1"):
        try:
            with open(filepath, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return ""


def _write_file_safe(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def get_manuscript_stats():
    if not MANUSCRIPT.exists():
        return {"total_files": 0, "files": []}
    files = []
    for f in sorted(MANUSCRIPT.glob("*.md")):
        text = _read_file_safe(f)
        char_count = len(text.replace("\n", "").replace(" ", ""))
        files.append({
            "name": f.name,
            "size": f.stat().st_size,
            "chars": char_count
        })
    return {"total_files": len(files), "files": files}


NOW = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


class DashboardHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            return self.serve_json(self.build_status())
        elif path == "/api/chapters":
            return self.serve_json(self.build_chapters())
        elif path == "/api/characters":
            return self.serve_json(load_json(CHARACTERS / "character-knowledge.json"))
        elif path == "/api/world":
            return self.serve_json(load_json(WORLDBUILDING / "world-state.json"))
        elif path == "/api/config":
            ctx = load_json(PLANNING / "project-context.json")
            return self.serve_json(ctx.get("_config", {}))
        elif path == "/api/reference-files":
            return self.serve_json(self.build_reference_list())
        elif path == "/api/reference":
            return self.serve_reference_file(parsed)
        elif path == "/api/foreshadowing":
            return self.serve_json(load_json(PLANNING / "foreshadow-tracking.json"))
        elif path == "/api/issues":
            return self.serve_json(load_json(PLANNING / "issue-tracker.json"))
        elif re.match(r"^/api/chapter/(\d+)$", path):
            m = re.match(r"^/api/chapter/(\d+)$", path)
            return self.serve_chapter(int(m.group(1)))
        elif re.match(r"^/api/chapter-metadata/(\d+)$", path):
            m = re.match(r"^/api/chapter-metadata/(\d+)$", path)
            return self.serve_chapter_metadata(int(m.group(1)))
        elif path == "/" or path == "":
            return self.serve_html()
        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        if re.match(r"^/api/chapter/(\d+)$", path):
            m = re.match(r"^/api/chapter/(\d+)$", path)
            return self.save_chapter(int(m.group(1)), body)
        elif re.match(r"^/api/chapter-metadata/(\d+)$", path):
            m = re.match(r"^/api/chapter-metadata/(\d+)$", path)
            return self.save_chapter_metadata(int(m.group(1)), body)
        elif path == "/api/save-chapter-status":
            return self.save_chapter_status(body)
        elif path == "/api/save-plot-progress":
            return self.save_plot_progress(body)
        elif path == "/api/reference":
            return self.save_reference_file(body)
        elif path == "/api/foreshadowing":
            return self.save_foreshadowing(body)
        elif path == "/api/issues":
            return self.save_issues(body)
        elif re.match(r"^/api/foreshadowing/(.+)/delete$", path):
            m = re.match(r"^/api/foreshadowing/(.+)/delete$", path)
            return self.delete_foreshadowing(m.group(1))
        elif re.match(r"^/api/issues/(.+)/resolve$", path):
            m = re.match(r"^/api/issues/(.+)/resolve$", path)
            return self.resolve_issue(m.group(1))
        elif re.match(r"^/api/issues/(.+)/delete$", path):
            m = re.match(r"^/api/issues/(.+)/delete$", path)
            return self.delete_issue(m.group(1))
        else:
            self.send_error(404, "Not Found")

    # ──── serve helpers ────

    def serve_json(self, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def serve_html(self):
        html = HTML_TEMPLATE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(html))
        self.end_headers()
        self.wfile.write(html)

    def serve_chapter(self, num):
        fname = f"chapter-{num:02d}.md"
        fpath = MANUSCRIPT / fname
        if not fpath.exists():
            return self.serve_json({"num": num, "content": "", "exists": False})
        content = _read_file_safe(fpath)
        return self.serve_json({"num": num, "content": content, "exists": True, "filename": fname})

    def serve_chapter_metadata(self, num):
        chapters = load_json(PLANNING / "chapter-status.json")
        key = f"chapter_{num}"
        ch = chapters.get(key, {})
        return self.serve_json({
            "num": num,
            "title": ch.get("title", ""),
            "status": ch.get("status", "not_started"),
            "hook_type": ch.get("hook_type"),
            "system_option": ch.get("system_option"),
            "parent_child_phase": ch.get("parent_child_phase"),
            "volume": ch.get("volume", 0),
            "volume_phase": ch.get("volume_phase", ""),
            "foreshadowing_buried": ch.get("foreshadowing_buried", []),
            "foreshadowing_resolved": ch.get("foreshadowing_resolved", []),
            "issue_ids": ch.get("issue_ids", []),
            "chinese_chars": ch.get("chinese_chars", 0),
            "words_estimated": ch.get("words_estimated", 0)
        })

    # ──── save helpers ────

    def save_chapter(self, num, body):
        try:
            data = json.loads(body.decode("utf-8"))
            content = data.get("content", "")
            fname = f"chapter-{num:02d}.md"
            fpath = MANUSCRIPT / fname
            MANUSCRIPT.mkdir(parents=True, exist_ok=True)
            _write_file_safe(fpath, content)
            return self.serve_json({"ok": True, "filename": fname, "chars": len(content.replace("\n","").replace(" ",""))})
        except Exception as e:
            self.send_error(500, str(e))

    def save_chapter_metadata(self, num, body):
        try:
            data = json.loads(body.decode("utf-8"))
            chapters = load_json(PLANNING / "chapter-status.json")
            key = f"chapter_{num}"
            if key not in chapters:
                chapters[key] = {}
            ch = chapters[key]
            for field in ("title", "status", "hook_type", "system_option", "parent_child_phase", "volume_phase"):
                if field in data:
                    ch[field] = data[field]
            if "volume" in data:
                ch["volume"] = data["volume"]
            for field in ("foreshadowing_buried", "foreshadowing_resolved", "issue_ids"):
                if field in data:
                    ch[field] = data[field]
            # update char count from file
            fname = f"chapter-{num:02d}.md"
            fpath = MANUSCRIPT / fname
            if fpath.exists():
                content = _read_file_safe(fpath)
                ch["chinese_chars"] = len(content.replace("\n", "").replace(" ", ""))
                ch["file_exists"] = True
            chapters[key] = ch
            save_json(PLANNING / "chapter-status.json", chapters)
            return self.serve_json({"ok": True, "chapter": {key: ch}})
        except Exception as e:
            self.send_error(500, str(e))

    def save_chapter_status(self, body):
        try:
            data = json.loads(body.decode("utf-8"))
            save_json(PLANNING / "chapter-status.json", data)
            return self.serve_json({"ok": True})
        except Exception as e:
            self.send_error(500, str(e))

    def save_plot_progress(self, body):
        try:
            data = json.loads(body.decode("utf-8"))
            save_json(PLANNING / "plot-progress.json", data)
            return self.serve_json({"ok": True})
        except Exception as e:
            self.send_error(500, str(e))

    def save_foreshadowing(self, body):
        try:
            data = json.loads(body.decode("utf-8"))
            existing = load_json(PLANNING / "foreshadow-tracking.json")
            threads = existing.get("threads", [])
            incoming = data.get("threads", data.get("thread", None))
            if isinstance(incoming, dict):
                # single thread upsert
                idx = next((i for i, t in enumerate(threads) if t.get("id") == incoming.get("id")), None)
                incoming["updated_at"] = NOW
                if "created_at" not in incoming or not incoming["created_at"]:
                    incoming["created_at"] = NOW
                if idx is not None:
                    threads[idx] = incoming
                else:
                    threads.append(incoming)
            elif isinstance(incoming, list):
                threads = incoming
            save_json(PLANNING / "foreshadow-tracking.json", {"threads": threads})
            return self.serve_json({"ok": True})
        except Exception as e:
            self.send_error(500, str(e))

    def delete_foreshadowing(self, fid):
        try:
            existing = load_json(PLANNING / "foreshadow-tracking.json")
            threads = [t for t in existing.get("threads", []) if t.get("id") != fid]
            save_json(PLANNING / "foreshadow-tracking.json", {"threads": threads})
            return self.serve_json({"ok": True})
        except Exception as e:
            self.send_error(500, str(e))

    def save_issues(self, body):
        try:
            data = json.loads(body.decode("utf-8"))
            existing = load_json(PLANNING / "issue-tracker.json")
            issues = existing.get("issues", [])
            incoming = data.get("issues", data.get("issue", None))
            if isinstance(incoming, dict):
                idx = next((i for i, t in enumerate(issues) if t.get("id") == incoming.get("id")), None)
                incoming["updated_at"] = NOW
                if "created_at" not in incoming or not incoming["created_at"]:
                    incoming["created_at"] = NOW
                if idx is not None:
                    issues[idx] = incoming
                else:
                    issues.append(incoming)
            elif isinstance(incoming, list):
                issues = incoming
            save_json(PLANNING / "issue-tracker.json", {"issues": issues})
            return self.serve_json({"ok": True})
        except Exception as e:
            self.send_error(500, str(e))

    def resolve_issue(self, iid):
        try:
            existing = load_json(PLANNING / "issue-tracker.json")
            for issue in existing.get("issues", []):
                if issue.get("id") == iid:
                    issue["status"] = "resolved"
                    issue["resolved_at"] = NOW
            save_json(PLANNING / "issue-tracker.json", existing)
            return self.serve_json({"ok": True})
        except Exception as e:
            self.send_error(500, str(e))

    def delete_issue(self, iid):
        try:
            existing = load_json(PLANNING / "issue-tracker.json")
            issues = [t for t in existing.get("issues", []) if t.get("id") != iid]
            save_json(PLANNING / "issue-tracker.json", {"issues": issues})
            return self.serve_json({"ok": True})
        except Exception as e:
            self.send_error(500, str(e))

    # ──── reference file helpers ────

    def build_reference_list(self):
        result = {}
        for cat, dirpath in REFERENCE_DIRS.items():
            if not dirpath.exists():
                result[cat] = []
                continue
            files = []
            for f in sorted(dirpath.glob("*.md")):
                files.append({
                    "name": f.name,
                    "cat": cat,
                    "size": f.stat().st_size,
                    "path": str(f.relative_to(MAIN_PROJECT)).replace("\\", "/")
                })
            result[cat] = files
        return result

    def serve_reference_file(self, parsed):
        qs = parse_qs(parsed.query)
        cat = qs.get("cat", [""])[0]
        fname = qs.get("file", [""])[0]
        if not cat or not fname:
            self.send_error(400, "Missing cat or file param")
            return
        if cat not in REFERENCE_DIRS:
            self.send_error(404, "Unknown category")
            return
        fpath = REFERENCE_DIRS[cat] / fname
        if not fpath.exists() or not fpath.is_file():
            self.send_error(404, "File not found")
            return
        content = _read_file_safe(fpath)
        return self.serve_json({"cat": cat, "file": fname, "content": content, "exists": True})

    def save_reference_file(self, body):
        try:
            data = json.loads(body.decode("utf-8"))
            cat = data.get("cat", "")
            fname = data.get("file", "")
            content = data.get("content", "")
            if not cat or not fname:
                self.send_error(400, "Missing cat or file")
                return
            if cat not in REFERENCE_DIRS:
                self.send_error(404, "Unknown category")
                return
            fpath = REFERENCE_DIRS[cat] / fname
            REFERENCE_DIRS[cat].mkdir(parents=True, exist_ok=True)
            _write_file_safe(fpath, content)
            return self.serve_json({"ok": True})
        except Exception as e:
            self.send_error(500, str(e))

    # ──── data builders ────

    def build_status(self):
        progress = load_json(PLANNING / "plot-progress.json")
        chapters = load_json(PLANNING / "chapter-status.json")
        manuscript = get_manuscript_stats()

        total_chars = 0
        published_count = 0
        draft_count = 0
        for k, v in chapters.items():
            total_chars += v.get("chinese_chars", 0)
            if v.get("status") == "published":
                published_count += 1
            elif v.get("status") == "draft":
                draft_count += 1

        target = progress.get("total_chapters_target", 200) * 3000
        pct = round(total_chars / target * 100, 1) if target else 0

        return {
            "title": progress.get("novel_title", ""),
            "current_chapter": progress.get("current_chapter", 1),
            "current_volume": progress.get("current_volume", 1),
            "volume_title": progress.get("volume_title", ""),
            "parent_child_phase": progress.get("parent_child_phase", ""),
            "total_chars": total_chars,
            "target_chars": target,
            "progress_pct": pct,
            "published_count": published_count,
            "draft_count": draft_count,
            "total_chapters_target": progress.get("total_chapters_target", 200),
            "chapters_completed": progress.get("chapters_completed", []),
            "chapters_published": progress.get("chapters_published", []),
            "manuscript_files": manuscript.get("total_files", 0),
            "active_foreshadowing": progress.get("active_foreshadowing", []),
            "tech_lines": progress.get("tech_lines_active", []),
            "last_sync": progress.get("last_sync_time", "")
        }

    def build_chapters(self):
        chapters = load_json(PLANNING / "chapter-status.json")
        manuscript = get_manuscript_stats()
        file_map = {f["name"]: f["chars"] for f in manuscript.get("files", [])}

        result = []
        for i in range(1, 201):
            key = f"chapter_{i}"
            ch = chapters.get(key, {"status": "not_started", "title": "", "chinese_chars": 0, "words_estimated": 0, "file_exists": False})
            fname = f"chapter-{i:02d}.md"
            actual_chars = file_map.get(fname, 0)
            result.append({
                "num": i,
                "title": ch.get("title", ""),
                "status": ch.get("status", "not_started"),
                "tracked_chars": ch.get("chinese_chars", 0),
                "actual_chars": actual_chars,
                "file_exists": fname in file_map,
                "volume": ch.get("volume", 0),
                "phase": ch.get("volume_phase", ""),
                "needs_revision": ch.get("needs_revision", False),
                "issues": ch.get("issues", []),
                "hook_type": ch.get("hook_type"),
                "system_option": ch.get("system_option"),
                "parent_child_phase": ch.get("parent_child_phase"),
                "foreshadowing_buried": ch.get("foreshadowing_buried", []),
                "foreshadowing_resolved": ch.get("foreshadowing_resolved", []),
                "issue_ids": ch.get("issue_ids", [])
            })
        return result

    def log_message(self, format, *args):
        print(f"[WEB] {args[0]}")


# ═══════════════════════════════════════════════════
#  HTML + CSS + JS  (embedded single-page app v3)
# ═══════════════════════════════════════════════════

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>大秦小说 — 写作看板 v3</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#0f0f0f;color:#e0e0e0;min-height:100vh}
.header{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:14px 24px;border-bottom:2px solid #c9a84c;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
.header h1{font-size:1.4em;color:#c9a84c}
.header .sub{font-size:.8em;color:#888}
.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.controls button,.controls select{background:#2a2a3e;color:#e0e0e0;border:1px solid #444;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:.82em}
.controls button:hover{background:#3a3a5e}
.controls button.primary{background:#c9a84c;color:#0f0f0f;border-color:#c9a84c;font-weight:bold}
/* Main Navigation */
.main-nav{display:flex;gap:0;padding:0 24px;background:#12122a;border-bottom:1px solid #2a2a3e}
.nav-tab{padding:10px 22px;background:none;border:none;color:#888;cursor:pointer;font-size:.85em;border-bottom:2px solid transparent;transition:all .2s}
.nav-tab:hover{color:#ccc}
.nav-tab.active{color:#c9a84c;border-bottom-color:#c9a84c}
.nav-badge{background:#c62828;color:#fff;padding:1px 6px;border-radius:8px;font-size:.7em;margin-left:4px}
/* Panels */
.panel{display:none}
.panel.active{display:block}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;padding:16px}
.card{background:#1a1a2e;border-radius:10px;padding:16px;border:1px solid #2a2a3e}
.card h3{color:#c9a84c;font-size:.85em;margin-bottom:10px;text-transform:uppercase;letter-spacing:1px}
.big-num{font-size:2.2em;font-weight:bold;color:#fff}
.progress-bar{width:100%;height:20px;background:#2a2a3e;border-radius:10px;overflow:hidden;margin:8px 0}
.progress-fill{height:100%;background:linear-gradient(90deg,#c9a84c,#e6c95c);border-radius:10px;transition:width .5s}
.pct{text-align:right;color:#c9a84c;font-weight:bold}
.tags{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}
.tag{padding:3px 10px;border-radius:10px;font-size:.73em}
.tag-published{background:#1a3a1a;color:#4caf50}
.tag-draft{background:#3a2a0a;color:#ff9800}
.tag-not_started{background:#1a1a1a;color:#666}
.tag-active{background:#1a3a3a;color:#03a9f4}
.tag-resolved{background:#1a3a1a;color:#4caf50}
.tag-abandoned{background:#2a2a2a;color:#888}
.tag-open{background:#3a1a1a;color:#f44336}
.sev-critical{background:#c62828;color:#fff;padding:2px 8px;border-radius:4px;font-size:.73em;font-weight:bold}
.sev-major{background:#e65100;color:#fff;padding:2px 8px;border-radius:4px;font-size:.73em}
.sev-minor{background:#f9a825;color:#000;padding:2px 8px;border-radius:4px;font-size:.73em}
.sev-suggestion{background:#1565c0;color:#fff;padding:2px 8px;border-radius:4px;font-size:.73em}
.section{margin:0 16px 16px}
.section h2{color:#c9a84c;font-size:1.05em;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #2a2a3e}
.filter-bar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.filter-btn{padding:5px 12px;border-radius:14px;border:1px solid #444;background:transparent;color:#aaa;cursor:pointer;font-size:.78em}
.filter-btn.active{background:#c9a84c;color:#0f0f0f;border-color:#c9a84c}
.char-card{background:#1a1a2e;border-radius:8px;padding:12px;border:1px solid #2a2a3e}
.char-card h4{color:#c9a84c;margin-bottom:4px}
.char-card .role{color:#888;font-size:.78em}
.char-card .traits{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px}
.trait{background:#2a2a3e;padding:2px 8px;border-radius:8px;font-size:.7em}
.chapter-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(36px,1fr));gap:3px}
.ch-dot{aspect-ratio:1;border-radius:4px;cursor:pointer;transition:transform .1s;border:none}
.ch-dot:hover{transform:scale(1.4);z-index:2;outline:2px solid #fff}
.ch-published{background:#4caf50}
.ch-draft{background:#ff9800}
.ch-not_started{background:#2a2a3e}
.empty{text-align:center;color:#666;padding:40px}
.footer{text-align:center;color:#555;padding:16px;font-size:.72em}
/* Chapter table */
.chapter-table tbody tr{cursor:pointer}
.chapter-table tbody tr:hover{background:#252540}
.chapter-table{width:100%;border-collapse:collapse;font-size:.82em}
.chapter-table th{text-align:left;padding:7px 10px;color:#888;border-bottom:1px solid #2a2a3e;position:sticky;top:0;background:#1a1a2e;z-index:1}
.chapter-table td{padding:7px 10px;border-bottom:1px solid #1a1a2e}
.chapter-table .c-num{color:#c9a84c;font-weight:bold;width:45px}
/* Issue table */
.issue-table{width:100%;border-collapse:collapse;font-size:.82em}
.issue-table th{text-align:left;padding:7px 10px;color:#888;border-bottom:1px solid #2a2a3e;background:#1a1a2e}
.issue-table td{padding:7px 10px;border-bottom:1px solid #1a1a2e;vertical-align:middle}
/* Modal */
.modal-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.75);z-index:100;justify-content:center;align-items:center}
.modal-overlay.show{display:flex}
.modal{background:#1a1a2e;border-radius:12px;border:1px solid #3a3a5e;width:92vw;max-width:1000px;max-height:90vh;display:flex;flex-direction:column}
.modal-header{display:flex;justify-content:space-between;align-items:center;padding:14px 20px;border-bottom:1px solid #2a2a3e}
.modal-header h2{color:#c9a84c;font-size:1.1em}
.modal-header .close{background:none;border:none;color:#888;font-size:1.5em;cursor:pointer;padding:0 8px}
.modal-header .close:hover{color:#fff}
.modal-tabs{display:flex;gap:0;padding:0 20px;background:#12122a;border-bottom:1px solid #2a2a3e}
.modal-tab{padding:10px 20px;background:none;border:none;color:#888;cursor:pointer;font-size:.85em;border-bottom:2px solid transparent}
.modal-tab.active{color:#c9a84c;border-bottom-color:#c9a84c}
.modal-body{flex:1;overflow-y:auto;padding:16px 20px}
.modal-footer{display:flex;justify-content:flex-end;gap:10px;padding:12px 20px;border-top:1px solid #2a2a3e}
.editor-textarea{width:100%;min-height:55vh;background:#0f0f0f;color:#e0e0e0;border:1px solid #3a3a5e;border-radius:8px;padding:14px;font-family:'Cascadia Code','Fira Code',Consolas,monospace;font-size:.85em;line-height:1.7;resize:vertical}
.viewer-content{white-space:pre-wrap;line-height:1.8;font-size:.9em;color:#ccc}
.viewer-content p{margin-bottom:.8em}
.toast{position:fixed;bottom:20px;right:20px;padding:10px 20px;border-radius:8px;color:#fff;font-size:.85em;z-index:200;animation:fadeIn .3s}
.toast-ok{background:#2e7d32}
.toast-err{background:#c62828}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.chapter-info{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;font-size:.82em;color:#888}
.chapter-info span{background:#12122a;padding:4px 10px;border-radius:6px}
/* Metadata form */
.meta-form{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.meta-form label{color:#888;font-size:.78em;display:flex;flex-direction:column;gap:4px}
.meta-form label.full{grid-column:1/-1}
.meta-form input,.meta-form select,.meta-form textarea{background:#0f0f0f;color:#e0e0e0;border:1px solid #3a3a5e;padding:8px 10px;border-radius:6px;font-size:.85em;width:100%}
.meta-form textarea{min-height:60px;resize:vertical}
.meta-form .chips{display:flex;gap:4px;flex-wrap:wrap}
.meta-form .chip{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:12px;font-size:.75em;background:#2a2a3e;cursor:pointer}
.meta-form .chip.selected{background:#c9a84c;color:#0f0f0f}
.meta-form .chip .x{font-weight:bold;margin-left:2px;opacity:.6}
/* Timeline */
.timeline{position:relative;padding:20px 0;margin:16px 0;overflow-x:auto}
.timeline-line{position:relative;height:8px;background:#2a2a3e;border-radius:4px;min-width:600px}
.timeline-dot{position:absolute;top:-6px;width:20px;height:20px;border-radius:50%;cursor:pointer;transition:transform .15s}
.timeline-dot:hover{transform:scale(1.5);z-index:2;outline:2px solid #fff}
.timeline-labels{display:flex;justify-content:space-between;min-width:600px;margin-top:8px;font-size:.65em;color:#666}
/* Inline form */
.inline-form{background:#12122a;border:1px solid #2a2a3e;border-radius:10px;padding:16px;margin-bottom:14px}
.inline-form h4{color:#c9a84c;margin-bottom:10px}
.inline-form .row{display:flex;gap:10px;margin-bottom:8px;flex-wrap:wrap}
.inline-form .row label{color:#888;font-size:.78em;display:flex;flex-direction:column;gap:3px}
.inline-form input,.inline-form select,.inline-form textarea{background:#0f0f0f;color:#e0e0e0;border:1px solid #3a3a5e;padding:7px 10px;border-radius:6px;font-size:.82em}
.inline-form textarea{min-height:50px;resize:vertical;width:100%}
.inline-form .actions{display:flex;gap:6px;margin-top:10px}
/* Button styles */
.btn-sm{padding:4px 12px;border-radius:4px;border:1px solid #444;background:#2a2a3e;color:#e0e0e0;cursor:pointer;font-size:.75em}
.btn-sm:hover{background:#3a3a5e}
.btn-sm.active{background:#c9a84c;color:#0f0f0f;border-color:#c9a84c}
.btn-sm.danger{background:#5a1a1a;border-color:#c62828;color:#f44336}
.btn-sm.danger:hover{background:#7a2a2a}
.btn-sm.ok{background:#1a3a1a;border-color:#388e3c;color:#4caf50}
.btn-sm.ok:hover{background:#2a4a2a}
/* Foreshadowing cards */
.fw-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-top:12px}
.fw-card{background:#1a1a2e;border-radius:8px;padding:14px;border:1px solid #2a2a3e}
.fw-card h4{color:#c9a84c;font-size:.9em;margin-bottom:4px}
.fw-card .desc{color:#aaa;font-size:.78em;margin-bottom:6px}
.fw-card .meta{display:flex;gap:12px;font-size:.73em;color:#888;flex-wrap:wrap}
.fw-card .actions{display:flex;gap:6px;margin-top:8px}
@media(max-width:600px){.grid{grid-template-columns:1fr;padding:10px}.header{padding:12px 14px}.modal{width:98vw}.meta-form{grid-template-columns:1fr}}
/* Reference panel */
.ref-layout{display:flex;gap:0;height:calc(100vh - 200px);min-height:500px}
.ref-sidebar{width:240px;min-width:180px;background:#12122a;border-right:1px solid #2a2a3e;overflow-y:auto;padding:8px 0}
.ref-cat{margin-bottom:12px}
.ref-cat-title{color:#c9a84c;font-size:.75em;font-weight:bold;padding:8px 16px 4px;text-transform:uppercase;letter-spacing:1px}
.ref-file{display:block;width:100%;text-align:left;padding:6px 16px 6px 24px;background:none;border:none;color:#aaa;cursor:pointer;font-size:.78em;transition:all .15s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ref-file:hover{background:#1a1a3e;color:#fff}
.ref-file.active{background:#1a1a4e;color:#c9a84c;border-left:2px solid #c9a84c}
.ref-main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.ref-toolbar{display:flex;justify-content:space-between;align-items:center;padding:8px 16px;background:#12122a;border-bottom:1px solid #2a2a3e;gap:10px;flex-shrink:0}
.ref-toolbar .fname{color:#c9a84c;font-size:.85em;font-weight:bold}
.ref-content{flex:1;overflow-y:auto;padding:20px 24px;font-size:.88em;line-height:1.85;color:#ccc}
.ref-content h1{color:#c9a84c;font-size:1.6em;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #2a2a3e}
.ref-content h2{color:#c9a84c;font-size:1.25em;margin:24px 0 10px}
.ref-content h3{color:#ddd;font-size:1.05em;margin:18px 0 8px}
.ref-content strong{color:#fff}
.ref-content code{background:#0f0f0f;padding:2px 6px;border-radius:3px;font-size:.88em;color:#e6c95c}
.ref-content table{width:100%;border-collapse:collapse;margin:12px 0;font-size:.82em}
.ref-content th{text-align:left;padding:8px 10px;background:#12122a;color:#c9a84c;border:1px solid #2a2a3e}
.ref-content td{padding:7px 10px;border:1px solid #2a2a3e;vertical-align:top}
.ref-content ul,.ref-content ol{padding-left:20px;margin:8px 0}
.ref-content li{margin:3px 0}
.ref-content hr{border:none;border-top:1px solid #2a2a3e;margin:20px 0}
.ref-content blockquote{border-left:3px solid #c9a84c;padding:4px 14px;margin:10px 0;color:#aaa;background:#12122a;border-radius:0 6px 6px 0}
.ref-content a{color:#c9a84c}
.ref-editor{width:100%;height:100%;background:#0f0f0f;color:#e0e0e0;border:none;padding:16px;font-family:'Cascadia Code','Fira Code',Consolas,monospace;font-size:.82em;line-height:1.7;resize:none}
.empty-state{display:flex;align-items:center;justify-content:center;height:100%;color:#555;font-size:.95em}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>大秦小说写作看板</h1>
    <span class="sub" id="subtitle">加载中...</span>
  </div>
  <div class="controls">
    <select id="volumeFilter" onchange="renderChapters()"><option value="0">全部卷</option></select>
    <select id="statusFilter" onchange="renderChapters()">
      <option value="all">全部状态</option>
      <option value="published">已发布</option>
      <option value="draft">草稿</option>
      <option value="not_started">未开始</option>
    </select>
    <button onclick="refresh()">刷新</button>
    <button class="primary" onclick="openChapter(currentEditNum||26)">写新章</button>
    <label style="display:flex;align-items:center;gap:4px;font-size:.78em;color:#888">
      <input type="checkbox" id="autoRefresh"> 自动(30s)
    </label>
  </div>
</div>

<!-- Main Navigation -->
<div class="main-nav">
  <button class="nav-tab active" id="navChapters" onclick="switchMainTab('chapters')">章节管理</button>
  <button class="nav-tab" id="navForeshadowing" onclick="switchMainTab('foreshadowing')">伏笔追踪 <span class="nav-badge" id="fwBadge" style="display:none"></span></button>
  <button class="nav-tab" id="navIssues" onclick="switchMainTab('issues')">问题跟踪 <span class="nav-badge" id="issBadge" style="display:none"></span></button>
  <button class="nav-tab" id="navChars" onclick="switchMainTab('chars')">角色速览</button>
  <button class="nav-tab" id="navRefs" onclick="switchMainTab('refs')">大纲与参考</button>
</div>

<!-- Panel: 章节管理 -->
<div class="panel active" id="panelChapters">
  <div class="grid" id="cards"></div>
  <div class="section">
    <h2>全部章节 (200章) — 点击行或色块查看/编辑</h2>
    <div id="chapterDots" style="margin-bottom:10px"></div>
    <div class="filter-bar" id="filterBar"></div>
    <div style="max-height:450px;overflow-y:auto;border-radius:8px">
      <table class="chapter-table">
        <thead><tr><th>#</th><th>标题</th><th>状态</th><th>字数</th><th>卷</th><th>阶段</th></tr></thead>
        <tbody id="chapterBody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- Panel: 伏笔追踪 -->
<div class="panel" id="panelForeshadowing">
  <div class="section">
    <h2>伏笔时间线</h2>
    <div class="timeline" id="fwTimeline"></div>
    <div class="filter-bar">
      <button class="filter-btn active" onclick="filterForeshadowing('all',this)">全部</button>
      <button class="filter-btn" onclick="filterForeshadowing('active',this)">活跃</button>
      <button class="filter-btn" onclick="filterForeshadowing('resolved',this)">已回收</button>
      <button class="filter-btn" onclick="filterForeshadowing('abandoned',this)">已放弃</button>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <span style="color:#888;font-size:.82em" id="fwCount"></span>
      <button class="btn-sm ok" onclick="showFwForm()">+ 新增伏笔</button>
    </div>
    <div id="fwFormContainer"></div>
    <div class="fw-cards" id="fwCards"></div>
  </div>
</div>

<!-- Panel: 问题跟踪 -->
<div class="panel" id="panelIssues">
  <div class="section">
    <div class="filter-bar">
      <button class="filter-btn active" onclick="filterIssues('all',this)">全部</button>
      <button class="filter-btn" onclick="filterIssues('open',this)">待解决</button>
      <button class="filter-btn" onclick="filterIssues('resolved',this)">已解决</button>
      <button class="filter-btn" onclick="filterIssues('critical',this)" style="color:#f44336">严重</button>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <span style="color:#888;font-size:.82em" id="issCount"></span>
      <button class="btn-sm ok" onclick="showIssueForm()">+ 新增问题</button>
    </div>
    <div id="issFormContainer"></div>
    <div style="max-height:500px;overflow-y:auto;border-radius:8px">
      <table class="issue-table">
        <thead><tr><th>ID</th><th>标题</th><th>严重度</th><th>分类</th><th>章节</th><th>操作</th></tr></thead>
        <tbody id="issBody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- Panel: 角色速览 -->
<div class="panel" id="panelChars">
  <div class="section">
    <h2>核心角色</h2>
    <div class="grid" id="charGrid" style="grid-template-columns:repeat(auto-fill,minmax(220px,1fr))"></div>
  </div>
</div>

<!-- Panel: 大纲与参考 -->
<div class="panel" id="panelRefs">
  <div class="ref-layout">
    <div class="ref-sidebar" id="refSidebar">
      <div class="empty-state" style="height:auto;padding:20px">加载中...</div>
    </div>
    <div class="ref-main">
      <div class="ref-toolbar" id="refToolbar" style="display:none">
        <span class="fname" id="refFname"></span>
        <div style="display:flex;gap:6px">
          <button class="btn-sm" id="btnRefView" onclick="switchRefMode('view')">阅读</button>
          <button class="btn-sm" id="btnRefEdit" onclick="switchRefMode('edit')">编辑</button>
          <button class="btn-sm ok" id="btnRefSave" style="display:none" onclick="saveRef()">保存</button>
        </div>
      </div>
      <div style="flex:1;overflow:hidden">
        <div class="ref-content" id="refViewer"></div>
        <textarea class="ref-editor" id="refEditor" style="display:none" placeholder="编辑内容..."></textarea>
        <div class="empty-state" id="refEmpty">← 从左侧选择文件查看/编辑</div>
      </div>
    </div>
  </div>
</div>

<div class="footer">Web Dashboard v3 · 章节管理 | 伏笔追踪 | 问题跟踪 | 大纲与参考 | Ctrl+S 保存</div>

<!-- ──── Chapter Detail Modal ──── -->
<div class="modal-overlay" id="modalOverlay">
  <div class="modal">
    <div class="modal-header">
      <h2 id="modalTitle">第26章</h2>
      <button class="close" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-tabs">
      <button class="modal-tab active" id="tabView" onclick="switchTab('view')">阅读</button>
      <button class="modal-tab" id="tabEdit" onclick="switchTab('edit')">编辑</button>
      <button class="modal-tab" id="tabMeta" onclick="switchTab('meta')">元数据</button>
    </div>
    <div class="modal-body">
      <div class="chapter-info" id="chapterInfo"></div>
      <div id="viewPanel" class="viewer-content">加载中...</div>
      <textarea id="editPanel" class="editor-textarea" style="display:none" placeholder="在此编写章节内容..."></textarea>
      <div id="metaPanel" style="display:none">
        <form class="meta-form" id="metaForm">
          <label>标题 <input type="text" id="metaTitle"></label>
          <label>状态 <select id="metaStatus"></select></label>
          <label>钩子类型 <select id="metaHookType"><option value="">无</option></select></label>
          <label>系统选项 <select id="metaSysOption"><option value="">无</option></select></label>
          <label>父子阶段 <select id="metaPhase"><option value="">无</option></select></label>
          <label>卷 <input type="number" id="metaVolume" min="1" max="8"></label>
          <label>卷阶段 <select id="metaVolPhase"><option value="">无</option></select></label>
          <label class="full">伏笔埋设 <div class="chips" id="metaFwBuried"></div></label>
          <label class="full">伏笔回收 <div class="chips" id="metaFwResolved"></div></label>
          <label class="full">关联问题 <div class="chips" id="metaIssues"></div></label>
        </form>
      </div>
    </div>
    <div class="modal-footer">
      <span style="color:#888;font-size:.78em;margin-right:auto" id="saveStatus"></span>
      <button onclick="closeModal()">关闭</button>
      <button class="primary" id="btnSaveMeta" style="display:none" onclick="saveMetadata()">保存元数据</button>
      <button class="primary" id="btnSaveContent" onclick="saveChapter()">保存 (Ctrl+S)</button>
    </div>
  </div>
</div>

<script>
// ═══════════ Global State ═══════════
let allChapters=[], autoTimer=null, currentEditNum=null, currentTab='view', mainTab='chapters';
let allForeshadowing=[], allIssues=[], config={}, refFiles={};
let fwFilter='all', issFilter='all', currentRefCat=null, currentRefFile=null, refMode='view';

// ═══════════ Data Fetching ═══════════
async function refresh(){
  try{
    const [st,ch,chars,fw,iss,cfg] = await Promise.all([
      fetch('/api/status').then(r=>r.json()),
      fetch('/api/chapters').then(r=>r.json()),
      fetch('/api/characters').then(r=>r.json()),
      fetch('/api/foreshadowing').then(r=>r.json()),
      fetch('/api/issues').then(r=>r.json()),
      fetch('/api/config').then(r=>r.json())
    ]);
    allChapters=ch; allForeshadowing=fw.threads||[]; allIssues=iss.issues||[]; config=cfg;
    renderStatus(st); renderChapters(); renderChars(chars);
    renderForeshadowing(); renderIssues();
    navBadges();
    document.getElementById('subtitle').textContent=
      `卷${st.current_volume}「${st.volume_title}」· ${st.parent_child_phase} · 第${st.current_chapter}章`;
    document.title=`大秦看板 · ${st.progress_pct}%`;
  }catch(e){console.error(e);}
}

// ═══════════ Status Cards ═══════════
function renderStatus(s){
  document.getElementById('cards').innerHTML=`
  <div class="card"><h3>总进度</h3><div class="big-num">${s.progress_pct}%</div>
    <div class="progress-bar"><div class="progress-fill" style="width:${Math.min(s.progress_pct,100)}%"></div></div>
    <div class="pct">${(s.total_chars||0).toLocaleString()} / ${(s.target_chars||0).toLocaleString()} 字</div></div>
  <div class="card"><h3>章节</h3><div class="big-num">${s.chapters_completed.length} <span style="font-size:.5em;color:#888">/ ${s.total_chapters_target}</span></div>
    <div class="tags"><span class="tag tag-published">已发布 ${s.published_count}</span><span class="tag tag-draft">草稿 ${s.draft_count}</span><span class="tag tag-not_started">待写 ${s.total_chapters_target-s.chapters_completed.length}</span></div></div>
  <div class="card"><h3>当前位置</h3><div style="font-size:1.2em;margin:8px 0">第 <b>${s.current_chapter}</b> 章</div>
    <div style="color:#888">卷${s.current_volume}「${s.volume_title}」</div><div style="color:#c9a84c;margin-top:6px">${s.parent_child_phase}</div></div>
  <div class="card"><h3>活跃伏笔 & 科技线</h3>
    <div class="tags">${(s.active_foreshadowing||[]).map(f=>`<span class="tag tag-draft">${f}</span>`).join('')}</div>
    <div class="tags" style="margin-top:8px">${(s.tech_lines||[]).map(t=>`<span class="trait">${t}</span>`).join('')}</div></div>`;

  const vols=[...new Set(allChapters.map(c=>c.volume).filter(v=>v>0))].sort();
  document.getElementById('volumeFilter').innerHTML='<option value="0">全部卷</option>'+vols.map(v=>`<option value="${v}">卷${v}</option>`).join('');

  let dots='<div class="chapter-grid">';
  for(const c of allChapters){
    const cls=c.status==='published'?'ch-published':c.status==='draft'?'ch-draft':'ch-not_started';
    dots+=`<button class="ch-dot ${cls}" onclick="openChapter(${c.num})" title="第${c.num}章 ${c.title||''} (${c.actual_chars||0}字)"></button>`;
  }
  dots+='</div>';
  document.getElementById('chapterDots').innerHTML=dots;
}

// ═══════════ Chapter Table ═══════════
function renderChapters(){
  const vol=parseInt(document.getElementById('volumeFilter').value);
  const status=document.getElementById('statusFilter').value;
  let filtered=allChapters;
  if(vol>0) filtered=filtered.filter(c=>c.volume===vol);
  if(status!=='all') filtered=filtered.filter(c=>c.status===status);
  const sl={'published':'已发布','draft':'草稿','not_started':'未开始'};
  const sc={'published':'tag-published','draft':'tag-draft','not_started':'tag-not_started'};

  document.getElementById('chapterBody').innerHTML=filtered.map(c=>{
    let extra='';
    if(c.needs_revision) extra+=`<span class="sev-critical" style="margin-left:4px">!</span>`;
    const hasIssues=c.issue_ids&&c.issue_ids.length>0;
    return `<tr onclick="openChapter(${c.num})">
      <td class="c-num">${c.num}</td><td>${c.title||'—'}${hasIssues?`<span class="nav-badge" style="vertical-align:middle">${c.issue_ids.length}</span>`:''}${extra}</td>
      <td><span class="tag ${sc[c.status]||'tag-not_started'}">${sl[c.status]||c.status}</span></td>
      <td>${c.actual_chars>0?c.actual_chars.toLocaleString():'—'}</td>
      <td>${c.volume||'—'}</td><td>${c.phase||'—'}</td></tr>`;
  }).join('');

  const counts={all:allChapters.length,published:0,draft:0,not_started:0};
  allChapters.forEach(c=>{if(counts[c.status]!==undefined)counts[c.status]++});
  document.getElementById('filterBar').innerHTML=['all','published','draft','not_started'].map(s=>
    `<button class="filter-btn ${status===s?'active':''}" onclick="document.getElementById('statusFilter').value='${s}';renderChapters()">${sl[s]||'全部'} (${counts[s]})</button>`
  ).join('');
}

// ═══════════ Characters ═══════════
function renderChars(data){
  const core=data.core_characters||{};
  let html='';
  if(data.protagonist&&data.protagonist.name){
    const p=data.protagonist;
    html+=`<div class="char-card"><h4>${p.name} <span style="color:#c9a84c;font-size:.75em">主角</span></h4>
      <div class="role">${(p.identity||{}).current_title||''}</div>
      <div style="color:#aaa;font-size:.78em;margin-top:4px">${p.current_status||''}</div>
      <div class="traits">${(p.personality||[]).map(t=>`<span class="trait">${t}</span>`).join('')}</div></div>`;
  }
  for(const [name,info] of Object.entries(core)){
    html+=`<div class="char-card"><h4>${name}</h4><div class="role">${info.role||''}</div>
      <div style="color:#aaa;font-size:.78em;margin-top:4px">${info.current_status||info.status||''}</div>
      <div class="traits">${(info.personality||[]).map(t=>`<span class="trait">${t}</span>`).join('')}</div></div>`;
  }
  document.getElementById('charGrid').innerHTML=html||'<div class="empty">暂无角色数据</div>';
}

// ═══════════ Main Tab Switching ═══════════
function switchMainTab(tab){
  mainTab=tab;
  ['chapters','foreshadowing','issues','chars','refs'].forEach(t=>{
    const navId='nav'+t.charAt(0).toUpperCase()+t.slice(1);
    const panelId='panel'+t.charAt(0).toUpperCase()+t.slice(1);
    const navEl=document.getElementById(navId);
    const panelEl=document.getElementById(panelId);
    if(navEl) navEl.classList.toggle('active',t===tab);
    if(panelEl) panelEl.classList.toggle('active',t===tab);
  });
  if(tab==='foreshadowing') renderForeshadowing();
  if(tab==='issues') renderIssues();
  if(tab==='chars'&&allChapters.length) renderCharsFromCache();
  if(tab==='refs') initRefs();
}

function renderCharsFromCache(){
  fetch('/api/characters').then(r=>r.json()).then(renderChars);
}

function navBadges(){
  const activeFw=allForeshadowing.filter(t=>t.status==='active').length;
  const openIss=allIssues.filter(t=>t.status==='open').length;
  const fwBadge=document.getElementById('fwBadge');
  const issBadge=document.getElementById('issBadge');
  if(activeFw>0){fwBadge.style.display='inline';fwBadge.textContent=activeFw}
  else fwBadge.style.display='none';
  if(openIss>0){issBadge.style.display='inline';issBadge.textContent=openIss}
  else issBadge.style.display='none';
}

// ═══════════ Foreshadowing Panel ═══════════
function renderForeshadowing(){
  let threads=allForeshadowing;
  if(fwFilter!=='all') threads=threads.filter(t=>t.status===fwFilter);
  document.getElementById('fwCount').textContent=`${threads.length} 条伏笔`;
  renderFwTimeline();
  renderFwCards(threads);
}

function renderFwTimeline(){
  const maxCh=200;
  let dots='';
  for(const t of allForeshadowing){
    const ch=t.buried_chapter||1;
    const pct=(ch/maxCh*100);
    const color=t.status==='resolved'?'#4caf50':t.status==='abandoned'?'#888':'#03a9f4';
    dots+=`<div class="timeline-dot" style="left:${pct}%;background:${color}" title="${t.id} ${t.name} (第${ch}章埋伏)"></div>`;
  }
  let labels='';
  for(let i=0;i<=200;i+=25) labels+=`<span>${i===0?1:i}章</span>`;
  document.getElementById('fwTimeline').innerHTML=`
    <div class="timeline-line">${dots}</div>
    <div class="timeline-labels">${labels}</div>`;
}

function renderFwCards(threads){
  if(threads.length===0){
    document.getElementById('fwCards').innerHTML='<div class="empty">暂无伏笔数据</div>';
    return;
  }
  const statusLabels={active:'活跃',resolved:'已回收',abandoned:'已放弃'};
  const statusCls={active:'tag-active',resolved:'tag-resolved',abandoned:'tag-abandoned'};
  document.getElementById('fwCards').innerHTML=threads.map(t=>`
    <div class="fw-card">
      <h4>${t.id} ${t.name}</h4>
      <div class="desc">${t.description||''}</div>
      <div class="meta">
        <span>埋伏: 第${t.buried_chapter}章</span>
        <span>计划回收: 第${t.planned_recovery_chapter}章</span>
        ${t.actual_recovery_chapter?`<span>实际回收: 第${t.actual_recovery_chapter}章</span>`:''}
        <span class="tag ${statusCls[t.status]||'tag-abandoned'}">${statusLabels[t.status]||t.status}</span>
      </div>
      ${t.related_characters&&t.related_characters.length?`<div class="tags">${t.related_characters.map(c=>`<span class="trait">${c}</span>`).join('')}</div>`:''}
      <div class="actions">
        <button class="btn-sm" onclick="editFw('${t.id}')">编辑</button>
        <button class="btn-sm danger" onclick="deleteFw('${t.id}')">删除</button>
      </div>
    </div>`).join('');
}

function filterForeshadowing(f,btn){
  fwFilter=f;
  document.querySelectorAll('#panelForeshadowing .filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderForeshadowing();
}

function showFwForm(editId){
  const existing=editId?allForeshadowing.find(t=>t.id===editId):null;
  const nextId=editId?existing.id:'F-'+String(allForeshadowing.length+1).padStart(3,'0');
  const container=document.getElementById('fwFormContainer');
  container.innerHTML=`
    <div class="inline-form">
      <h4>${editId?'编辑伏笔 '+editId:'新增伏笔'}</h4>
      <div class="row">
        <label>ID <input id="fwId" value="${nextId}" style="width:80px"></label>
        <label>名称 <input id="fwName" value="${existing?existing.name:''}" style="width:180px"></label>
        <label>状态 <select id="fwStatus">${(config.foreshadowing_statuses||['active','resolved','abandoned']).map(s=>`<option value="${s}" ${existing&&existing.status===s?'selected':''}>${s==='active'?'活跃':s==='resolved'?'已回收':'已放弃'}</option>`).join('')}</select></label>
      </div>
      <div class="row">
        <label>描述 <input id="fwDesc" value="${existing?existing.description||'':''}" style="flex:1"></label>
      </div>
      <div class="row">
        <label>埋伏章节 <input id="fwBuried" type="number" min="1" max="200" value="${existing?existing.buried_chapter:''}" style="width:80px"></label>
        <label>计划回收章节 <input id="fwPlanned" type="number" min="1" max="200" value="${existing?existing.planned_recovery_chapter:''}" style="width:80px"></label>
        <label>实际回收章节 <input id="fwActual" type="number" min="1" max="200" value="${existing?existing.actual_recovery_chapter||'':''}" style="width:80px"></label>
      </div>
      <div class="row">
        <label>关联角色 <input id="fwChars" value="${existing&&existing.related_characters?existing.related_characters.join(','):''}" placeholder="逗号分隔" style="flex:1"></label>
      </div>
      <div class="row">
        <label>备注 <textarea id="fwNotes">${existing?existing.notes||'':''}</textarea></label>
      </div>
      <div class="actions">
        <button class="btn-sm ok" onclick="saveFw()">保存</button>
        <button class="btn-sm" onclick="document.getElementById('fwFormContainer').innerHTML=''">取消</button>
      </div>
    </div>`;
}

function editFw(id){showFwForm(id);}

async function saveFw(){
  const thread={
    id:document.getElementById('fwId').value.trim(),
    name:document.getElementById('fwName').value.trim(),
    description:document.getElementById('fwDesc').value.trim(),
    status:document.getElementById('fwStatus').value,
    buried_chapter:parseInt(document.getElementById('fwBuried').value)||null,
    planned_recovery_chapter:parseInt(document.getElementById('fwPlanned').value)||null,
    actual_recovery_chapter:parseInt(document.getElementById('fwActual').value)||null,
    related_characters:document.getElementById('fwChars').value.split(',').map(s=>s.trim()).filter(Boolean),
    notes:document.getElementById('fwNotes').value.trim()
  };
  try{
    const res=await fetch('/api/foreshadowing',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({thread})});
    const data=await res.json();
    if(data.ok){
      showToast('伏笔已保存','ok');
      document.getElementById('fwFormContainer').innerHTML='';
      const fw=await fetch('/api/foreshadowing').then(r=>r.json());
      allForeshadowing=fw.threads||[];
      renderForeshadowing(); navBadges();
    }
  }catch(e){showToast('保存失败','err');}
}

async function deleteFw(id){
  if(!confirm(`确定删除伏笔 ${id}？`)) return;
  try{
    await fetch(`/api/foreshadowing/${encodeURIComponent(id)}/delete`,{method:'POST'});
    allForeshadowing=allForeshadowing.filter(t=>t.id!==id);
    renderForeshadowing(); navBadges();
    showToast(`伏笔 ${id} 已删除`,'ok');
  }catch(e){showToast('删除失败','err');}
}

// ═══════════ Issue Tracker Panel ═══════════
function renderIssues(){
  let issues=allIssues;
  if(issFilter==='open') issues=issues.filter(t=>t.status==='open');
  else if(issFilter==='resolved') issues=issues.filter(t=>t.status==='resolved');
  else if(issFilter==='critical') issues=issues.filter(t=>t.severity==='critical'&&t.status==='open');

  document.getElementById('issCount').textContent=`${issues.length} 个问题`;
  const sevLabels={critical:'严重',major:'重要',minor:'轻微',suggestion:'建议'};
  const sevCls={critical:'sev-critical',major:'sev-major',minor:'sev-minor',suggestion:'sev-suggestion'};
  const statusLabels={open:'待解决',resolved:'已解决'};

  document.getElementById('issBody').innerHTML=issues.map(t=>`
    <tr>
      <td style="color:#888;font-size:.78em">${t.id}</td>
      <td><b>${t.title}</b>${t.description?`<div style="color:#888;font-size:.73em;margin-top:2px">${t.description}</div>`:''}</td>
      <td><span class="${sevCls[t.severity]||'sev-suggestion'}">${sevLabels[t.severity]||t.severity}</span></td>
      <td style="font-size:.78em">${t.category||'—'}</td>
      <td style="font-size:.78em">${(t.affected_chapters||[]).map(c=>`第${c}章`).join(', ')}</td>
      <td>
        ${t.status==='open'?`<button class="btn-sm ok" onclick="resolveIssue('${t.id}')">解决</button>`:`<span style="color:#4caf50;font-size:.78em">已解决</span>`}
        <button class="btn-sm danger" onclick="deleteIssue('${t.id}')">删</button>
      </td>
    </tr>`).join('')||'<tr><td colspan="6" class="empty">暂无问题</td></tr>';
}

function filterIssues(f,btn){
  issFilter=f;
  document.querySelectorAll('#panelIssues .filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderIssues();
}

function showIssueForm(editId){
  const existing=editId?allIssues.find(t=>t.id===editId):null;
  const nextId=editId?existing.id:'I-'+String(allIssues.length+1).padStart(3,'0');
  const container=document.getElementById('issFormContainer');
  container.innerHTML=`
    <div class="inline-form">
      <h4>${editId?'编辑问题 '+editId:'新增问题'}</h4>
      <div class="row">
        <label>ID <input id="issId" value="${nextId}" style="width:80px"></label>
        <label>标题 <input id="issTitle" value="${existing?existing.title:''}" style="width:200px"></label>
        <label>严重度 <select id="issSeverity">${(config.issue_severities||['critical','major','minor','suggestion']).map(s=>`<option value="${s}" ${existing&&existing.severity===s?'selected':''}>${s}</option>`).join('')}</select></label>
        <label>分类 <select id="issCategory">${(config.issue_categories||[]).map(s=>`<option value="${s}" ${existing&&existing.category===s?'selected':''}>${s}</option>`).join('')}</select></label>
      </div>
      <div class="row">
        <label>描述 <input id="issDesc" value="${existing?existing.description||'':''}" style="flex:1"></label>
      </div>
      <div class="row">
        <label>关联章节 <input id="issChapters" value="${existing&&existing.affected_chapters?existing.affected_chapters.join(','):''}" placeholder="逗号分隔,如: 21,22" style="width:200px"></label>
      </div>
      <div class="actions">
        <button class="btn-sm ok" onclick="saveIssue()">保存</button>
        <button class="btn-sm" onclick="document.getElementById('issFormContainer').innerHTML=''">取消</button>
      </div>
    </div>`;
}

async function saveIssue(){
  const issue={
    id:document.getElementById('issId').value.trim(),
    title:document.getElementById('issTitle').value.trim(),
    description:document.getElementById('issDesc').value.trim(),
    severity:document.getElementById('issSeverity').value,
    category:document.getElementById('issCategory').value,
    status:'open',
    affected_chapters:document.getElementById('issChapters').value.split(',').map(s=>parseInt(s.trim())).filter(Boolean),
    resolution:'',
    tags:[]
  };
  try{
    const res=await fetch('/api/issues',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({issue})});
    const data=await res.json();
    if(data.ok){
      showToast('问题已保存','ok');
      document.getElementById('issFormContainer').innerHTML='';
      const iss=await fetch('/api/issues').then(r=>r.json());
      allIssues=iss.issues||[];
      renderIssues(); navBadges();
    }
  }catch(e){showToast('保存失败','err');}
}

async function resolveIssue(id){
  try{await fetch(`/api/issues/${encodeURIComponent(id)}/resolve`,{method:'POST'});}
  catch(e){}
  const iss=await fetch('/api/issues').then(r=>r.json());
  allIssues=iss.issues||[];
  renderIssues(); navBadges();
  showToast(`问题 ${id} 已解决`,'ok');
}

async function deleteIssue(id){
  if(!confirm(`确定删除问题 ${id}？`)) return;
  try{await fetch(`/api/issues/${encodeURIComponent(id)}/delete`,{method:'POST'});}
  catch(e){}
  allIssues=allIssues.filter(t=>t.id!==id);
  renderIssues(); navBadges();
  showToast(`问题 ${id} 已删除`,'ok');
}

// ═══════════ Reference Panel ═══════════
async function initRefs(){
  if(Object.keys(refFiles).length===0) await loadRefList();
}

async function loadRefList(){
  try{
    const r=await fetch('/api/reference-files');
    refFiles=await r.json();
  }catch(e){refFiles={};}
  renderRefSidebar();
}

function renderRefSidebar(){
  const cats=Object.keys(refFiles);
  if(cats.length===0){
    document.getElementById('refSidebar').innerHTML='<div class="empty-state" style="height:auto;padding:20px">未找到参考文件</div>';
    return;
  }
  let html='';
  for(const [cat,files] of Object.entries(refFiles)){
    html+=`<div class="ref-cat"><div class="ref-cat-title">${cat} (${files.length})</div>`;
    for(const f of files){
      const isActive=currentRefCat===cat&&currentRefFile===f.name;
      html+=`<button class="ref-file${isActive?' active':''}" onclick="openRef('${cat}','${f.name}')" title="${f.name}">${f.name.replace('.md','')}</button>`;
    }
    html+='</div>';
  }
  document.getElementById('refSidebar').innerHTML=html;
}

async function openRef(cat,file){
  currentRefCat=cat; currentRefFile=file; refMode='view';
  renderRefSidebar();
  document.getElementById('refToolbar').style.display='flex';
  document.getElementById('refFname').textContent=`${cat} / ${file}`;
  document.getElementById('refEmpty').style.display='none';
  document.getElementById('refViewer').style.display='block';
  document.getElementById('refEditor').style.display='none';
  document.getElementById('btnRefSave').style.display='none';
  document.getElementById('btnRefView').classList.add('active');
  document.getElementById('btnRefEdit').classList.remove('active');
  document.getElementById('refViewer').innerHTML='<span style="color:#888">加载中...</span>';
  try{
    const r=await fetch(`/api/reference?cat=${encodeURIComponent(cat)}&file=${encodeURIComponent(file)}`);
    const d=await r.json();
    if(d.exists){
      document.getElementById('refViewer').innerHTML=renderMarkdown(d.content);
      document.getElementById('refEditor').value=d.content;
    }
  }catch(e){
    document.getElementById('refViewer').innerHTML=`<span style="color:#f44336">加载失败: ${e}</span>`;
  }
}

function switchRefMode(mode){
  refMode=mode;
  const isView=mode==='view';
  document.getElementById('refViewer').style.display=isView?'block':'none';
  document.getElementById('refEditor').style.display=isView?'none':'block';
  document.getElementById('btnRefSave').style.display=isView?'none':'inline-block';
  document.getElementById('btnRefView').classList.toggle('active',isView);
  document.getElementById('btnRefEdit').classList.toggle('active',!isView);
  if(!isView) document.getElementById('refEditor').focus();
}

async function saveRef(){
  if(!currentRefCat||!currentRefFile) return;
  const content=document.getElementById('refEditor').value;
  try{
    const r=await fetch('/api/reference',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({cat:currentRefCat,file:currentRefFile,content})
    });
    const d=await r.json();
    if(d.ok){
      showToast('已保存','ok');
      document.getElementById('refViewer').innerHTML=renderMarkdown(content);
      switchRefMode('view');
    }else{showToast('保存失败','err');}
  }catch(e){showToast('网络错误','err');}
}

function renderMarkdown(text){
  let html=text;
  // Escape HTML
  html=html.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  // Headers
  html=html.replace(/^#### (.+)$/gm,'<h4>$1</h4>');
  html=html.replace(/^### (.+)$/gm,'<h3>$1</h3>');
  html=html.replace(/^## (.+)$/gm,'<h2>$1</h2>');
  html=html.replace(/^# (.+)$/gm,'<h1>$1</h1>');
  // Bold/italic
  html=html.replace(/\*\*\*(.+?)\*\*\*/g,'<strong><em>$1</em></strong>');
  html=html.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  html=html.replace(/\*(.+?)\*/g,'<em>$1</em>');
  // Inline code
  html=html.replace(/`([^`]+)`/g,'<code>$1</code>');
  // Horizontal rules
  html=html.replace(/^---$/gm,'<hr>');
  // Blockquotes
  html=html.replace(/^&gt; (.+)$/gm,'<blockquote>$1</blockquote>');
  // Unordered lists
  html=html.replace(/^- (.+)$/gm,'<li>$1</li>');
  html=html.replace(/((?:<li>.*<\/li>\n?)+)/g,'<ul>$1</ul>');
  // Tables - simple pipe table support
  html=html.replace(/^\|(.+)\|$/gm,function(m){
    const cells=m.slice(1,-1).split('|').map(c=>c.trim());
    const tag=cells[0].match(/^[-:]+$/)&&cells.every(c=>c.match(/^[-:]+$/))?'th':'td';
    return '<tr>'+cells.map(c=>`<${tag}>${c}</${tag}>`).join('')+'</tr>';
  });
  html=html.replace(/((?:<tr>.*<\/tr>\n?)+)/g,'<table>$1</table>');
  // Paragraphs: wrap remaining text blocks
  const lines=html.split('\n');
  let out=[], buf=[];
  for(const line of lines){
    if(line.match(/^<(h[1-4]|table|ul|hr|blockquote|tr|li)/)||line.trim()===''){
      if(buf.length){out.push('<p>'+buf.join('<br>')+'</p>');buf=[];}
      out.push(line);
    }else{buf.push(line);}
  }
  if(buf.length) out.push('<p>'+buf.join('<br>')+'</p>');
  return out.join('\n');
}

// ═══════════ Chapter Modal ═══════════
async function openChapter(num){
  currentEditNum=num;
  document.getElementById('modalTitle').textContent=`第${num}章`;
  document.getElementById('modalOverlay').classList.add('show');
  switchTab('view');

  const info=allChapters.find(c=>c.num===num);
  document.getElementById('chapterInfo').innerHTML=info?`
    <span>状态: ${info.status}</span><span>字数: ${(info.actual_chars||0).toLocaleString()}</span>
    <span>卷${info.volume||'?'} · ${info.phase||''}</span>
    ${info.needs_revision?`<span style="color:#f44336">需修订</span>`:''}
    ${info.hook_type?`<span>钩子: ${info.hook_type}</span>`:''}
  `:'';

  document.getElementById('viewPanel').textContent='加载中...';
  try{
    const res=await fetch(`/api/chapter/${num}`);
    const data=await res.json();
    if(data.exists){
      document.getElementById('viewPanel').textContent=data.content;
      document.getElementById('editPanel').value=data.content;
    }else{
      document.getElementById('viewPanel').textContent='（章节文件尚未创建，切换到「编辑」标签开始写作）';
      document.getElementById('editPanel').value='';
    }
  }catch(e){
    document.getElementById('viewPanel').textContent='加载失败: '+e;
  }
  // Load metadata
  try{
    const mr=await fetch(`/api/chapter-metadata/${num}`);
    const md=await mr.json();
    populateMetadata(md);
  }catch(e){}
}

function closeModal(){
  document.getElementById('modalOverlay').classList.remove('show');
}

function switchTab(tab){
  currentTab=tab;
  document.getElementById('tabView').classList.toggle('active',tab==='view');
  document.getElementById('tabEdit').classList.toggle('active',tab==='edit');
  document.getElementById('tabMeta').classList.toggle('active',tab==='meta');
  document.getElementById('viewPanel').style.display=tab==='view'?'block':'none';
  document.getElementById('editPanel').style.display=tab==='edit'?'block':'none';
  document.getElementById('metaPanel').style.display=tab==='meta'?'block':'none';
  document.getElementById('btnSaveContent').style.display=tab==='meta'?'none':'block';
  document.getElementById('btnSaveMeta').style.display=tab==='meta'?'block':'none';
}

// ═══════════ Metadata Form ═══════════
function populateMetadata(md){
  document.getElementById('metaTitle').value=md.title||'';
  // Status dropdown
  const statuses=config.chapter_statuses||['not_started','draft','published'];
  const statusLabels={'not_started':'未开始','draft':'草稿','published':'已发布'};
  document.getElementById('metaStatus').innerHTML=statuses.map(s=>`<option value="${s}" ${md.status===s?'selected':''}>${statusLabels[s]||s}</option>`).join('');
  // Hook type
  const hooks=(config.hook_types||[]);
  document.getElementById('metaHookType').innerHTML='<option value="">无</option>'+hooks.map(h=>`<option value="${h}" ${md.hook_type===h?'selected':''}>${h}</option>`).join('');
  // System option
  const sysOpts=config.system_option_types||['basic','high_risk','hidden'];
  document.getElementById('metaSysOption').innerHTML='<option value="">无</option>'+sysOpts.map(s=>`<option value="${s}" ${md.system_option===s?'selected':''}>${s}</option>`).join('');
  // Parent child phase
  const phases=config.parent_child_phases||[];
  document.getElementById('metaPhase').innerHTML='<option value="">无</option>'+phases.map(p=>`<option value="${p}" ${md.parent_child_phase===p?'selected':''}>${p}</option>`).join('');
  // Volume
  document.getElementById('metaVolume').value=md.volume||'';
  // Volume phase
  const vphases=config.volume_phases||[];
  document.getElementById('metaVolPhase').innerHTML='<option value="">无</option>'+vphases.map(p=>`<option value="${p}" ${md.volume_phase===p?'selected':''}>${p}</option>`).join('');
  // Foreshadowing chips
  const fwBuried=md.foreshadowing_buried||[];
  document.getElementById('metaFwBuried').innerHTML=allForeshadowing.map(f=>{
    const sel=fwBuried.includes(f.id);
    return `<span class="chip ${sel?'selected':''}" id="chipBuried_${f.id}" onclick="toggleChip('buried','${f.id}')">${f.id} ${f.name}</span>`;
  }).join('')||'<span style="color:#666;font-size:.75em">无伏笔可选</span>';
  const fwResolved=md.foreshadowing_resolved||[];
  document.getElementById('metaFwResolved').innerHTML=allForeshadowing.map(f=>{
    const sel=fwResolved.includes(f.id);
    return `<span class="chip ${sel?'selected':''}" id="chipResolved_${f.id}" onclick="toggleChip('resolved','${f.id}')">${f.id} ${f.name}</span>`;
  }).join('')||'<span style="color:#666;font-size:.75em">无伏笔可选</span>';
  // Issue chips
  const issIds=md.issue_ids||[];
  document.getElementById('metaIssues').innerHTML=allIssues.map(i=>{
    const sel=issIds.includes(i.id);
    return `<span class="chip ${sel?'selected':''}" id="chipIssue_${i.id}" onclick="toggleChip('issue','${i.id}')">${i.id} ${i.title}</span>`;
  }).join('')||'<span style="color:#666;font-size:.75em">无问题可选</span>';
}

// Track multi-select changes
let metaSelected={buried:[],resolved:[],issue:[]};
function toggleChip(type,id){
  const arr=metaSelected[type];
  const idx=arr.indexOf(id);
  if(idx>-1) arr.splice(idx,1); else arr.push(id);
  const chip=document.getElementById(`chip${type==='buried'?'Buried':type==='resolved'?'Resolved':'Issue'}_${id}`);
  if(chip) chip.classList.toggle('selected',idx===-1);
}

async function saveMetadata(){
  const num=currentEditNum;
  const data={
    title:document.getElementById('metaTitle').value.trim(),
    status:document.getElementById('metaStatus').value,
    hook_type:document.getElementById('metaHookType').value||null,
    system_option:document.getElementById('metaSysOption').value||null,
    parent_child_phase:document.getElementById('metaPhase').value||null,
    volume:parseInt(document.getElementById('metaVolume').value)||0,
    volume_phase:document.getElementById('metaVolPhase').value||null,
    foreshadowing_buried:metaSelected.buried,
    foreshadowing_resolved:metaSelected.resolved,
    issue_ids:metaSelected.issue
  };
  try{
    const res=await fetch(`/api/chapter-metadata/${num}`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(data)
    });
    const d=await res.json();
    if(d.ok){
      showToast('元数据已保存','ok');
      setTimeout(refresh,500);
      // update local chapter
      const ch=allChapters.find(c=>c.num===num);
      if(ch){
        Object.assign(ch,data);
        renderChapters();
      }
    }else{showToast('保存失败','err');}
  }catch(e){showToast('网络错误','err');}
}

// ═══════════ Save Chapter Content ═══════════
async function saveChapter(){
  const content=document.getElementById('editPanel').value;
  document.getElementById('saveStatus').textContent='保存中...';
  try{
    const res=await fetch(`/api/chapter/${currentEditNum}`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({content})
    });
    const data=await res.json();
    if(data.ok){
      document.getElementById('saveStatus').textContent=`已保存 (${data.chars.toLocaleString()} 字)`;
      showToast('保存成功','ok');
      document.getElementById('viewPanel').textContent=content;
      setTimeout(refresh,500);
    }else{
      document.getElementById('saveStatus').textContent='保存失败';
      showToast('保存失败','err');
    }
  }catch(e){
    document.getElementById('saveStatus').textContent='错误: '+e;
    showToast('网络错误','err');
  }
}

// ═══════════ Utilities ═══════════
function showToast(msg,type){
  const t=document.createElement('div');
  t.className='toast toast-'+type;
  t.textContent=msg;
  document.body.appendChild(t);
  setTimeout(()=>t.remove(),2000);
}

// Keyboard shortcuts
document.addEventListener('keydown',e=>{
  if(e.ctrlKey&&e.key==='s'){
    e.preventDefault();
    if(document.getElementById('modalOverlay').classList.contains('show')){
      if(currentTab==='meta') saveMetadata();
      else if(currentTab==='edit') saveChapter();
    }else if(mainTab==='refs'&&refMode==='edit'){
      saveRef();
    }
  }
  if(e.key==='Escape') closeModal();
});

document.getElementById('autoRefresh').addEventListener('change',function(){
  if(this.checked){autoTimer=setInterval(refresh,30000);}
  else{clearInterval(autoTimer);}
});

// Initialize metadata tracking
document.addEventListener('click',function(e){
  // Reset metaSelected when opening new chapter (handled in populateMetadata)
});
// Override populateMetadata to also reset metaSelected
const origPopulateMetadata=populateMetadata;
populateMetadata=function(md){
  metaSelected={
    buried:[...(md.foreshadowing_buried||[])],
    resolved:[...(md.foreshadowing_resolved||[])],
    issue:[...(md.issue_ids||[])]
  };
  origPopulateMetadata(md);
};

refresh();
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Novel Writing Web Dashboard v3")
    parser.add_argument("--port", "-p", type=int, default=8080, help="HTTP port (default: 8080)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)
    server = HTTPServer((args.host, args.port), DashboardHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║   大秦小说 Web 写作看板 v3                ║
║                                              ║
║   -> 浏览器访问: http://{args.host}:{args.port}       ║
║                                              ║
║   功能: 进度看板 | 章节管理 | 元数据编辑     ║
║        伏笔追踪 | 问题跟踪 | 角色速览       ║
║   按 Ctrl+C 停止服务                          ║
╚══════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[WEB] 看板已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
