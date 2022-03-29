from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional


@dataclass
class Order:
    price: float
    quantity: float


class OrderBook:
    def __init__(self) -> None:
        self.bids: OrderedDict[float, Order] = OrderedDict()
        self.asks: OrderedDict[float, Order] = OrderedDict()
        self.last_update_id: int = 0

    def top_ask(self) -> Optional[float]:
        return None if not self.asks else min(self.asks.keys())

    def top_bid(self) -> Optional[float]:
        return None if not self.bids else max(self.bids.keys())

    def remove_bid(self, price: float) -> None:
        self.bids.pop(price, None)

    def remove_ask(self, price: float) -> None:
        self.asks.pop(price, None)

    def add_or_update_bid(self, order: Order) -> None:
        if order.quantity == 0:
            del self.bids[order.price]
        else:
            self.bids[order.price] = order

    def add_or_update_ask(self, order: Order) -> None:
        if order.quantity == 0:
            del self.asks[order.price]
        else:
            self.asks[order.price] = order
