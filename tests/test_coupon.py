from shop.coupon import Coupon


def test_percent_off():
    assert Coupon("SAVE10", percent_off=10).apply(100_00) == 90_00


def test_amount_off_never_goes_negative():
    assert Coupon("BIG", amount_off_cents=50_00).apply(30_00) == 0
