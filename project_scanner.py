import datetime
import json
import os
import re
import subprocess
from typing import Dict, List, Optional
from paths import DEFAULT_PROJECTS_DIR, PROJECTS_DB_PATH

KNOWN_COMPLETED = {
    "AlgoVision", "JavaVision", "Steam-Game-Idler", "Insta-Winner-Picker",
    "Core-Portfolio", "Personal-Portfolio", "Yurei-AI", "Smart-Dictator",
    "PM-Copilot", "Arcade-Hub", "Typing Samurai", "TensorVision"
}


class ProjectScanner:
    def __init__(self, projects_dir: str = DEFAULT_PROJECTS_DIR):
        self.projects_dir = projects_dir

    def scan_all_projects(self) -> List[Dict]:
        saved_db = self._load_saved_db()
        discovered = []

        if not os.path.isdir(self.projects_dir):
            return discovered

        for entry in sorted(os.listdir(self.projects_dir)):
            full_path = os.path.join(self.projects_dir, entry)
            if not os.path.isdir(full_path):
                continue

            # Detect git info
            git_info = self._get_git_info(full_path)

            # Detect stack
            stack = self._detect_tech_stack(full_path)

            # Detect description
            desc = self._extract_readme_description(full_path)

            # Merge with saved metadata
            saved = saved_db.get(entry, {})

            # Default status heuristics
            default_status = "Completed" if entry in KNOWN_COMPLETED else "In Progress"
            default_pct = 100 if default_status == "Completed" else (70 if git_info.get("is_git") else 40)

            project_record = {
                "id": entry,
                "name": entry.replace("-", " "),
                "folder_name": entry,
                "path": full_path,
                "status": saved.get("status", default_status),
                "progress_pct": saved.get("progress_pct", default_pct),
                "priority": saved.get("priority", "Medium"),
                "notes": saved.get("notes", ""),
                "todos": saved.get("todos", self._default_todos(entry, default_status)),
                "tech_stack": stack,
                "description": desc or saved.get("description", "A local software development project."),
                "git_branch": git_info.get("branch", ""),
                "git_remote": git_info.get("remote", ""),
                "last_commit_date": git_info.get("last_commit_date", ""),
                "last_commit_msg": git_info.get("last_commit_msg", ""),
                "is_git": git_info.get("is_git", False),
                "last_modified": self._get_last_modified_date(full_path)
            }
            discovered.append(project_record)

        self._save_db({p["folder_name"]: p for p in discovered})
        return discovered

    def _default_todos(self, name: str, status: str) -> List[Dict]:
        if status == "Completed":
            return [
                {"text": "Core architecture & logic implemented", "done": True},
                {"text": "Local test build verified with 0 errors", "done": True},
                {"text": "Documentation & README created", "done": True}
            ]
        return [
            {"text": "Refine core algorithms & feature logic", "done": False},
            {"text": "Add automated unit tests & verify edge cases", "done": False},
            {"text": "Polish UI motion curves & documentation", "done": False}
        ]

    def _get_git_info(self, path: str) -> Dict:
        git_dir = os.path.join(path, ".git")
        if not os.path.isdir(git_dir):
            return {"is_git": False}

        branch = "main"
        remote = ""
        last_date = ""
        last_msg = ""

        try:
            r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=path, capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                branch = r.stdout.strip()

            r = subprocess.run(["git", "config", "--get", "remote.origin.url"], cwd=path, capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                remote = r.stdout.strip()

            r = subprocess.run(["git", "log", "-1", "--pretty=format:%ad|%s", "--date=short"], cwd=path, capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                parts = r.stdout.strip().split("|", 1)
                last_date = parts[0]
                if len(parts) > 1:
                    last_msg = parts[1]
        except Exception:
            pass

        return {
            "is_git": True,
            "branch": branch,
            "remote": remote,
            "last_commit_date": last_date,
            "last_commit_msg": last_msg
        }

    def _detect_tech_stack(self, path: str) -> List[str]:
        stack = []
        files = set(os.listdir(path)) if os.path.isdir(path) else set()

        # Web & JS/TS
        if "package.json" in files:
            stack.append("Node.js")
            try:
                with open(os.path.join(path, "package.json"), "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "react" in deps:
                    stack.append("React")
                if "typescript" in deps or "tsconfig.json" in files:
                    stack.append("TypeScript")
                if "vite" in deps:
                    stack.append("Vite")
                if "tailwindcss" in deps:
                    stack.append("Tailwind CSS")
                if "express" in deps:
                    stack.append("Express")
            except Exception:
                pass

        # Python
        has_py = any(f.endswith(".py") for f in files) or "requirements.txt" in files
        if has_py:
            stack.append("Python")
            if any("pyside" in f.lower() or "pyqt" in f.lower() for f in files):
                stack.append("PySide6 (Qt)")

        # C++
        has_cpp = any(f.endswith(".cpp") or f.endswith(".h") for f in files) or "CMakeLists.txt" in files
        if has_cpp:
            stack.append("C++")

        # Java
        has_java = any(f.endswith(".java") for f in files) or "pom.xml" in files
        if has_java:
            stack.append("Java")

        return stack or ["Software"]

    def _extract_readme_description(self, path: str) -> str:
        for fname in ("README.md", "readme.md", "README.txt"):
            fp = os.path.join(path, fname)
            if os.path.isfile(fp):
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as f:
                        lines = [l.strip() for l in f.readlines() if l.strip()]
                    for l in lines:
                        if not l.startswith("#") and not l.startswith("[!") and len(l) > 15:
                            return l[:180] + ("..." if len(l) > 180 else "")
                except Exception:
                    pass
        return ""

    def _get_last_modified_date(self, path: str) -> str:
        try:
            mtime = os.path.getmtime(path)
            return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except Exception:
            return ""

    def _load_saved_db(self) -> Dict[str, dict]:
        if os.path.isfile(PROJECTS_DB_PATH):
            try:
                with open(PROJECTS_DB_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_db(self, data: Dict[str, dict]):
        try:
            with open(PROJECTS_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving projects DB: {e}")

    def update_project(self, folder_name: str, updates: dict):
        db = self._load_saved_db()
        if folder_name in db:
            db[folder_name].update(updates)
        else:
            db[folder_name] = updates
        self._save_db(db)

    def update_metadata(self, folder_name: str, updates: dict):
        self.update_project(folder_name, updates)
