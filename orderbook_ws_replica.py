import aiohttp
import asyncio
import ujson
from tabulate import tabulate
from copy import deepcopy

# Pairs which generate orderbook for.
PAIRS = [
        'BTCUSD',
        'ETCBTC',
        # 'ETCUSD',
        # 'ETHBTC',
        # 'ETHUSD',
        # 'XMRBTC',
        # 'XMRUSD',
        # 'ZECBTC',
        # 'ZECUSD'
    ]

# If there is n pairs we need to subscribe to n websocket channels.
# This the subscription message template.
# For details about settings refer to https://bitfinex.readme.io/v2/reference#ws-public-order-books.
SUB_MESG = {
        'event': 'subscribe',
        'channel': 'book',
        'freq': 'F1',
        'len': '25',
        'prec': 'P0'
        # 'pair': <pair>
    }


def build_book(res, pair):
    """ Updates orderbook.
    :param res: Orderbook update message.
    :param pair: Updated pair.
    
    """

    global orderbooks

    # Filter out subscription status messages.
    if res.data[0] == '[':

        # String to json
        data = ujson.loads(res.data)[1]

        # Build orderbook
        # Observe the structure of orderbook. The prices are keys for corresponding count and amount.
        # Structuring data in this way significantly simplifies orderbook updates.
        if len(data) > 10:
            bids = {
                       str(level[0]): [str(level[1]), str(level[2])]
                       for level in data if level[2] > 0
            }

            asks = {
                       str(level[0]): [str(level[1]), str(level[2])[1:]]
                       for level in data if level[2] < 0
            }

            orderbooks[pair]['bids'] = bids
            orderbooks[pair]['asks'] = asks

        # Update orderbook and filter out heartbeat messages.
        elif data[0] != 'h':

            # Example update message structure [1765.2, 0, 1] where we have [price, count, amount].
            # Update algorithm pseudocode from Bitfinex documentation:
            # 1. - When count > 0 then you have to add or update the price level.
            #   1.1- If amount > 0 then add/update bids.
            #   1.2- If amount < 0 then add/update asks.
            # 2. - When count = 0 then you have to delete the price level.
            #   2.1- If amount = 1 then remove from bids
            #   2.2- If amount = -1 then remove from asks

            data = [str(data[0]), str(data[1]), str(data[2])]
            if int(data[1]) > 0:  # 1.

                if float(data[2]) > 0:  # 1.1
                    orderbooks[pair]['bids'].update({data[0]: [data[1], data[2]]})

                elif float(data[2]) < 0:  # 1.2
                    orderbooks[pair]['asks'].update({data[0]: [data[1], str(data[2])[1:]]})

            elif data[1] == '0':  # 2.

                if data[2] == '1':  # 2.1
                    if orderbooks[pair]['bids'].get(data[0]):
                        del orderbooks[pair]['bids'][data[0]]

                elif data[2] == '-1':  # 2.2
                    if orderbooks[pair]['asks'].get(data[0]):
                        del orderbooks[pair]['asks'][data[0]]

async def print_books():
    """ Prints orderbooks snapshots for all pairs every 10 seconds. """
    global orderbooks
    while 1:
        await asyncio.sleep(10)
        for pair in PAIRS:
            bids = [[v[1], v[0], k] for k, v in orderbooks[pair]['bids'].items()]
            asks = [[k, v[0], v[1]] for k, v in orderbooks[pair]['asks'].items()]
            bids.sort(key=lambda x: float(x[2]), reverse=True)
            asks.sort(key=lambda x: float(x[0]))
            table = [[*bid, *ask] for (bid, ask) in zip(bids, asks)]
            headers = ['bid:amount', 'bid:count', 'bid:price', 'ask:price', 'ask:count', 'ask:amount']
            print('orderbook for {}'.format(pair))
            print(tabulate(table, headers=headers))


async def get_book(pair, session):
    """ Subscribes for orderbook updates and fetches updates. """
    print('enter get_book, pair: {}'.format(pair))
    pair_dict = deepcopy(SUB_MESG)
    pair_dict.update({'pair': pair})
    async with session.ws_connect('wss://api.bitfinex.com/ws/2') as ws:
        ws.send_json(pair_dict)
        while 1:
            res = await ws.receive()
            # print(pair_dict['pair'], res.data)  # debug
            build_book(res, pair)

async def main():
    """ Driver coroutine. """
    async with aiohttp.ClientSession() as session:
        coros = [
            get_book(pair, session)
            for pair in PAIRS
        ]
        # Append coroutine for printing orderbook snapshots every 10s.
        coros.append(print_books())

        await asyncio.wait(coros)

orderbooks = {
    pair: {}
    for pair in PAIRS
}
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
