# AI 时代的 CI 怎么拆：跟练仓库

这是我（Captain）给视频做的跟练小项目：一个很小的网店结算模块，外加一套拆好的 CI。
每一集结束时的样子都打了 tag，想回到哪一集，就 `git checkout` 到哪一集。

| 集 | tag | 内容 |
| --- | --- | --- |
| EP1 | `ep1` | 四类检查：提交前检查、PR 快检查、主分支全量测试、特性开关 + 按比例放量 |
| EP2 | `ep2` | 攒批：几个分支攒成一批，一批只开一个 PR、只跑一次重检查 |

## 准备

需要 Python 3.10 以上和 git。

```bash
git clone <仓库地址>
cd ai-ci-demo
python3 -m venv .venv
source .venv/bin/activate        # Windows 用 .venv\Scripts\activate
pip install -e ".[dev]"
```

## EP1：四类检查

我把检查分成四类，各放在不同的地方跑：

| 类 | 查什么 | 放在哪 | 这个仓库里对应的文件 |
| --- | --- | --- | --- |
| 1 | 规则：格式、代码规范 | 提交之前，你自己电脑上 | `.pre-commit-config.yaml` |
| 2 | 这次改动对不对 | 开 PR 时，只跑相关测试，限时 5 分钟 | `.github/workflows/pr-fast.yml`、`scripts/related_tests.py` |
| 3 | 主分支整体对不对 | 合进主分支之后，全量测试 | `.github/workflows/main-full.yml` |
| 4 | 能不能放给用户 | 上线以后，特性开关 + 按比例放量 | `src/shop/flags.py` |

**第 1 步：装上提交前检查**

```bash
pre-commit install
pre-commit run --all-files
```

以后每次 `git commit`，都会先自动检查格式。不合格的，它会帮你改好，你再提交一次就行。

**第 2 步：看看「只跑相关测试」**

```bash
git switch -c try-related
# 随便改一下 src/shop/coupon.py，然后：
git commit -am "改优惠券"
python scripts/related_tests.py main
```

只改了优惠券，它就只跑和优惠券有关的测试：优惠券自己的，加上用到了优惠券的结算。购物车和开关的测试不跑。

**第 3 步：全量测试（包括慢测试）**

```bash
pytest          # 全部，包括慢测试
pytest -m "not slow"   # 只跑快的
```

**第 4 步：特性开关**

`src/shop/flags.py` 里，「满 100 减 20」这个新功能只放给 5% 的用户（5 是建议的起步值，可以调）。
同一个购物车，不同的用户算出来的价格可能不一样。这就是为什么你室友有新功能，你却没有。

```bash
python -c "
from shop.cart import Cart
from shop.checkout import total_cents
cart = Cart(); cart.add('东西', 120_00)
prices = [total_cents(cart, f'user{i}') for i in range(1000)]
print('1000 个用户买同样的东西，拿到满减的有', prices.count(100_00), '个')
"
```

两个 workflow 推到 GitHub 上会自动生效：开 PR 时跑「PR 快检查」，合进 main 之后跑「主分支全量测试」。

## EP2：攒批

一个改动一个 PR，每个 PR 都要跑一趟重检查。AI 一天开几十个 PR，就要跑几十趟。
攒批就像外卖骑手顺路攒单：每个改动还是单独一个分支，只是几个分支拼成一个 PR，重检查只跑一趟。

| 步 | 做什么 | 这个仓库里对应的文件 |
| --- | --- | --- |
| 1 | 每个改动照样一个分支 | — |
| 2 | 分支推上来，先跑轻检查：规范 + 能不能编译，不跑测试 | `.github/workflows/branch-light.yml` |
| 3、4 | 过了轻检查的分支，攒成一个批次分支 `batch/N`，开一个 PR，跑重检查 | `scripts/batch.py`、`.github/workflows/batch-pr.yml` |
| 5 | 同一时间最多一个批次，上一批没合进 main，新分支等下一批 | `scripts/batch.py` |
| 6 | 批次红了，不改旧分支，加一个修复分支进这一批（向前修） | `scripts/batch.py add` |

**照着做**

```bash
# 几个做完的分支，攒成一批（有 GitHub 远程仓库会自动开 PR，需要先装好 gh 并登录）
python scripts/batch.py start feat/a feat/b feat/c

# 批次红了：从批次分支拉一个修复分支，改好以后加进同一批
git switch -c fix/xxx batch/1
# ……改代码、提交……
python scripts/batch.py add fix/xxx

# 看看当前批次里有哪些分支
python scripts/batch.py status
```

没有远程仓库也能玩：脚本会在本地跑重检查。

两种做法可以并存：分支名是 `batch/N` 的 PR 走批次重检查，其他 PR 还是走 EP1 的「PR 快检查」。

**抄之前先看** [`CHECKLIST.md`](CHECKLIST.md)：攒批的三个代价和三个问题。

