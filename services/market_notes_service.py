import logging
from typing import List, Dict, Optional
from datetime import datetime
from datatypes.market_note import MarketNote, NoteType, NotePriority
from services.redis_manager import redis_manager

class MarketNotesService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_market_notes(self, stock_data: Dict) -> List[MarketNote]:
        """Generate market notes for a stock based on StockManager data structure"""
        notes = []
        
        try:
            # Volume Analysis
            volume_notes = self._analyze_volume(stock_data)
            notes.extend(volume_notes)

            # Price Action Analysis
            price_notes = self._analyze_price_action(stock_data)
            notes.extend(price_notes)

            # Technical Analysis
            technical_notes = self._analyze_technicals(stock_data)
            notes.extend(technical_notes)

            # Strategy Analysis
            strategy_notes = self._analyze_strategy(stock_data)
            notes.extend(strategy_notes)

            # Order Book Analysis
            orderbook_notes = self._analyze_order_book(stock_data)
            notes.extend(orderbook_notes)

            # Pattern Analysis
            pattern_notes = self._analyze_patterns(stock_data)
            notes.extend(pattern_notes)

            return notes

        except Exception as e:
            self.logger.error(f"Error generating market notes: {e}")
            return []

    def _analyze_volume(self, ticker: str) -> List[MarketNote]:
        """Analyze volume patterns from StockManager data"""
        notes = []
        try:
            indicators = redis_manager.get_technical_indicators(ticker)

            volume_ratio = indicators.get('Volume_Ratio', 0)
            rvol = indicators.get('RVol', 0)

            if volume_ratio > 5:
                notes.append(MarketNote(
                    message=f"Extreme volume: {volume_ratio:.1f}x average daily volume",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.CRITICAL,
                    icon="🚀"
                ))
            elif volume_ratio > 3:
                notes.append(MarketNote(
                    message=f"High volume: {volume_ratio:.1f}x average daily volume",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.IMPORTANT,
                    icon="📈"
                ))
            elif volume_ratio > 2:
                notes.append(MarketNote(
                    message=f"Above average volume: {volume_ratio:.1f}x normal",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.NORMAL,
                    icon="📊"
                ))

            if rvol > 3:
                notes.append(MarketNote(
                    message=f"Strong relative volume: {rvol:.1f}x 5-min average",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.IMPORTANT,
                    icon="⚡"
                ))

        except Exception as e:
            self.logger.error(f"Error in volume analysis: {e}")

        return notes

    def _analyze_price_action(self, ticker: str) -> List[MarketNote]:
        """Analyze price action from StockManager data"""
        notes = []
        try:
            indicators = redis_manager.get_technical_indicators(ticker)
            
            current_price = redis_manager.get_stock_price(ticker)
            vwap = indicators.get('VWAP', 0)
            vwap_slope = indicators.get('VWAP_Slope', 0)
            ema200 = indicators.get('EMA200', 0)
            
            if vwap > 0:
                vwap_diff = ((current_price - vwap) / vwap) * 100
                if vwap_diff > 3:
                    notes.append(MarketNote(
                        message=f"Trading {abs(vwap_diff):.1f}% above VWAP",
                        type=NoteType.POSITIVE,
                        priority=NotePriority.NORMAL,
                        icon="🔼"
                    ))
                elif vwap_diff < -3:
                    notes.append(MarketNote(
                        message=f"Trading {abs(vwap_diff):.1f}% below VWAP",
                        type=NoteType.WARNING,
                        priority=NotePriority.NORMAL,
                        icon="🔽"
                    ))

            if vwap_slope > 0:
                notes.append(MarketNote(
                    message="VWAP trending upward - bullish momentum",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.NORMAL,
                    icon="📈"
                ))
            elif vwap_slope < -0.001:
                notes.append(MarketNote(
                    message="VWAP trending downward - bearish pressure",
                    type=NoteType.WARNING,
                    priority=NotePriority.NORMAL,
                    icon="📉"
                ))

            if ema200 > 0 and current_price > ema200:
                notes.append(MarketNote(
                    message="Trading above 200 EMA - long-term bullish",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.NORMAL,
                    icon="📊"
                ))

        except Exception as e:
            self.logger.error(f"Error in price action analysis: {e}")

        return notes

    def _analyze_technicals(self, ticker: str) -> List[MarketNote]:
        """Analyze technical indicators from StockManager data"""
        notes = []
        try:
            indicators = redis_manager.get_technical_indicators(ticker)
            scores = redis_manager.get_technical_scores(ticker)
            
            # RSI Analysis
            stoch_rsi = indicators.get('StochRSI_K', 50)
            if stoch_rsi > 80:
                notes.append(MarketNote(
                    message=f"Overbought conditions (Stoch RSI: {stoch_rsi:.0f})",
                    type=NoteType.WARNING,
                    priority=NotePriority.IMPORTANT,
                    icon="🔥"
                ))
            elif stoch_rsi < 20:
                notes.append(MarketNote(
                    message=f"Oversold conditions (Stoch RSI: {stoch_rsi:.0f})",
                    type=NoteType.WARNING,
                    priority=NotePriority.IMPORTANT,
                    icon="❄️"
                ))

            # MACD Analysis
            macd = indicators.get('MACD', 0)
            macd_signal = indicators.get('MACD_signal', 0)
            if macd > macd_signal and macd > 0:
                notes.append(MarketNote(
                    message="MACD showing strong bullish momentum",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.NORMAL,
                    icon="📈"
                ))
            elif macd < macd_signal and macd < 0:
                notes.append(MarketNote(
                    message="MACD showing bearish momentum",
                    type=NoteType.WARNING,
                    priority=NotePriority.NORMAL,
                    icon="📉"
                ))

            # ADX Analysis
            adx = indicators.get('ADX', 0)
            if adx > 25:
                notes.append(MarketNote(
                    message=f"Strong trend strength (ADX: {adx:.0f})",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.NORMAL,
                    icon="💪"
                ))

            # ROC Analysis
            roc = indicators.get('ROC', 0)
            if roc > 5:
                notes.append(MarketNote(
                    message=f"Strong momentum (ROC: {roc:.1f}%)",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.NORMAL,
                    icon="🚀"
                ))
            elif roc < -5:
                notes.append(MarketNote(
                    message=f"Negative momentum (ROC: {roc:.1f}%)",
                    type=NoteType.WARNING,
                    priority=NotePriority.NORMAL,
                    icon="⚠️"
                ))

            # Supertrend Analysis
            supertrend = indicators.get('Supertrend', 0)
            if supertrend == 1:
                notes.append(MarketNote(
                    message="Supertrend bullish - uptrend confirmed",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.IMPORTANT,
                    icon="📈"
                ))
            elif supertrend == -1:
                notes.append(MarketNote(
                    message="Supertrend bearish - downtrend confirmed",
                    type=NoteType.WARNING,
                    priority=NotePriority.IMPORTANT,
                    icon="📉"
                ))

            # Technical Score Analysis
            technical_score = scores.get('technical_score', 0)
            if technical_score > 0.8:
                notes.append(MarketNote(
                    message=f"Excellent technical score: {technical_score:.2f}",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.IMPORTANT,
                    icon="⭐"
                ))
            elif technical_score < 0.3:
                notes.append(MarketNote(
                    message=f"Poor technical score: {technical_score:.2f}",
                    type=NoteType.WARNING,
                    priority=NotePriority.IMPORTANT,
                    icon="⚠️"
                ))

        except Exception as e:
            self.logger.error(f"Error in technical analysis: {e}")

        return notes

    def _analyze_strategy(self, stock_data: Dict) -> List[MarketNote]:
        """Analyze current strategy from StockManager data"""
        notes = []
        try:
            strategy = stock_data.get('strategy', {})
            if strategy and strategy.get('state') == 'LOCKED':
                current_price = stock_data.get('price', 0)
                target_price = float(strategy.get('target_price', 0))
                stop_price = float(strategy.get('stop_price', 0))

                if target_price > 0:
                    distance_to_target = ((target_price - current_price) / current_price) * 100
                    if distance_to_target < 2:
                        notes.append(MarketNote(
                            message=f"Approaching target: {distance_to_target:.1f}% away",
                            type=NoteType.POSITIVE,
                            priority=NotePriority.CRITICAL,
                            icon="🎯",
                            is_strategy=True,
                            strategy_details=strategy
                        ))

                if stop_price > 0:
                    distance_to_stop = ((current_price - stop_price) / current_price) * 100
                    if distance_to_stop < 2:
                        notes.append(MarketNote(
                            message=f"Near stop loss: {distance_to_stop:.1f}% away",
                            type=NoteType.DANGER,
                            priority=NotePriority.CRITICAL,
                            icon="⚠️",
                            is_strategy=True,
                            strategy_details=strategy
                        ))

        except Exception as e:
            self.logger.error(f"Error in strategy analysis: {e}")

        return notes

    def _analyze_order_book(self, stock_data: Dict) -> List[MarketNote]:
        """Analyze order book from StockManager data"""
        notes = []
        try:
            orderbook = stock_data.get('orderbook', [])
            if not orderbook:
                return notes

            # Get the latest orderbook snapshot
            latest_snapshot = orderbook[-1] if orderbook else {}
            
            bids = latest_snapshot.get('bids', [])
            asks = latest_snapshot.get('asks', [])
            imbalance = latest_snapshot.get('imbalance', 0)

            if not bids or not asks:
                return notes

            total_bid_volume = latest_snapshot.get('bid_volume', 0)
            total_ask_volume = latest_snapshot.get('ask_volume', 0)

            if total_ask_volume > 0:
                buy_sell_ratio = total_bid_volume / total_ask_volume

                if buy_sell_ratio > 2:
                    notes.append(MarketNote(
                        message=f"Strong buying pressure ({buy_sell_ratio:.1f}x bid/ask ratio)",
                        type=NoteType.POSITIVE,
                        priority=NotePriority.IMPORTANT,
                        icon="💪"
                    ))
                elif buy_sell_ratio < 0.5:
                    notes.append(MarketNote(
                        message=f"Heavy selling pressure ({buy_sell_ratio:.1f}x bid/ask ratio)",
                        type=NoteType.WARNING,
                        priority=NotePriority.IMPORTANT,
                        icon="⚠️"
                    ))

            if imbalance > 0.3:
                notes.append(MarketNote(
                    message=f"Bid-heavy order book (imbalance: {imbalance:.2f})",
                    type=NoteType.POSITIVE,
                    priority=NotePriority.NORMAL,
                    icon="📈"
                ))
            elif imbalance < -0.3:
                notes.append(MarketNote(
                    message=f"Ask-heavy order book (imbalance: {imbalance:.2f})",
                    type=NoteType.WARNING,
                    priority=NotePriority.NORMAL,
                    icon="📉"
                ))

        except Exception as e:
            self.logger.error(f"Error in order book analysis: {e}")

        return notes

    def _analyze_patterns(self, stock_data: Dict) -> List[MarketNote]:
        """Analyze detected patterns from StockManager data"""
        notes = []
        try:
            patterns = stock_data.get('patterns', [])
            
            for pattern in patterns:
                pattern_name = pattern.get('name', 'Unknown')
                confidence = pattern.get('confidence', 0)
                signal = pattern.get('signal', 'neutral')
                
                if confidence > 0.7:
                    if signal == 'bullish':
                        notes.append(MarketNote(
                            message=f"Strong bullish pattern: {pattern_name}",
                            type=NoteType.POSITIVE,
                            priority=NotePriority.IMPORTANT,
                            icon="📈"
                        ))
                    elif signal == 'bearish':
                        notes.append(MarketNote(
                            message=f"Strong bearish pattern: {pattern_name}",
                            type=NoteType.WARNING,
                            priority=NotePriority.IMPORTANT,
                            icon="📉"
                        ))

        except Exception as e:
            self.logger.error(f"Error in pattern analysis: {e}")

        return notes

# Create global instance
market_notes_service = MarketNotesService() 