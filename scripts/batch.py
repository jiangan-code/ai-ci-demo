"""EP2：把做完的几个分支攒成一批，一批只开一个 PR，只跑一次重检查。

用法：
  python scripts/batch.py start 分支1 分支2 ...   开一个新批次（同一时间只能有一个）
  python scripts/batch.py add 分支                 往当前批次里再加一个分支（比如修复分支）
  python scripts/batch.py status                   看当前批次里有哪些分支

规矩（都是确定的，不靠猜）：
1. 每个改动照样一个分支。
2. 进批之前，先过一轮轻检查：代码规范 + 能不能编译。
3. 过了轻检查的分支，从最新的 main 拉出一个批次分支 batch/N，挨个合进去。
4. 有 GitHub 远程仓库，就推上去用 gh 开一个 PR，在 PR 上跑重检查；没有，就在本地跑重检查。
5. 同一时间最多一个批次。上一批还没合进 main，新分支就等下一批。
6. 批次红了，不改旧分支，而是从批次分支拉一个修复分支，用 add 加进这一批（向前修）。
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def git(*args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} 失败：\n{r.stderr.strip()}")
    return r.stdout.strip()


def has_remote() -> bool:
    return "origin" in git("remote").split()


def base() -> str:
    """最新的 main：有远程就用 origin/main。"""
    if has_remote():
        git("fetch", "-q", "origin")
        return "origin/main"
    return "main"


def open_batch() -> str | None:
    """还没合进 main 的批次分支，就是「进行中的批次」。"""
    b = base()
    for name in git("branch", "--format=%(refname:short)", "--list", "batch/*").split():
        if git("rev-list", "--count", f"{b}..{name}") != "0":
            return name
    return None


def next_batch_name() -> str:
    names = git("branch", "-a", "--format=%(refname:short)").split()
    nums = [
        int(n.rsplit("/", 1)[1]) for n in names if "batch/" in n and n.rsplit("/", 1)[1].isdigit()
    ]
    return f"batch/{max(nums, default=0) + 1}"


def run(cmd: list[str], cwd: Path) -> bool:
    print("  $", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd).returncode == 0


def light_check(branch: str) -> bool:
    """轻检查：只看代码规范和能不能编译，几秒钟。不跑测试。"""
    print(f"轻检查 {branch}")
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "wt"
        git("worktree", "add", "-q", "--detach", str(wt), branch)
        try:
            return (
                run([PY, "-m", "ruff", "check", "."], wt)
                and run([PY, "-m", "ruff", "format", "--check", "."], wt)
                and run([PY, "-m", "compileall", "-q", "src"], wt)
            )
        finally:
            git("worktree", "remove", "--force", str(wt))


def heavy_check() -> bool:
    """重检查（本地版）：规范 + 全部快测试。GitHub 上由 batch-pr.yml 来跑。"""
    print("本地重检查")
    return run([PY, "-m", "ruff", "check", "."], ROOT) and run(
        [PY, "-m", "pytest", "-q", "-m", "not slow"], ROOT
    )


def merge_in(batch: str, branch: str) -> bool:
    git("switch", "-q", batch)
    r = subprocess.run(
        ["git", "merge", "--no-ff", "-q", "-m", f"{batch}：合入 {branch}", branch],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        git("merge", "--abort", check=False)
        print(f"  {branch} 和这一批有冲突，先不进，留给下一批")
        return False
    print(f"  已合入 {branch}")
    return True


def branches_in(batch: str) -> list[str]:
    subjects = git("log", "--format=%s", f"{base()}..{batch}").splitlines()
    return [s.split("：合入 ", 1)[1] for s in reversed(subjects) if "：合入 " in s]


def publish(batch: str, created: bool) -> None:
    names = branches_in(batch)
    if not has_remote():
        print("没有远程仓库，在本地跑重检查")
        print("重检查：", "通过" if heavy_check() else "没通过，往这一批里加一个修复分支")
        return
    git("push", "-q", "-u", "origin", batch)
    if created:
        body = "这一批合入的分支：\n" + "\n".join(f"- {n}" for n in names)
        title = f"{batch}：{len(names)} 个改动"
        out = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                "main",
                "--head",
                batch,
                "--title",
                title,
                "--body",
                body,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        print(out.stdout.strip() or out.stderr.strip())
    else:
        print("已推送，PR 上的重检查会自动重跑")


def cmd_start(branches: list[str]) -> None:
    busy = open_batch()
    if busy:
        sys.exit(f"{busy} 还没合进 main。同一时间只能有一个批次，这些分支先等下一批。")
    ok = [b for b in branches if light_check(b)]
    for b in sorted(set(branches) - set(ok)):
        print(f"{b} 没过轻检查，先不进批")
    if not ok:
        sys.exit("没有能进批的分支")
    batch = next_batch_name()
    git("switch", "-q", "-c", batch, base())
    merged = [b for b in ok if merge_in(batch, b)]
    print(f"{batch}：{len(merged)} 个分支攒成一批")
    publish(batch, created=True)


def cmd_add(branch: str) -> None:
    batch = open_batch()
    if not batch:
        sys.exit("现在没有进行中的批次，用 start 开一个")
    if not light_check(branch):
        sys.exit(f"{branch} 没过轻检查")
    if merge_in(batch, branch):
        publish(batch, created=False)


def cmd_status() -> None:
    batch = open_batch()
    if not batch:
        print("现在没有进行中的批次")
        return
    print(batch)
    for n in branches_in(batch):
        print("  -", n)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["start"] and len(args) > 1:
        cmd_start(args[1:])
    elif args[:1] == ["add"] and len(args) == 2:
        cmd_add(args[1])
    elif args[:1] == ["status"]:
        cmd_status()
    else:
        sys.exit(__doc__)
