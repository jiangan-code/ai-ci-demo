"""购物车：放商品、算小计。金额一律用「分」存，避免小数误差。"""

from dataclasses import dataclass, field


@dataclass
class Item:
    name: str
    price_cents: int
    qty: int = 1

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("商品名不能是空的")
        if self.price_cents < 0:
            raise ValueError("价格不能是负数")
        if self.qty < 1:
            raise ValueError("数量至少是 1")


@dataclass
class Cart:
    items: list[Item] = field(default_factory=list)

    def add(self, name: str, price_cents: int, qty: int = 1) -> None:
        self.items.append(Item(name, price_cents, qty))

    def subtotal_cents(self) -> int:
        return sum(item.price_cents * item.qty for item in self.items)
