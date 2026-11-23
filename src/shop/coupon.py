"""优惠券：打折券和立减券。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Coupon:
    code: str
    percent_off: int = 0  # 打几折的「折扣部分」，比如 10 表示减 10%
    amount_off_cents: int = 0  # 直接立减多少分

    def apply(self, subtotal_cents: int) -> int:
        after_percent = subtotal_cents * (100 - self.percent_off) // 100
        return max(after_percent - self.amount_off_cents, 0)
