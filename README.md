# AI 时代的 CI 怎么拆：跟练仓库

这是我（Captain）给视频做的跟练小项目：一个很小的网店结算模块，外加一套拆好的 CI。
每一集结束时的样子都打了 tag，想回到哪一集，就 `git checkout` 到哪一集。

| 集 | tag | 内容 |
| --- | --- | --- |
| EP1 | `ep1` | 四类检查：提交前检查、PR 快检查、主分支全量测试、特性开关 + 按比例放量 |
| EP2 | `ep2` | 攒批：几条分支攒成一个 PR（还在做） |

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
