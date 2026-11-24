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

    def label(self) -> str:
        """给用户看的券名，比如「9 折券」「立减 5 元」。"""
        parts = []
        if self.percent_off:
            parts.append(f"{(100 - self.percent_off) / 10:g} 折券")
        if self.amount_off_cents:
            parts.append(f"立减 {self.amount_off_cents / 100:g} 元")
        return " + ".join(parts) or "无优惠"
