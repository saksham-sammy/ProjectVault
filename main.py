import argparse
import sys
from paths import DEFAULT_PROJECTS_DIR
from project_scanner import ProjectScanner


def main():
    parser = argparse.ArgumentParser(description="ProjectVault - Visual Portfolio & Project Lifecycle Hub")
    parser.add_argument("--list", action="store_true", help="List all discovered local projects with status and progress")
    args = parser.parse_args()

    scanner = ProjectScanner(DEFAULT_PROJECTS_DIR)

    if args.list:
        projects = scanner.scan_all_projects()
        print(f"\n=== ProjectVault: {len(projects)} Discovered Local Projects ===")
        for p in projects:
            print(f"- {p['name']:30s} | {p['status']:12s} ({p['progress_pct']}%) | Stack: {', '.join(p['tech_stack'][:3])}")
        sys.exit(0)

    from ui_app import run_app
    run_app()


if __name__ == "__main__":
    main()
