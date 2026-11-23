"""第 4 类检查用到的工具：特性开关 + 按比例放量。

新功能的代码可以先合进主分支、先上线，但开关只对一部分用户打开。
同一个用户每次算出来的结果都一样，所以不会一会儿有、一会儿没有。
"""

import hashlib

# 每个开关放给多少比例的用户（0–100）。
# 5 是建议的起步值，不是定死的规矩：先放一小部分人，没问题再往上调。
ROLLOUT_PERCENT: dict[str, int] = {
    "full_reduction": 5,  # 新功能：满 100 减 20
}


def bucket(flag: str, user_id: str) -> int:
    """把用户稳定地分到 0–99 号桶里。"""
    digest = hashlib.sha256(f"{flag}:{user_id}".encode()).hexdigest()
    return int(digest, 16) % 100


def is_enabled(flag: str, user_id: str) -> bool:
    return bucket(flag, user_id) < ROLLOUT_PERCENT.get(flag, 0)
