import pytest

from shop.cart import Cart


def test_subtotal_adds_price_times_qty():
    cart = Cart()
    cart.add("奶茶", 15_00, qty=2)
    cart.add("面包", 8_50)
    assert cart.subtotal_cents() == 38_50


def test_empty_cart_is_zero():
    assert Cart().subtotal_cents() == 0


def test_rejects_negative_price():
    with pytest.raises(ValueError):
        Cart().add("坏数据", -1)


def test_rejects_empty_name():
    with pytest.raises(ValueError):
        Cart().add("  ", 1_00)
