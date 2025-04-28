import os
import time
import csv
import logging
import signal
import subprocess
from datetime import datetime
import aiohttp
import asyncio
import random
from typing import Optional

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='revenant_bot.log'
)
logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

# Configuration
PRICE_LOG_FILE = 'revenant_price_log.csv'
HEARTBEAT_INTERVAL = 3600  # 1 hour
PRICE_CHECK_INTERVAL = 60  # 1 min
API_MAX_RETRIES = 5
API_BACKOFF_FACTOR = 2  # Exponential backoff factor

class RevenantBot:
    def __init__(self):
        self.last_heartbeat = 0
        self.last_price = None
        self.running = True
        self.initialize_csv()
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Set up graceful shutdown for SIGINT and SIGTERM"""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self.shutdown_handler)
    
    def shutdown_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def initialize_csv(self):
        """Initialize the CSV file if it doesn't exist"""
        if not os.path.exists(PRICE_LOG_FILE):
            with open(PRICE_LOG_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'price', 'movement'])
            logger.info(f"Created {PRICE_LOG_FILE}")
    
    async def send_heartbeat(self):
        """Send a heartbeat message to log"""
        current_time = time.time()
        if current_time - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            logger.info("HEARTBEAT: RevenantBot is running")
            self.last_heartbeat = current_time
    
    async def get_btc_price(self) -> Optional[float]:
        """Fetch BTC price with exponential backoff retry logic"""
        url = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
        retries = 0
        
        while retries < API_MAX_RETRIES:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'result' in data and 'XXBTZUSD' in data['result']:
                                price = float(data['result']['XXBTZUSD']['c'][0])
                                return price
                            else:
                                logger.error(f"Unexpected API response format: {data}")
                        else:
                            logger.warning(f"API returned status code {response.status}")
            except aiohttp.ClientError as e:
                logger.error(f"Connection error: {e}")
            except Exception as e:
                logger.error(f"Error fetching price: {e}")
            
            retries += 1
            if retries < API_MAX_RETRIES:
                # Calculate backoff with jitter to avoid thundering herd
                backoff_time = (API_BACKOFF_FACTOR ** retries) + random.uniform(0, 1)
                logger.info(f"Retrying in {backoff_time:.2f} seconds (attempt {retries}/{API_MAX_RETRIES})")
                await asyncio.sleep(backoff_time)
        
        logger.error(f"Failed to fetch price after {API_MAX_RETRIES} attempts")
        return None
    
    def log_price(self, price: float):
        """Log the price data to CSV"""
        movement = 'initial'
        if self.last_price:
            if price > self.last_price:
                movement = 'up'
            elif price < self.last_price:
                movement = 'down'
            else:
                movement = 'same'
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with open(PRICE_LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, price, movement])
            self.last_price = price
        except IOError as e:
            logger.error(f"Failed to write to CSV: {e}")
    
    async def price_check_task(self):
        """Task for periodic price checking"""
        while self.running:
            try:
                price = await self.get_btc_price()
                if price:
                    self.log_price(price)
                    logger.info(f"Price checked: ${price:.2f}")
                await self.send_heartbeat()  # Check if heartbeat should be sent
            except Exception as e:
                logger.error(f"Error in price check task: {e}")
            
            # Sleep until next check, but do it in small increments to allow for clean shutdown
            for _ in range(PRICE_CHECK_INTERVAL):
                if not self.running:
                    break
                await asyncio.sleep(1)
    
    async def run(self):
        """Main entry point for the bot"""
        logger.info("Revenant Bot is starting...")
        self.last_heartbeat = time.time()  # Initialize heartbeat
        
        # Start main task
        try:
            await self.price_check_task()
        except asyncio.CancelledError:
            logger.info("Bot tasks cancelled")
        except Exception as e:
            logger.error(f"Unhandled exception in bot: {e}")
        finally:
            logger.info("Revenant Bot has shut down")

async def main():
    """Main entry point for the application"""
    bot = RevenantBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())