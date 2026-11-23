"""结算：小计 → 优惠券 → （如果开关对你打开了）满减。"""

from shop.cart import Cart
from shop.coupon import Coupon
from shop.flags import is_enabled

FULL_REDUCTION_THRESHOLD_CENTS = 100_00
FULL_REDUCTION_CENTS = 20_00


def total_cents(cart: Cart, user_id: str, coupon: Coupon | None = None) -> int:
    total = cart.subtotal_cents()
    if coupon is not None:
        total = coupon.apply(total)
    if is_enabled("full_reduction", user_id) and total >= FULL_REDUCTION_THRESHOLD_CENTS:
        total -= FULL_REDUCTION_CENTS
    return total
