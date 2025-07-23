#!/usr/bin/env python3
"""
AI Gold Scalper - Market Data Processor
Phase 6: Production Integration & Infrastructure

Real-time market data collection, processing, and distribution system.
Handles multiple data sources, validation, and feeds processed data to AI models.
"""

import asyncio
import json
import logging
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yfinance as yf
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor
import websocket
import ssl

@dataclass
class MarketTick:
    """Market tick data structure"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: int
    high: float
    low: float
    open: float
    close: float

class DataSource:
    """Base class for market data sources"""
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority
        self.is_connected = False
        self.last_update = None
        self.error_count = 0
        self.max_errors = 5
    
    async def connect(self) -> bool:
        """Connect to data source"""
        raise NotImplementedError
    
    async def disconnect(self):
        """Disconnect from data source"""
        raise NotImplementedError
    
    async def get_tick(self, symbol: str) -> Optional[MarketTick]:
        """Get latest tick data"""
        raise NotImplementedError
    
    def is_healthy(self) -> bool:
        """Check if data source is healthy"""
        return (
            self.is_connected and 
            self.error_count < self.max_errors and
            self.last_update and
            (datetime.now() - self.last_update).seconds < 300  # 5 minutes
        )

class YahooFinanceSource(DataSource):
    """Yahoo Finance data source"""
    
    def __init__(self):
        super().__init__("YahooFinance", priority=2)
        self.session = requests.Session()
    
    async def connect(self) -> bool:
        """Connect to Yahoo Finance"""
        try:
            # Test connection
            test_data = yf.download("GC=F", period="1d", interval="1m", progress=False)
            if not test_data.empty:
                self.is_connected = True
                self.last_update = datetime.now()
                logging.info("Yahoo Finance data source connected")
                return True
        except Exception as e:
            logging.error(f"Yahoo Finance connection failed: {e}")
            self.error_count += 1
        return False
    
    async def disconnect(self):
        """Disconnect from Yahoo Finance"""
        self.is_connected = False
        self.session.close()
    
    async def get_tick(self, symbol: str) -> Optional[MarketTick]:
        """Get latest tick from Yahoo Finance"""
        try:
            # Map symbol
            yf_symbol = "GC=F" if symbol == "XAUUSD" else symbol
            
            # Get latest data
            data = yf.download(yf_symbol, period="1d", interval="1m", progress=False)
            if data.empty:
                return None
            
            latest = data.iloc[-1]
            now = datetime.now()
            
            tick = MarketTick(
                symbol=symbol,
                timestamp=now,
                bid=float(latest['Close']) - 0.1,  # Approximate bid
                ask=float(latest['Close']) + 0.1,  # Approximate ask
                last=float(latest['Close']),
                volume=int(latest['Volume']) if 'Volume' in latest else 0,
                high=float(latest['High']),
                low=float(latest['Low']),
                open=float(latest['Open']),
                close=float(latest['Close'])
            )
            
            self.last_update = now
            self.error_count = 0
            return tick
            
        except Exception as e:
            logging.error(f"Yahoo Finance tick error: {e}")
            self.error_count += 1
            return None

class AlphaVantageSource(DataSource):
    """Alpha Vantage data source"""
    
    def __init__(self, api_key: str):
        super().__init__("AlphaVantage", priority=1)
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    async def connect(self) -> bool:
        """Connect to Alpha Vantage"""
        try:
            # Test API connection
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'GC=F',
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data:
                    self.is_connected = True
                    self.last_update = datetime.now()
                    logging.info("Alpha Vantage data source connected")
                    return True
        except Exception as e:
            logging.error(f"Alpha Vantage connection failed: {e}")
            self.error_count += 1
        return False
    
    async def disconnect(self):
        """Disconnect from Alpha Vantage"""
        self.is_connected = False
    
    async def get_tick(self, symbol: str) -> Optional[MarketTick]:
        """Get latest tick from Alpha Vantage"""
        try:
            # Map symbol for Alpha Vantage
            av_symbol = "GC=F" if symbol == "XAUUSD" else symbol
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': av_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code}")
            
            data = response.json()
            if 'Global Quote' not in data:
                raise Exception("Invalid API response")
            
            quote = data['Global Quote']
            now = datetime.now()
            
            tick = MarketTick(
                symbol=symbol,
                timestamp=now,
                bid=float(quote['05. price']) - 0.1,
                ask=float(quote['05. price']) + 0.1,
                last=float(quote['05. price']),
                volume=int(quote['06. volume']),
                high=float(quote['03. high']),
                low=float(quote['04. low']),
                open=float(quote['02. open']),
                close=float(quote['08. previous close'])
            )
            
            self.last_update = now
            self.error_count = 0
            return tick
            
        except Exception as e:
            logging.error(f"Alpha Vantage tick error: {e}")
            self.error_count += 1
            return None

class MarketDataProcessor:
    """Main market data processing system"""
    
    def __init__(self, db_path: str = "data/market_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Data sources
        self.sources: List[DataSource] = []
        self.primary_source: Optional[DataSource] = None
        
        # Processing
        self.symbols = ["XAUUSD"]  # Gold
        self.tick_buffer: Dict[str, List[MarketTick]] = {}
        self.processed_data: Dict[str, pd.DataFrame] = {}
        
        # State
        self.is_running = False
        self.processing_thread = None
        self.update_interval = 1.0  # seconds
        
        # Callbacks
        self.tick_callbacks = []
        self.ohlc_callbacks = []
        
        # Initialize database
        self._init_database()
        
        logging.info("Market Data Processor initialized")
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ticks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        bid REAL NOT NULL,
                        ask REAL NOT NULL,
                        last REAL NOT NULL,
                        volume INTEGER DEFAULT 0,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        open REAL NOT NULL,
                        close REAL NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time 
                    ON ticks(symbol, timestamp)
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ohlc_1m (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume INTEGER DEFAULT 0,
                        tick_count INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, timestamp)
                    )
                """)
                
                conn.commit()
                logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
    
    def add_data_source(self, source: DataSource):
        """Add data source"""
        self.sources.append(source)
        self.sources.sort(key=lambda x: x.priority)
        logging.info(f"Added data source: {source.name} (priority: {source.priority})")
    
    def add_tick_callback(self, callback):
        """Add callback for new ticks"""
        self.tick_callbacks.append(callback)
    
    def add_ohlc_callback(self, callback):
        """Add callback for OHLC data"""
        self.ohlc_callbacks.append(callback)
    
    async def connect_sources(self):
        """Connect to all data sources"""
        connected_count = 0
        for source in self.sources:
            try:
                if await source.connect():
                    connected_count += 1
                    if not self.primary_source or source.priority < self.primary_source.priority:
                        self.primary_source = source
                        logging.info(f"Primary source: {source.name}")
            except Exception as e:
                logging.error(f"Failed to connect {source.name}: {e}")
        
        logging.info(f"Connected {connected_count}/{len(self.sources)} data sources")
        return connected_count > 0
    
    async def disconnect_sources(self):
        """Disconnect from all data sources"""
        for source in self.sources:
            try:
                await source.disconnect()
            except Exception as e:
                logging.error(f"Error disconnecting {source.name}: {e}")
    
    def _save_tick(self, tick: MarketTick):
        """Save tick to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO ticks 
                    (symbol, timestamp, bid, ask, last, volume, high, low, open, close)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tick.symbol, tick.timestamp, tick.bid, tick.ask, tick.last,
                    tick.volume, tick.high, tick.low, tick.open, tick.close
                ))
                conn.commit()
        except Exception as e:
            logging.error(f"Failed to save tick: {e}")
    
    def _process_ohlc(self, symbol: str):
        """Process ticks into OHLC data"""
        try:
            if symbol not in self.tick_buffer or not self.tick_buffer[symbol]:
                return
            
            ticks = self.tick_buffer[symbol]
            now = datetime.now()
            minute_start = now.replace(second=0, microsecond=0)
            
            # Filter ticks for current minute
            minute_ticks = [
                t for t in ticks 
                if t.timestamp >= minute_start and t.timestamp < minute_start + timedelta(minutes=1)
            ]
            
            if not minute_ticks:
                return
            
            # Create OHLC
            prices = [t.last for t in minute_ticks]
            volumes = [t.volume for t in minute_ticks]
            
            ohlc_data = {
                'symbol': symbol,
                'timestamp': minute_start,
                'open': prices[0],
                'high': max(prices),
                'low': min(prices),
                'close': prices[-1],
                'volume': sum(volumes),
                'tick_count': len(minute_ticks)
            }
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO ohlc_1m 
                    (symbol, timestamp, open, high, low, close, volume, tick_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ohlc_data['symbol'], ohlc_data['timestamp'],
                    ohlc_data['open'], ohlc_data['high'], ohlc_data['low'],
                    ohlc_data['close'], ohlc_data['volume'], ohlc_data['tick_count']
                ))
                conn.commit()
            
            # Notify callbacks
            for callback in self.ohlc_callbacks:
                try:
                    callback(ohlc_data)
                except Exception as e:
                    logging.error(f"OHLC callback error: {e}")
            
            # Clean old ticks (keep last 100)
            if len(self.tick_buffer[symbol]) > 100:
                self.tick_buffer[symbol] = self.tick_buffer[symbol][-100:]
        
        except Exception as e:
            logging.error(f"OHLC processing error: {e}")
    
    async def _processing_loop(self):
        """Main data processing loop"""
        logging.info("Data processing loop started")
        
        while self.is_running:
            try:
                # Get ticks from all symbols
                for symbol in self.symbols:
                    # Try primary source first, then fallback
                    tick = None
                    for source in self.sources:
                        if source.is_healthy():
                            tick = await source.get_tick(symbol)
                            if tick:
                                break
                    
                    if tick:
                        # Initialize buffer if needed
                        if symbol not in self.tick_buffer:
                            self.tick_buffer[symbol] = []
                        
                        # Add tick to buffer
                        self.tick_buffer[symbol].append(tick)
                        
                        # Save tick
                        self._save_tick(tick)
                        
                        # Process OHLC
                        self._process_ohlc(symbol)
                        
                        # Notify tick callbacks
                        for callback in self.tick_callbacks:
                            try:
                                callback(tick)
                            except Exception as e:
                                logging.error(f"Tick callback error: {e}")
                    
                    else:
                        logging.warning(f"No tick data available for {symbol}")
                
                # Health check on sources
                healthy_sources = [s for s in self.sources if s.is_healthy()]
                if not healthy_sources:
                    logging.error("No healthy data sources available!")
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logging.error(f"Processing loop error: {e}")
                await asyncio.sleep(5)  # Error backoff
    
    async def start(self):
        """Start data processing"""
        if self.is_running:
            logging.warning("Data processor already running")
            return
        
        logging.info("Starting market data processor...")
        
        # Connect to sources
        if not await self.connect_sources():
            logging.error("Failed to connect to any data sources")
            return False
        
        # Start processing
        self.is_running = True
        self.processing_thread = threading.Thread(
            target=lambda: asyncio.run(self._processing_loop())
        )
        self.processing_thread.start()
        
        logging.info("Market data processor started successfully")
        return True
    
    async def stop(self):
        """Stop data processing"""
        logging.info("Stopping market data processor...")
        
        self.is_running = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=10)
        
        await self.disconnect_sources()
        
        logging.info("Market data processor stopped")
    
    def get_latest_tick(self, symbol: str) -> Optional[MarketTick]:
        """Get latest tick for symbol"""
        if symbol in self.tick_buffer and self.tick_buffer[symbol]:
            return self.tick_buffer[symbol][-1]
        return None
    
    def get_ohlc_data(self, symbol: str, periods: int = 100) -> pd.DataFrame:
        """Get OHLC data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT timestamp, open, high, low, close, volume, tick_count
                    FROM ohlc_1m 
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(symbol, periods))
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df.sort_values('timestamp')
        except Exception as e:
            logging.error(f"Failed to get OHLC data: {e}")
            return pd.DataFrame()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        status = {
            'is_running': self.is_running,
            'total_sources': len(self.sources),
            'healthy_sources': len([s for s in self.sources if s.is_healthy()]),
            'primary_source': self.primary_source.name if self.primary_source else None,
            'symbols_tracked': len(self.symbols),
            'tick_buffer_size': sum(len(buffer) for buffer in self.tick_buffer.values()),
            'sources': []
        }
        
        for source in self.sources:
            source_status = {
                'name': source.name,
                'priority': source.priority,
                'is_connected': source.is_connected,
                'is_healthy': source.is_healthy(),
                'error_count': source.error_count,
                'last_update': source.last_update.isoformat() if source.last_update else None
            }
            status['sources'].append(source_status)
        
        return status

