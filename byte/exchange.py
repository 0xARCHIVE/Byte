from abc import ABC, abstractmethod

from byte.orderbook import OrderBook


class Exchange(ABC):
    @abstractmethod
    def get_orderbook(self) -> OrderBook:
        ...

    @abstractmethod
    async def listen_forever(self) -> None:
        ...
