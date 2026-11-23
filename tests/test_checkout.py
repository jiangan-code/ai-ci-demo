from shop import flags
from shop.cart import Cart
from shop.checkout import total_cents


def _cart_of(cents: int) -> Cart:
    cart = Cart()
    cart.add("东西", cents)
    return cart


def test_full_reduction_when_flag_on(monkeypatch):
    monkeypatch.setitem(flags.ROLLOUT_PERCENT, "full_reduction", 100)
    assert total_cents(_cart_of(120_00), "anyone") == 100_00


def test_no_reduction_when_flag_off(monkeypatch):
    monkeypatch.setitem(flags.ROLLOUT_PERCENT, "full_reduction", 0)
    assert total_cents(_cart_of(120_00), "anyone") == 120_00


def test_same_cart_different_users_can_differ():
    """你和室友买一样的东西，价格可能不一样：开关只对一部分人打开了。"""
    results = {total_cents(_cart_of(120_00), f"user{i}") for i in range(500)}
    assert results == {100_00, 120_00}
