#!/usr/bin/env python3
"""Interactive CS50P check/submit center for the WSL environment."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import requests


COURSE_SLUG = "cs50/problems/2022/python"
REPO_ROOT = Path(__file__).resolve().parent.parent
PROBLEM_ROOT = REPO_ROOT / "problem_sets"
VERSION = "1.0"


@dataclass(frozen=True)
class Problem:
    week: str
    slug: str
    title: str
    files: tuple[str, ...]


PROBLEMS = (
    Problem("P0", "indoor", "Indoor Voice", ("indoor.py",)),
    Problem("P0", "playback", "Playback Speed", ("playback.py",)),
    Problem("P1", "deep", "Deep Thought", ("deep.py",)),
    Problem("P1", "einstein", "Einstein", ("einstein.py",)),
    Problem("P1", "faces", "Faces", ("faces.py",)),
    Problem("P1", "tip", "Math Interpreter", ("tip.py",)),
    Problem("P2", "camel", "camelCase", ("camel.py",)),
    Problem("P2", "coke", "Coke Machine", ("coke.py",)),
    Problem("P2", "twttr", "Just setting up my twttr", ("twttr.py",)),
    Problem("P3", "outdated", "Outdated", ("outdated.py",)),
    Problem("P3", "grocery", "Grocery List", ("grocery.py",)),
    Problem("P4", "emojize", "Emojize", ("emojize.py",)),
    Problem("P4", "figlet", "Frank, Ian and Glen's Letters", ("figlet.py",)),
    Problem("P4", "game", "Guessing Game", ("game.py",)),
    Problem("P4", "professor", "Little Professor", ("professor.py",)),
    Problem("P4", "bitcoin", "Bitcoin Price Index", ("bitcoin.py",)),
    Problem("P5", "adieu", "Adieu, Adieu", ("adieu.py",)),
    Problem("P5", "bank", "Home Federal Savings Bank", ("bank.py", "test_bank.py")),
    Problem("P5", "extensions", "File Extensions", ("extensions.py",)),
    Problem("P5", "interpreter", "Math Interpreter 2", ("interpreter.py",)),
    Problem("P5", "meal", "Meal Time", ("meal.py",)),
    Problem("P5", "plates", "Vanity Plates", ("plates.py", "test_plates.py")),
    Problem("P5", "taqueria", "Felipe's Taqueria", ("taqueria.py", "test_taqueria.py")),
    Problem("P6", "lines", "Lines of Code", ("lines.py",)),
    Problem("P6", "pizza", "CS50 Pizza", ("pizza.py",)),
    Problem("P6", "scourgify", "Scourgify", ("scourgify.py",)),
    Problem("P6", "shirt", "CS50 Shirtificate", ("shirt.py",)),
    Problem("P7", "numb3rs", "NUMB3RS", ("numb3rs.py", "test_numb3rs.py")),
    Problem("P7", "response", "Regular, um, Expressions", ("response.py",)),
    Problem("P7", "um", "Um, Again", ("um.py", "test_um.py")),
    Problem("P7", "working", "Working 9 to 5", ("working.py", "test_working.py")),
    Problem("P8", "seasons", "Seasons of Love", ("seasons.py", "test_seasons.py")),
    Problem("P8", "jar", "Cookie Jar", ("jar.py", "test_jar.py")),
    Problem("P8", "shirtificate", "CS50 Shirtificate", ("shirtificate.py",)),
    Problem("Final", "project", "Final Project", ("project.py", "test_project.py", "requirements.txt")),
)


def clear_screen() -> None:
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")


def pause() -> None:
    try:
        input("\n按 Enter 返回主菜单...")
    except (EOFError, KeyboardInterrupt):
        print()


def run(command: list[str], cwd: Path) -> int:
    print()
    print("$ " + " ".join(command))
    print()
    try:
        result = subprocess.run(command, cwd=cwd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"找不到命令：{command[0]}")
        return 127
    except KeyboardInterrupt:
        print("\n操作已取消。")
        return 130


def run_interactive(command: list[str], cwd: Path) -> int:
    return run(command, cwd)


def version_of(executable: str) -> str:
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        output = (result.stdout or result.stderr).strip()
        return output.splitlines()[0] if output else "已安装"
    except (OSError, subprocess.SubprocessError):
        return "不可用"


def validate_submit_access() -> tuple[bool, str]:
    user = os.environ.get("CS50_GH_USER", "")
    token = os.environ.get("CS50_TOKEN", "")
    if not user or not token:
        return False, "未取得 GitHub 登录信息"

    try:
        response = requests.get(
            f"https://api.github.com/repos/me50/{user}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=20,
        )
        if response.ok and response.json().get("permissions", {}).get("push"):
            return True, f"可向 me50/{user} 提交"
        if response.status_code == 404:
            return False, f"找不到 me50/{user}，请先加入 CS50 课程"
        return False, f"GitHub 返回 HTTP {response.status_code}"
    except requests.RequestException as exc:
        return False, f"GitHub 连接失败：{exc}"


def problem_directory(problem: Problem) -> Path:
    week_number = problem.week.removeprefix("P").lower()
    return PROBLEM_ROOT / f"pset{week_number}" / problem.slug


def prepare_problem(problem: Problem) -> Path:
    directory = problem_directory(problem)
    directory.mkdir(parents=True, exist_ok=True)

    for filename in problem.files:
        path = directory / filename
        if not path.exists() and filename.endswith(".py"):
            path.write_text(
                "# TODO: Complete this CS50P assignment.\n",
                encoding="utf-8",
            )

    return directory


def windows_path(path: Path) -> str:
    resolved = str(path.resolve())
    if resolved.startswith("/mnt/") and len(resolved) > 6:
        drive = resolved[5]
        return f"{drive.upper()}:\\" + resolved[7:].replace("/", "\\")
    return resolved


def find_vscode() -> Path | None:
    candidates = [
        Path("/mnt/c/Program Files/Microsoft VS Code/Code.exe"),
        Path("/mnt/c/Program Files (x86)/Microsoft VS Code/Code.exe"),
    ]
    users_root = Path("/mnt/c/Users")
    if users_root.exists():
        candidates.extend(
            users_root.glob("*/AppData/Local/Programs/Microsoft VS Code/Code.exe")
        )

    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def open_editor(directory: Path) -> None:
    editor = find_vscode()
    if editor is None:
        print("找不到 VS Code。请运行：winget install Microsoft.VisualStudioCode")
        return

    python_files = sorted(directory.glob("*.py"))
    target = python_files[0] if python_files else directory
    subprocess.Popen(
        [str(editor), "-n", windows_path(target)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"已用 VS Code 打开：{target}")


def open_folder(directory: Path) -> None:
    explorer = shutil.which("explorer.exe")
    if not explorer:
        print(f"题目目录：{directory}")
        return

    subprocess.Popen(
        [explorer, windows_path(directory)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def show_environment() -> None:
    check_status = version_of("/usr/local/bin/check50")
    submit_status = version_of("/usr/local/bin/submit50")
    access_ok, access_text = validate_submit_access()
    print(f"check50   : {check_status}")
    print(f"submit50  : {submit_status}")
    print(f"GitHub 账号: {os.environ.get('CS50_GH_USER', '未登录')}")
    print(f"提交权限  : {'正常' if access_ok else '不可用'} - {access_text}")
    print(f"作业仓库  : {REPO_ROOT}")


def select_problem() -> Problem | None:
    print("选择作业（按题集分组）：\n")
    for index, problem in enumerate(PROBLEMS, start=1):
        directory = problem_directory(problem)
        marker = "●" if directory.exists() else "○"
        print(
            f" {index:>2}. [{problem.week:>5}] {marker} "
            f"{problem.slug:<14} {problem.title}"
        )

    print("\n C. 使用自定义 CS50 slug")
    print(" 0. 返回主菜单")
    choice = input("\n输入编号：").strip()

    if choice == "0":
        return None
    if choice.lower() == "c":
        slug = input("输入题目 slug（例如 cs50/problems/2022/python/indoor）：").strip()
        if not slug:
            return None
        name = slug.rstrip("/").split("/")[-1]
        custom = Problem("Custom", name, "自定义题目", (f"{name}.py",))
        custom_dir = PROBLEM_ROOT / "custom" / name
        custom_dir.mkdir(parents=True, exist_ok=True)
        os.environ["CS50_CUSTOM_SLUG"] = slug
        return custom

    try:
        selected = int(choice)
    except ValueError:
        print("请输入列表中的编号。")
        pause()
        return None

    if not 1 <= selected <= len(PROBLEMS):
        print("编号超出范围。")
        pause()
        return None
    return PROBLEMS[selected - 1]


def slug_for(problem: Problem) -> str:
    if problem.week == "Custom":
        return os.environ["CS50_CUSTOM_SLUG"]
    return f"{COURSE_SLUG}/{problem.slug}"


def selected_directory(problem: Problem) -> Path:
    if problem.week == "Custom":
        return PROBLEM_ROOT / "custom" / problem.slug
    return prepare_problem(problem)


def check_problem(problem: Problem) -> None:
    directory = selected_directory(problem)
    python_files = sorted(directory.glob("*.py"))
    if not python_files:
        print(f"\n目录中还没有 Python 文件：{directory}")
        print("请先在编辑器里创建并完成作业。")
        pause()
        return

    print(f"\n题目目录：{directory}")
    print("将运行：check50 " + slug_for(problem))
    run_interactive(["/usr/local/bin/check50", slug_for(problem)], directory)
    pause()


def submit_problem(problem: Problem) -> None:
    directory = selected_directory(problem)
    print(f"\n题目目录：{directory}")
    print("即将调用 CS50 官方 submit50。")
    answer = input("确认提交这个作业吗？(yes/no): ").strip().lower()
    if answer not in {"y", "yes"}:
        print("已取消提交。")
        pause()
        return

    ok, detail = validate_submit_access()
    if not ok:
        print(f"\n无法提交：{detail}")
        pause()
        return

    run_interactive(["/usr/local/bin/submit50", slug_for(problem)], directory)
    pause()


def run_problem(problem: Problem) -> None:
    directory = selected_directory(problem)
    python_files = sorted(directory.glob("*.py"))
    if not python_files:
        print(f"\n还没有可运行的文件。题目目录：{directory}")
        pause()
        return

    for index, file in enumerate(python_files, start=1):
        print(f"{index}. {file.name}")
    choice = input("选择要运行的文件（Enter 运行第一项）：").strip()
    try:
        selected = python_files[0] if not choice else python_files[int(choice) - 1]
    except (ValueError, IndexError):
        print("选择无效。")
        pause()
        return

    run_interactive(["/opt/cs50p-venv/bin/python", str(selected)], directory)
    pause()


def sync_github() -> None:
    git = shutil.which("git.exe") or shutil.which("git")
    if not git:
        print("找不到 Git。")
        pause()
        return

    print()
    subprocess.run([git, "status", "--short", "--branch"], cwd=REPO_ROOT, check=False)
    changed = subprocess.run(
        [git, "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if not changed:
        print("\n没有需要保存的新改动。")
        pause()
        return

    message = input("\n提交说明（Enter 使用默认说明）：").strip()
    if not message:
        message = "Update CS50P assignments"

    for command in (
        [git, "add", "-A"],
        [git, "commit", "-m", message],
        [git, "push"],
    ):
        result = run(command, REPO_ROOT)
        if result != 0:
            print("\n同步中断，请查看上方错误。")
            pause()
            return
    print("\n已保存并推送到 GitHub。")
    pause()


def main_menu() -> None:
    while True:
        clear_screen()
        access_ok, access_detail = validate_submit_access()
        print("=" * 66)
        print(" CS50P 作业中心")
        print("=" * 66)
        print(f" 仓库：{REPO_ROOT}")
        print(f" check50：{version_of('/usr/local/bin/check50')}")
        print(f" submit50：{version_of('/usr/local/bin/submit50')}")
        print(f" 提交状态：{'就绪' if access_ok else '需处理'}（{access_detail}）")
        print("-" * 66)
        print(" 1. 检查作业（check50）")
        print(" 2. 提交作业（submit50）")
        print(" 3. 运行作业程序")
        print(" 4. 编写作业代码（VS Code）")
        print(" 5. 在文件资源管理器中打开作业目录")
        print(" 6. 保存并同步到 GitHub")
        print(" 7. 查看环境状态")
        print(" 0. 退出")
        choice = input("\n请选择操作：").strip()

        if choice == "0":
            return
        if choice == "7":
            clear_screen()
            show_environment()
            pause()
            continue
        if choice == "6":
            clear_screen()
            sync_github()
            continue
        if choice not in {"1", "2", "3", "4", "5"}:
            continue

        clear_screen()
        problem = select_problem()
        if problem is None:
            continue

        if choice == "1":
            check_problem(problem)
        elif choice == "2":
            submit_problem(problem)
        elif choice == "3":
            run_problem(problem)
        elif choice == "4":
            directory = selected_directory(problem)
            open_editor(directory)
            pause()
        else:
            directory = selected_directory(problem)
            print(f"已准备题目目录：{directory}")
            open_folder(directory)
            pause()


def self_test() -> int:
    print("CS50P environment self-test")
    show_environment()

    failures = []
    if version_of("/usr/local/bin/check50") == "不可用":
        failures.append("check50")
    if version_of("/usr/local/bin/submit50") == "不可用":
        failures.append("submit50")
    access_ok, detail = validate_submit_access()
    if not access_ok:
        failures.append(detail)

    if failures:
        print("\nFAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nAll core checks passed.")
    return 0


if __name__ == "__main__":
    try:
        if "--self-test" in sys.argv:
            raise SystemExit(self_test())
        main_menu()
    except (EOFError, KeyboardInterrupt):
        print("\n已退出 CS50P 作业中心。")
