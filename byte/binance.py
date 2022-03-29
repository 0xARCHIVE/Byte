import json
from dataclasses import dataclass
from typing import Optional

import aiohttp
import websockets

from byte.exchange import Exchange
from byte.orderbook import Order, OrderBook


@dataclass
class BinanceEvent:
    first_update_id: int
    last_update_id: int
    bids: list[Order]
    asks: list[Order]


class BinanceExchange(Exchange):
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol.lower()

        self._prev_last_event_id: Optional[int] = None
        self._orderbook: OrderBook = OrderBook()

    def get_orderbook(self) -> OrderBook:
        return self._orderbook

    async def _update_orderbook(self, event: BinanceEvent) -> None:
        # create orderbook from snapshot
        if self._orderbook.last_update_id == 0:
            self._orderbook = await self._create_orderbook_from_snapshot()

        # update orderbook from event
        last_update_id: int = self._orderbook.last_update_id

        if event.first_update_id > last_update_id + 1:
            return None

        if event.last_update_id <= last_update_id:
            return None

        if (
            self._prev_last_event_id is not None
            and event.first_update_id != self._prev_last_event_id + 1
        ):
            # a problem occurred, need to reconcile (i.e. start again)
            self._orderbook = await self._create_orderbook_from_snapshot()
            self._prev_last_event_id = None
            return None

        self._prev_last_event_id = event.last_update_id
        self._update_from_event(event)

    def _update_from_event(self, event: BinanceEvent) -> None:
        self._orderbook.last_update_id = event.last_update_id

        for bid in event.bids:
            self._orderbook.add_or_update_bid(bid)

        for ask in event.asks:
            self._orderbook.add_or_update_ask(ask)

    async def _create_orderbook_from_snapshot(self) -> OrderBook:
        orderbook: OrderBook = OrderBook()
        params = {"symbol": self.symbol.upper(), "limit": 1000}
        url = "https://api.binance.com/api/v3/depth"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                json_data = await response.json()

                # build orderbook from json data (todo: validation of json)
                orderbook.last_update_id = json_data["lastUpdateId"]

                for price, quantity in json_data["bids"]:
                    order = Order(price=price, quantity=quantity)
                    orderbook.add_or_update_bid(order)

                for price, quantity in json_data["asks"]:
                    order = Order(price=price, quantity=quantity)
                    orderbook.add_or_update_ask(order)

        return orderbook

    async def listen_forever(self) -> None:
        url = f"wss://stream.binance.com:9443/ws/{self.symbol!s}@depth"
        async for websocket in websockets.connect(url):
            try:
                async for message in websocket:
                    message = json.loads(message)

                    event: BinanceEvent = BinanceEvent(
                        first_update_id=message["U"],
                        last_update_id=message["u"],
                        bids=[
                            Order(price=order[0], quantity=order[1])
                            for order in message["b"]
                        ],
                        asks=[
                            Order(price=order[0], quantity=order[1])
                            for order in message["a"]
                        ],
                    )

                    await self._update_orderbook(event)
            except websockets.ConnectionClosed:
                # something went wrong, so we will have to start again
                # when we reconnect
                self._orderbook = OrderBook()
                self._prev_last_event_id = None
