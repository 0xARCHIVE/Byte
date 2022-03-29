import asyncio

from byte.binance import BinanceExchange
from byte.exchange import Exchange
from byte.orderbook import OrderBook


async def print_top_ask_bid_forever(exchange: Exchange, delay: int) -> None:
    while True:
        orderbook: OrderBook = exchange.get_orderbook()

        await asyncio.sleep(delay)

        if orderbook.last_update_id == 0:
            continue

        top_ask = orderbook.top_ask()
        top_bid = orderbook.top_bid()

        print(f"Top ask: {top_ask!s}, top bid: {top_bid!s}")


async def main() -> None:
    exchange: Exchange = BinanceExchange("btcusdt")

    while True:
        await asyncio.gather(
            exchange.listen_forever(), print_top_ask_bid_forever(exchange, 5)
        )


if __name__ == "__main__":
    asyncio.run(main())
