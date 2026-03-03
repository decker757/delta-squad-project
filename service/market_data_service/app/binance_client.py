import asyncio
import json
import logging
from typing import AsyncIterator, Dict, Any

import websockets

class BinanceBookTickerClient:
    def __init__(self, ws_url: str, reconnect_delay: float, logger: logging.Logger):
        self.ws_url = ws_url
        self.reconnect_delay = reconnect_delay
        self.logger = logger

    async def stream(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Reconnecting async generator that yields raw Binance payloads
        """
        while True:
            try:
                self.logger.info("Connecting to Binance websocket: %s", self.ws_url)
                
                async with websockets.connect(self.ws_url) as ws:
                    self.logger.info("Connected to Binance websocket")

                    async for message in ws:
                        payload = json.loads(message)
                        yield payload
            
            except asyncio.CancelledError:
                self.logger.info("Binance stream canceled")
                raise
            except Exception as exc:
                self.logger.exception("Binance websocket error: %s", exc)
                self.logger.info(
                    "Reconnecting in %.1f seconds...", self.reconnect_delay 
                )
                await asyncio.sleep(self.reconnect_delay)
