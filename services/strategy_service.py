import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from datatypes.strategy import Strategy, StrategyState, TargetLevel
from patterns.ai_pattern_evaluator import ai_pattern_evaluator
from services.redis_manager import redis_manager
from core.db import get_db, StrategyHistory
from utils.util import get_current_session

class StrategyService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def evaluate_strategy_lock(self, ticker: str) -> Optional[Dict]:
        """Evaluate and manage strategy locks"""
        try:
            current_strategy = redis_manager.get_current_strategy(ticker)
            
            if current_strategy and current_strategy['state'] == StrategyState.LOCKED:
                return self._evaluate_existing_strategy(ticker, current_strategy)
            
            # Check for new strategy lock
            patterns = ai_pattern_evaluator.evaluate_all_patterns(ticker)
            if patterns and patterns[0]['match_score'] >= 65:
                return self._create_strategy_lock(ticker, patterns[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error evaluating strategy lock for {ticker}: {e}")
            return None

    def _evaluate_existing_strategy(self, ticker: str, strategy: Dict) -> Optional[Dict]:
        """Evaluate existing strategy lock"""
        current_price = redis_manager.get_stock_price(ticker)
        strategy_obj = Strategy.from_dict(strategy)
        
        # Check for target reached to update target
        if (strategy_obj.target_price and current_price >= float(strategy_obj.target_price) and strategy_obj.buy_time is not None):
            # Calculate new target based on technical analysis
            new_target = self._calculate_next_target(ticker, float(strategy_obj.target_price))
            
            if new_target:
                # Update the target with the new one
                target_updated = strategy_obj.update_target(new_target)
                
                if target_updated:
                    # Store updated strategy in Redis
                    strategy_dict = strategy_obj.to_dict()
                    redis_manager.set_current_strategy(ticker, strategy_dict)
                    redis_manager.publish('trade_signal', {
                        'type': 'trading_coach',
                        'status': 'target',
                        'ticker': ticker
                    })
                    return strategy_dict
                else:
                    redis_manager.publish('trade_signal', {
                        'type': 'trading_coach',
                        'status': 'exit',
                        'ticker': ticker
                    })
                    self._complete_strategy(ticker, strategy_obj.to_dict(), 'target')
                    return None
        
        # Check for high-confidence sell signals based on technical analysis
        if strategy_obj.buy_time is not None:
            sell_signal = self._check_sell_signals(ticker)

            if sell_signal:
                redis_manager.publish('trade_signal', {
                    'type': 'trading_coach',
                    'status': 'exit',
                    'ticker': ticker
                })
                self._complete_strategy(ticker, strategy_obj.to_dict(), 'sell')
                return None

        # Check for stop hit
        if (strategy_obj.stop_price and current_price <= float(strategy_obj.stop_price)):
            redis_manager.publish('trade_signal', {
                'type': 'trading_coach',
                'status': 'exit',
                'ticker': ticker
            })
            self._complete_strategy(ticker, strategy_obj.to_dict(), 'stop')
            return None

        # Check if we should update the stop loss for trailing
        new_stop = self._find_optimal_stop_adjustment(ticker, float(strategy_obj.stop_price))
        if new_stop and new_stop > float(strategy_obj.stop_price):
            strategy_obj.stop_price = new_stop

        # Update strategy metrics if needed
        updated_strategy = self._update_strategy_metrics(strategy_obj.to_dict(), ticker)
        redis_manager.set_current_strategy(ticker, updated_strategy)
        return updated_strategy

    def _create_strategy_lock(self, ticker: str, pattern: Dict) -> Dict:
        """Create new strategy lock"""
        price = redis_manager.get_stock_price(ticker)
        indicators = redis_manager.get_technical_indicators(ticker)
        strategy = Strategy(
            name=pattern['pattern_name'],
            state=StrategyState.LOCKED,
            entry_price=price,
            target_price=pattern['target_price'],
            stop_price=pattern['stop_price'],
            lock_time=datetime.now().isoformat(),
            buy_time=datetime.now().isoformat(),
            probability=pattern.get('probability', 0),
            match_score=pattern['match_score'],
            pattern_type=pattern.get('pattern_type', ''),
            description=pattern.get('description', ''),
            VWAP=indicators.get('VWAP', 0),
            RSI=indicators.get('RSI', 0),
            StochRSI_K=indicators.get('StochRSI_K', 0),
            StochRSI_D=indicators.get('StochRSI_D', 0),
            MACD=indicators.get('MACD', 0),
            MACD_signal=indicators.get('MACD_signal', 0),
            MACD_hist=indicators.get('MACD_hist', 0),
            ADX=indicators.get('ADX', 0),
            DMP=indicators.get('DMP', 0),
            DMN=indicators.get('DMN', 0),
            Supertrend=indicators.get('Supertrend', 0),
            Trend=indicators.get('Trend', 0),
            PSAR_L=indicators.get('PSAR_L', 0),
            PSAR_S=indicators.get('PSAR_S', 0),
            PSAR_R=indicators.get('PSAR_R', 0),
            EMA200=indicators.get('EMA200', 0),
            EMA21=indicators.get('EMA21', 0),
            EMA9=indicators.get('EMA9', 0),
            EMA4=indicators.get('EMA4', 0),
            EMA5=indicators.get('EMA5', 0),
            VWAP_Slope=indicators.get('VWAP_Slope', 0),
            Volume_Ratio=indicators.get('Volume_Ratio', 0),
            ROC=indicators.get('ROC', 0),
            Williams_R=indicators.get('Williams_R', 0),
            ATR=indicators.get('ATR', 0),
            HOD=indicators.get('HOD', 0),
            ATR_to_HOD=indicators.get('ATR_to_HOD', 0),
            ATR_to_VWAP=indicators.get('ATR_to_VWAP', 0),
            ZenP=indicators.get('ZenP', 0),
            RVol=indicators.get('RVol', 0),
            BB_lower=indicators.get('BB_lower', 0),
            BB_mid=indicators.get('BB_mid', 0),
            BB_upper=indicators.get('BB_upper', 0),
            ATR_Spread=indicators.get('ATR_Spread', 0),
        )

        # Initialize target history
        if strategy.target_price:
            strategy.target_history = [TargetLevel(
                price=strategy.target_price,
                timestamp=datetime.now().isoformat()
            )]

        strategy_dict = strategy.to_dict()
        redis_manager.set_current_strategy(ticker, strategy_dict)
        if pattern.get('probability', 0) >= 0.7:
            redis_manager.publish('trade_signal', {
                'type': 'trading_coach',
                'status': 'entry',
                'ticker': ticker
            })

        return strategy_dict

    def _complete_strategy(self, ticker: str, strategy: Dict, completion_type: str) -> None:
        """Complete a strategy and store in history"""
        strategy_obj = Strategy.from_dict(strategy)
        strategy_obj.state = StrategyState.COMPLETED
        strategy_obj.completion_type = completion_type
        strategy_obj.completion_time = datetime.now().isoformat()

        # Get current stock price for final calculations
        final_price = redis_manager.get_stock_price(ticker)

        # Calculate profit/loss
        profit_loss = 0.0
        profit_loss_percent = 0.0

        if strategy_obj.buy_time and final_price:
            # Calculate P&L based on entry price and final price
            if completion_type == 'sell':
                profit_loss = final_price - float(strategy_obj.entry_price)
                profit_loss_percent = (profit_loss / float(strategy_obj.entry_price)) * 100
            elif completion_type == 'stop':
                profit_loss = float(strategy_obj.stop_price) - float(strategy_obj.entry_price)
                profit_loss_percent = (profit_loss / float(strategy_obj.entry_price)) * 100
            elif completion_type == 'target':
                profit_loss = float(strategy_obj.target_price) - float(strategy_obj.entry_price)
                profit_loss_percent = (profit_loss / float(strategy_obj.entry_price)) * 100

        # Store in Redis history
        redis_manager.add_strategy_to_history(ticker, strategy_obj.to_dict())

        # Store in database
        self._store_strategy_in_database(ticker, strategy_obj, completion_type, final_price, profit_loss, profit_loss_percent)

        # Clear current strategy
        redis_manager.set_current_strategy(ticker, None)

    def _store_strategy_in_database(self, ticker: str, strategy_obj: Strategy, completion_type: str,
                                   final_price: float, profit_loss: float, profit_loss_percent: float) -> None:
        """Store completed strategy in database"""
        try:
            with get_db() as db:
                # Convert datetime strings to datetime objects
                lock_time = None
                buy_time = None
                hold_time = None
                completion_time = None

                if strategy_obj.lock_time:
                    lock_time = datetime.fromisoformat(strategy_obj.lock_time.replace('Z', '+00:00'))
                if strategy_obj.buy_time:
                    buy_time = datetime.fromisoformat(strategy_obj.buy_time.replace('Z', '+00:00'))
                if strategy_obj.hold_time:
                    hold_time = datetime.fromisoformat(strategy_obj.hold_time.replace('Z', '+00:00'))
                if strategy_obj.completion_time:
                    completion_time = datetime.fromisoformat(strategy_obj.completion_time.replace('Z', '+00:00'))

                # Create strategy history record
                strategy_history = StrategyHistory(
                    ticker=ticker,
                    strategy_name=strategy_obj.name,
                    entry_price=float(strategy_obj.entry_price),
                    target_price=float(strategy_obj.target_price),
                    stop_price=float(strategy_obj.stop_price),
                    lock_time=lock_time,
                    buy_time=buy_time,
                    hold_time=hold_time,
                    probability=strategy_obj.probability,
                    match_score=strategy_obj.match_score,
                    pattern_type=strategy_obj.pattern_type,
                    description=strategy_obj.description,
                    completion_type=completion_type,
                    completion_time=completion_time or datetime.utcnow(),
                    final_price=final_price,
                    profit_loss=profit_loss,
                    profit_loss_percent=profit_loss_percent,
                    target_history=json.dumps([target.to_dict() for target in strategy_obj.target_history]),
                    VWAP=strategy_obj.VWAP,
                    RSI=strategy_obj.RSI,
                    StochRSI_K=strategy_obj.StochRSI_K,
                    StochRSI_D=strategy_obj.StochRSI_D,
                    MACD=strategy_obj.MACD,
                    MACD_signal=strategy_obj.MACD_signal,
                    MACD_hist=strategy_obj.MACD_hist,
                    ADX=strategy_obj.ADX,
                    DMP=strategy_obj.DMP,
                    DMN=strategy_obj.DMN,
                    Supertrend=strategy_obj.Supertrend,
                    Trend=strategy_obj.Trend,
                    PSAR_L=strategy_obj.PSAR_L,
                    PSAR_S=strategy_obj.PSAR_S,
                    PSAR_R=strategy_obj.PSAR_R,
                    EMA200=strategy_obj.EMA200,
                    EMA21=strategy_obj.EMA21,
                    EMA9=strategy_obj.EMA9,
                    EMA4=strategy_obj.EMA4,
                    EMA5=strategy_obj.EMA5,
                    VWAP_Slope=strategy_obj.VWAP_Slope,
                    Volume_Ratio=strategy_obj.Volume_Ratio,
                    ROC=strategy_obj.ROC,
                    Williams_R=strategy_obj.Williams_R,
                    ATR=strategy_obj.ATR,
                    HOD=strategy_obj.HOD,
                    ATR_to_HOD=strategy_obj.ATR_to_HOD,
                    ATR_to_VWAP=strategy_obj.ATR_to_VWAP,
                    ZenP=strategy_obj.ZenP,
                    RVol=strategy_obj.RVol,
                    BB_lower=strategy_obj.BB_lower,
                    BB_mid=strategy_obj.BB_mid,
                    BB_upper=strategy_obj.BB_upper,
                    ATR_Spread=strategy_obj.ATR_Spread,
                    session=get_current_session(),
                )

                db.add(strategy_history)
                db.commit()

                self.logger.info(f"Stored completed strategy for {ticker} in database with ID: {strategy_history.id}")

        except Exception as e:
            self.logger.error(f"Error storing strategy history in database for {ticker}: {e}")
            # Don't raise the exception to avoid breaking the strategy completion flow

    def _update_strategy_metrics(self, strategy: Dict, ticker: str) -> Dict:
        """Update strategy metrics while maintaining original entry and stop prices"""
        # Create Strategy object to ensure proper handling of all fields
        strategy_obj = Strategy.from_dict(strategy)

        # Find if current strategy is still in the patterns
        current_pattern = ai_pattern_evaluator.evaluate_pattern(ticker, strategy_obj.name)

        if current_pattern:
            # Update metrics while keeping original price targets
            strategy_obj.match_score = current_pattern['match_score']
            strategy_obj.description = current_pattern['description']
            strategy_obj.probability = current_pattern.get('probability', strategy_obj.probability)

            return {
                **strategy,
                'match_score': current_pattern['match_score'],
                'description': current_pattern['description'],
                'probability': current_pattern.get('probability', strategy.get('probability', 0.65))
            }

        return strategy

    def _calculate_next_target(self, ticker: str, current_target: float) -> Optional[float]:
        """Calculate next target based on technical analysis"""
        try:
            key_levels = redis_manager.get_key_levels(ticker)

            # Find next resistance level above current target
            resistances = [level for level in key_levels
                         if level.get('type') == 'resistance' and level.get('price', 0) > current_target]

            if resistances:
                # Sort by price and take the closest one
                next_resistance = min(resistances, key=lambda x: x.get('price', float('inf')))
                return next_resistance.get('price', current_target * 1.02)

            # If no resistance levels, use ATR-based target
            atr = redis_manager.get_technical_indicator(ticker, 'ATR', 1)
            if atr > 0:
                return current_target + (atr * 1.5)  # 1.5 ATR above current target

            # Default: 2% above current target
            return current_target * 1.02

        except Exception as e:
            self.logger.error(f"Error calculating next target: {e}")
            return None

    def _check_sell_signals(self, ticker: str) -> Optional[str]:
        """Check for high-confidence sell signals based on technical analysis"""
        try:
            indicators = redis_manager.get_technical_indicators(ticker)

            current_price = redis_manager.get_stock_price(ticker)

            adx = indicators.get('ADX', 0)
            atr = indicators.get('ATR', 0)
            vwap_slope = indicators.get('VWAP_Slope', 0)
            roc2 = redis_manager.get_technical_indicator(ticker, 'ROC', 2)
            roc_prime = (roc2[-1] - roc2[-2]) if isinstance(roc2, list) and len(roc2) >= 2 else 0
            vwap = indicators.get('VWAP', current_price)
            ema9 = indicators.get('EMA9', vwap)
            volume_ratio = indicators.get('Volume_Ratio', 1)
            stoch_rsi = indicators.get('StochRSI_K', 50)
            williams_r = indicators.get('Williams_R', 0)

            aggressor_ratio = 0.5
            uptick_seq = 0
            ticks = redis_manager.get_tick(ticker)
            if ticks:
                try:
                    now_ts = pd.to_datetime(ticks[-1]['time'])
                    recent_ticks = [t for t in reversed(ticks) if pd.to_datetime(t['time']) >= now_ts - pd.Timedelta(seconds=5)]
                    buy_vol = sum(t.get('volume', 0) for t in recent_ticks if t.get('ticker_direction') == 'BUY')
                    sell_vol = sum(t.get('volume', 0) for t in recent_ticks if t.get('ticker_direction') == 'SELL')
                    total = buy_vol + sell_vol
                    aggressor_ratio = (buy_vol / total) if total > 0 else 0.5
                    for t in recent_ticks:
                        td = t.get('ticker_direction')
                        if td == 'BUY':
                            uptick_seq += 1
                        elif td == 'SELL':
                            break
                        else:
                            continue
                except Exception:
                    aggressor_ratio = 0.5
                    uptick_seq = 0


            # Outside strong-trend regime, evaluate conservative sell conditions
            # 1) Price below VWAP and EMA9 with weak tape/momentum
            if (current_price < vwap and current_price < (ema9 or vwap)) and ((stoch_rsi < 40) or (roc_prime < 0)) and (aggressor_ratio <= 0.45):
                return "Below VWAP/EMA9 with Weak Tape"

            # 2) High ADX + declining price only if tape confirms weakness
            if adx > 35 and current_price < min(vwap, (ema9 or vwap)) and aggressor_ratio <= 0.4 and roc_prime < 0 and uptick_seq == 0:
                return "Strong Bearish Trend Confirmation"

            # 3) Volume exhaustion only when coupled with tape rollover and momentum loss
            if volume_ratio > 3.0 and stoch_rsi > 80 and aggressor_ratio <= 0.5 and roc_prime <= 0:
                return "Volume Exhaustion with Tape Rollover"

            # 4) Williams %R overbought is not a sell by itself; require loss of structure
            if (williams_r >= -20 and adx > 20) and current_price < (ema9 or vwap) and ((aggressor_ratio <= 0.45) or (roc_prime < 0)):
                return "Williams %R Overbought with Structure Loss"

            return None

        except Exception as e:
            self.logger.error(f"Error checking sell signals: {e}")
            return None

    def _find_optimal_stop_adjustment(self, ticker: str, current_stop: float) -> Optional[float]:
        """Find optimal stop loss adjustment for trailing"""
        try:
            indicators = redis_manager.get_technical_indicators(ticker)

            current_price = redis_manager.get_stock_price(ticker)
            vwap = indicators.get('VWAP', current_price)
            atr = indicators.get('ATR', 0)

            # Calculate new stop based on VWAP
            if current_price > vwap:
                vwap_stop = vwap - (atr * 0.5)  # 0.5 ATR below VWAP
                if vwap_stop > current_stop:
                    return vwap_stop

            # Calculate new stop based on ATR
            if atr > 0:
                atr_stop = current_price - (atr * 1.5)  # 1.5 ATR below current price
                if atr_stop > current_stop:
                    return atr_stop

            return None

        except Exception as e:
            self.logger.error(f"Error finding optimal stop adjustment: {e}")
            return None

# Global strategy service instance
strategy_service = StrategyService()