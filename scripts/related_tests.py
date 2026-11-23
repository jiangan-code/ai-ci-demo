"""第 2 类检查：只跑和这次改动有关的测试。

用法：python scripts/related_tests.py <对比的分支，比如 origin/main>

怎么判断「有关」：
- 改了 tests/ 里的测试文件 → 跑它
- 改了 src/shop/xxx.py → 找出所有直接或间接用到 shop.xxx 的模块，再跑 import 了它们的测试
  （比如改了 coupon，checkout 用到了 coupon，那 checkout 的测试也要跑）
- 改了 pyproject.toml 或 CI 配置 → 改动影响面说不清，跑全部快测试
慢测试（@pytest.mark.slow）这里一律不跑，留给主分支的全量测试。
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_ALL_TRIGGERS = ("pyproject.toml", ".github/", "scripts/")


def changed_files(base: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def imports(path: Path, module: str) -> bool:
    """这个文件有没有用到 shop.<module>（两种写法都算）。"""
    text = path.read_text(encoding="utf-8")
    direct = rf"^\s*(from|import)\s+shop\.{module}\b"
    via_package = rf"^\s*from\s+shop\s+import\s+.*\b{module}\b"
    return bool(re.search(direct, text, re.M) or re.search(via_package, text, re.M))


def affected_modules(module: str) -> set[str]:
    """改了一个模块，哪些模块会跟着受影响（包括它自己）。"""
    affected, todo = {module}, [module]
    sources = list((ROOT / "src" / "shop").glob("*.py"))
    while todo:
        current = todo.pop()
        for src in sources:
            if src.stem not in affected and imports(src, current):
                affected.add(src.stem)
                todo.append(src.stem)
    return affected


def only_slow(test: Path) -> bool:
    """整个文件里的测试都是慢测试，就不用列出来了。"""
    text = test.read_text(encoding="utf-8")
    return text.count("def test_") == text.count("@pytest.mark.slow")


def tests_for(module: str) -> set[str]:
    hits = set()
    for name in affected_modules(module):
        for test in (ROOT / "tests").glob("test_*.py"):
            if imports(test, name) and not only_slow(test):
                hits.add(str(test.relative_to(ROOT)))
    return hits


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)  # 日志按顺序打印
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    files = changed_files(base)
    print(f"和 {base} 相比，改了这些文件：", *files or ["（没有）"], sep="\n  ")

    if any(f.startswith(RUN_ALL_TRIGGERS) for f in files):
        targets = ["tests"]
        print("改到了配置或脚本，影响面说不清，跑全部快测试。")
    else:
        selected: set[str] = set()
        for f in files:
            if f.startswith("tests/test_") and (ROOT / f).exists():
                selected.add(f)
            elif f.startswith("src/shop/") and f.endswith(".py"):
                selected |= tests_for(Path(f).stem)
        targets = sorted(selected)

    if not targets:
        print("没有和这次改动相关的测试，跳过。")
        return 0

    print("要跑的测试：", *targets, sep="\n  ")
    cmd = [sys.executable, "-m", "pytest", "-m", "not slow", *targets]
    return subprocess.run(cmd, cwd=ROOT).returncode


if __name__ == "__main__":
    sys.exit(main())
