"""结算：小计 → 优惠券 → （如果开关对你打开了）满减。"""

from shop.cart import Cart
from shop.coupon import Coupon
from shop.flags import is_enabled

FULL_REDUCTION_THRESHOLD_CENTS = 100_00
FULL_REDUCTION_CENTS = 20_00
FREE_SHIPPING_CENTS = 199_00  # 满 199 包邮
SHIPPING_CENTS = 10_00  # 不满就收 10 元运费


def total_cents(cart: Cart, user_id: str, coupon: Coupon | None = None) -> int:
    total = cart.subtotal_cents()
    if coupon is not None:
        total = coupon.apply(total)
    if is_enabled("full_reduction", user_id) and total >= FULL_REDUCTION_THRESHOLD_CENTS:
        total -= FULL_REDUCTION_CENTS
    if total < FREE_SHIPPING_CENTS:
        total += SHIPPING_CENTS
    return total
