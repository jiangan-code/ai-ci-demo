"""慢测试：模拟大量用户，检查整体规律。只在合进主分支之后的全量测试里跑。"""

import random

import pytest

from shop import flags
from shop.cart import Cart
from shop.checkout import total_cents
from shop.coupon import Coupon

USERS = 200_000


@pytest.mark.slow
def test_rollout_ratio_matches_setting():
    on = sum(flags.is_enabled("full_reduction", f"user{i}") for i in range(USERS))
    expected = flags.ROLLOUT_PERCENT["full_reduction"] / 100
    assert abs(on / USERS - expected) < 0.005


@pytest.mark.slow
def test_total_is_never_negative_or_above_subtotal():
    rng = random.Random(2026)
    coupons = [None, Coupon("A", percent_off=10), Coupon("B", amount_off_cents=30_00)]
    for i in range(USERS):
        cart = Cart()
        for _ in range(rng.randint(1, 5)):
            cart.add("x", rng.randint(0, 80_00), rng.randint(1, 3))
        total = total_cents(cart, f"user{i}", rng.choice(coupons))
        assert 0 <= total <= cart.subtotal_cents()