async def main():
    """Test the market data processor"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create processor
    processor = MarketDataProcessor()
    
    # Add data sources
    yahoo_source = YahooFinanceSource()
    processor.add_data_source(yahoo_source)
    
    # Add demo Alpha Vantage source (replace with real API key)
    # av_source = AlphaVantageSource("demo")
    # processor.add_data_source(av_source)
    
    # Add callbacks
    def tick_callback(tick):
        print(f"New tick: {tick.symbol} @ {tick.last:.2f} (Bid: {tick.bid:.2f}, Ask: {tick.ask:.2f})")
    
    def ohlc_callback(ohlc):
        print(f"OHLC: {ohlc['symbol']} O:{ohlc['open']:.2f} H:{ohlc['high']:.2f} L:{ohlc['low']:.2f} C:{ohlc['close']:.2f}")
    
    processor.add_tick_callback(tick_callback)
    processor.add_ohlc_callback(ohlc_callback)
    
    try:
        # Start processing
        await processor.start()
        
        # Run for demo period
        await asyncio.sleep(30)
        
        # Show status
        status = processor.get_health_status()
        print(f"\nSystem Status: {json.dumps(status, indent=2)}")
        
        # Show recent OHLC data
        ohlc_data = processor.get_ohlc_data("XAUUSD", 10)
        print(f"\nRecent OHLC data:\n{ohlc_data}")
        
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        await processor.stop()

if __name__ == "__main__":
    asyncio.run(main())
