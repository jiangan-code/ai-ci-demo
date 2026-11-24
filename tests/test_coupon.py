from shop.coupon import Coupon


def test_percent_off():
    assert Coupon("SAVE10", percent_off=10).apply(100_00) == 90_00


def test_amount_off_never_goes_negative():
    assert Coupon("BIG", amount_off_cents=50_00).apply(30_00) == 0


def test_label():
    assert Coupon("A", percent_off=10).label() == "9 折券"
    assert Coupon("B", amount_off_cents=5_00).label() == "立减 5 元"
    assert Coupon("C").label() == "无优惠"
