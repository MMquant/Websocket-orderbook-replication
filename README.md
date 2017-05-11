# Websocket-orderbook-replication
Example python script replicating remote orderbook from websocket stream

This code rebuilds multiple orderbooks using asyncio coroutines. There is no waiting for blocking tasks (waiting for messages after receive() call). I’m using here the Bitfinex WS API. Program is continuously updating opted pairs orderbooks keeping them in global orderbooks instance. From there they are printed out every 10 seconds in the pretty table structured as you are used to see on exchanges platforms. But what is the point here is that we have orderbooks available in real-time in the orderbooks global variable!

The program should work out of the box but is dependent on ujson, asyncio, aiohttp and tabulate libraries.  Just run it from shell or python console and fresh orderbook will be printed periodically to stdout.

For more information and deeper code analysis visit my [blog](http://mmquant.net/replicating-orderbooks-from-websocket-stream-with-python-and-asyncio/).
