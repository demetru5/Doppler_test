import pandas as pd
import pandas_ta as ta
import numpy as np
import time
import json
from typing import Dict, Any, List
import logging

from services.redis_manager import redis_manager
from utils.util import get_current_session, get_today_session_point_time, get_session_from_time

def convert_candles_to_dataframe(candles):
    try:
        df = pd.DataFrame(candles)

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        else:
            # Create a datetime index if timestamp column doesn't exist
            df.index = pd.to_datetime(df.index, unit='ms')

        # Sort by index to ensure chronological order
        df.sort_index(inplace=True)

        # Classify each row into trading session
        df['Session'] = df.index.map(get_session_from_time)

        return df
    except Exception as e:
        logging.error(f"Error while converting candles to dataframe: {e}")
        return None

def calculate_vr(df, n=26, m=6):
    """
    Calculate Volume Ratio (VR) indicator
    
    Formula:
    LC = REF(CLOSE, 1)  # Previous close
    TH = SUM(IF(CLOSE > LC, VOL, 0), N)  # Sum of volume when price rises
    TL = SUM(IF(CLOSE < LC, VOL, 0), N)  # Sum of volume when price falls  
    TQ = SUM(IF(CLOSE = LC, VOL, 0), N)  # Sum of volume when price unchanged
    VR = 100 * (TH * 2 + TQ) / (TL * 2 + TQ)
    VRMA = MA(VR, M)  # Moving average of VR
    """
    try:
        # Calculate previous close (LC)
        df['LC'] = df['close'].shift(1)
        
        # Calculate conditions for volume classification
        df['price_rise'] = df['close'] > df['LC']
        df['price_fall'] = df['close'] < df['LC']
        df['price_unchanged'] = df['close'] == df['LC']
        
        # Calculate volume for each condition
        df['vol_rise'] = np.where(df['price_rise'], df['volume'], 0)
        df['vol_fall'] = np.where(df['price_fall'], df['volume'], 0)
        df['vol_unchanged'] = np.where(df['price_unchanged'], df['volume'], 0)
        
        # Calculate rolling sums (TH, TL, TQ)
        df['TH'] = df['vol_rise'].rolling(window=n, min_periods=1).sum()
        df['TL'] = df['vol_fall'].rolling(window=n, min_periods=1).sum()
        df['TQ'] = df['vol_unchanged'].rolling(window=n, min_periods=1).sum()
        
        # Calculate VR
        df['Volume_Ratio'] = np.where(
            (df['TL'] * 2 + df['TQ']) != 0,
            100 * (df['TH'] * 2 + df['TQ']) / (df['TL'] * 2 + df['TQ']),
            0  # or np.nan if you prefer to indicate undefined values
        )
        
        # Clean up intermediate columns
        df.drop(['LC', 'price_rise', 'price_fall', 'price_unchanged', 
                'vol_rise', 'vol_fall', 'vol_unchanged', 'TH', 'TL', 'TQ'], 
                axis=1, inplace=True)
        
        return df
        
    except Exception as e:
        logging.error(f"Error calculating VR: {e}")
        df['Volume_Ratio'] = pd.Series([0] * len(df))
        return df

def calculate_macd(df, short=12, long=26, mid=9):
    """
    Calculate MACD using the exact formula from moomoo service
    MACD = EMA(CLOSE, SHORT) - EMA(CLOSE, LONG)
    MACD_signal = EMA(MACD, MID)
    MACD_hist = (MACD - MACD_signal) * 2
    """
    try:
        # Calculate macd (Difference Line)
        ema_short = ta.ema(df['close'], length=short)
        ema_long = ta.ema(df['close'], length=long)
        macd = ema_short - ema_long

        # Calculate macd_signal (Signal Line)
        macd_signal = ta.ema(macd, length=mid)

        # Calculate macd_hist (Histogram) - multiply by 2 as per formula
        macd_hist = (macd - macd_signal) * 2

        return {
            'MACD': macd,
            'MACD_signal': macd_signal,
            'MACD_hist': macd_hist
        }
    except Exception as e:
        logging.error(f"Error calculating custom MACD: {e}")
        return {
            'MACD': pd.Series([0] * len(df)),
            'MACD_signal': pd.Series([0] * len(df)),
            'MACD_hist': pd.Series([0] * len(df))
        }

def calculate_key_levels(prices: list, volumes: list) -> Dict[str, list]:
    """Calculate key price levels based on volume profile and price action"""
    try:
        if not prices or not volumes:
            return {'key_levels': [], 'support_resistance': []}
            
        # Convert to numpy arrays for efficient computation
        prices_arr = np.array(prices)
        volumes_arr = np.array(volumes)
        
        # Find high volume nodes
        volume_threshold = np.percentile(volumes_arr, 75)  # Top 25% volume
        high_volume_indices = np.where(volumes_arr >= volume_threshold)[0]
        
        # Calculate key levels (price levels with high volume)
        volume_price_levels = sorted(set([round(float(prices_arr[i]), 2) for i in high_volume_indices]))
        key_levels = [{'price': price, 'type': 'volume_level'} for price in volume_price_levels]
        
        # Calculate support and resistance using local minima/maxima
        window = min(20, len(prices) // 4)  # Adaptive window size
        support_resistance = []
        
        for i in range(window, len(prices) - window):
            # Get the window ranges
            left_window = prices_arr[i-window:i]
            right_window = prices_arr[i+1:i+window+1]
            current_price = float(prices_arr[i])
            
            # Check for peaks (local maxima)
            if (current_price > np.max(left_window) and 
                current_price > np.max(right_window)):
                support_resistance.append({
                    'price': round(current_price, 2),
                    'type': 'resistance',
                    'strength': float(volumes_arr[i]) / np.mean(volumes_arr)  # Volume-based strength
                })
            
            # Check for troughs (local minima)
            if (current_price < np.min(left_window) and 
                current_price < np.min(right_window)):
                support_resistance.append({
                    'price': round(current_price, 2),
                    'type': 'support',
                    'strength': float(volumes_arr[i]) / np.mean(volumes_arr)  # Volume-based strength
                })
        
        # Filter out levels that are too close to each other (within 0.5% range)
        filtered_levels = []
        if support_resistance:
            filtered_levels = [support_resistance[0]]
            for level in support_resistance[1:]:
                if abs(level['price'] - filtered_levels[-1]['price']) / filtered_levels[-1]['price'] > 0.005:
                    filtered_levels.append(level)
        
        # Combine key levels with support/resistance levels
        all_levels = key_levels + filtered_levels
        
        # Sort all levels by price
        all_levels.sort(key=lambda x: x['price'])
        
        return {
            'key_levels': all_levels,  # Now all levels are dictionaries with price and type
            'support_resistance': filtered_levels  # Only support/resistance levels
        }
    except Exception as e:
        return {'key_levels': [], 'support_resistance': []}

def update_technical_indicators(ticker: str):
    try:
        candles = redis_manager.get_candles(ticker)

        df = convert_candles_to_dataframe(candles)

        try:
            current_session = get_current_session()
            if current_session == 'closed':
                current_session_open_time = candles[0]['timestamp']
                current_session_close_time = candles[-1]['timestamp']
            else:
                current_session_open_time = get_today_session_point_time(current_session, 'open', as_string=True)
                current_session_close_time = get_today_session_point_time(current_session, 'close', as_string=True)

            # Initialize VWAP column with 0
            df['VWAP'] = 0.0

            # Filter for current session data only
            session_mask = (df.index >= current_session_open_time) & (df.index <= current_session_close_time)
            session_df = df[session_mask]

            if len(session_df) > 0:
                # Calculate VWAP only for session candles
                session_vwap = ta.vwap(
                    high=session_df['high'],
                    low=session_df['low'],
                    close=session_df['close'],
                    volume=session_df['volume']
                )

                # Only update VWAP values for the session period
                df.loc[session_mask, 'VWAP'] = session_vwap

        except Exception as e:
            logging.error(f"Error calculating session-based VWAP: {e}")
            df['VWAP'] = 0.0  # Ensure all values are 0 if error occurs

        # Calculate RSI
        df['RSI'] = ta.rsi(df['close'], length=14)

        # Calculate Stoch RSI
        stochrsi_data = ta.stochrsi(df['close'], length=14, smooth_k=3, smooth_d=3)
        if stochrsi_data is not None:
            df['StochRSI_K'] = stochrsi_data.get('STOCHRSIk_14_14_3_3', pd.Series([0] * len(df)))
            df['StochRSI_D'] = stochrsi_data.get('STOCHRSId_14_14_3_3', pd.Series([0] * len(df)))
        else:
            df['StochRSI_K'] = pd.Series([0] * len(df))
            df['StochRSI_D'] = pd.Series([0] * len(df))

        # Calculate MACD
        try:
            macd_data = calculate_macd(df, short=12, long=26, mid=9) if (len(df) > 26 and not df['close'].isnull().any()) else None
            if macd_data is not None:
                df['MACD'] = macd_data.get('MACD', pd.Series([0] * len(df)))
                df['MACD_signal'] = macd_data.get('MACD_signal', pd.Series([0] * len(df)))
                df['MACD_hist'] = macd_data.get('MACD_hist', pd.Series([0] * len(df)))
            else:
                df['MACD'] = pd.Series([0] * len(df))
                df['MACD_signal'] = pd.Series([0] * len(df))
                df['MACD_hist'] = pd.Series([0] * len(df))
        except Exception as e:
            logging.error(f"Error calculating MACD: {e}")
            df['MACD'] = pd.Series([0] * len(df))
            df['MACD_signal'] = pd.Series([0] * len(df))
            df['MACD_hist'] = pd.Series([0] * len(df))

        # Calculate ADX
        try:
            adx_data = ta.adx(df['high'], df['low'], df['close'], length=14, mamode='sma')
            if adx_data is not None:
                df['ADX'] = adx_data.get('ADX_14', pd.Series([0] * len(df)))
                df['DMP'] = adx_data.get('DMP_14', pd.Series([0] * len(df)))
                df['DMN'] = adx_data.get('DMN_14', pd.Series([0] * len(df)))
            else:
                df['ADX'] = pd.Series([0] * len(df))
                df['DMP'] = pd.Series([0] * len(df))
                df['DMN'] = pd.Series([0] * len(df))
        except Exception as e:
            logging.error(f"Error calculating ADX: {e}")
            df['ADX'] = pd.Series([0] * len(df))
            df['DMP'] = pd.Series([0] * len(df))
            df['DMN'] = pd.Series([0] * len(df))

        # Calculate Supertrend
        try:
            supertrend_data = ta.supertrend(high=df['high'], low=df['low'], close=df['close'], length=10, multiplier=3)
            if supertrend_data is not None:
                df['Supertrend'] = supertrend_data.get('SUPERT_10_3.0', pd.Series([0] * len(df)))
                df['Trend'] = np.where(df['Supertrend'] > df['close'], 1, -1)
            else:
                df['Supertrend'] = pd.Series([0] * len(df))
                df['Trend'] = pd.Series([0] * len(df))
        except Exception as e:
            logging.error(f"Error calculating Supertrend: {e}")
            df['Supertrend'] = pd.Series([0] * len(df))
            df['Trend'] = pd.Series([0] * len(df))

        # Calculate PSAR
        try:
            psar_data = ta.psar(df['high'], df['low'], df['close'], af0=0.02, af=0.02, max_af=0.2)
            if psar_data is not None:
                df['PSAR_L'] = psar_data.get('PSARl_0.02_0.2', pd.Series([0] * len(df)))
                df['PSAR_S'] = psar_data.get('PSARs_0.02_0.2', pd.Series([0] * len(df)))
                df['PSAR_AF'] = psar_data.get('PSARaf_0.02_0.2', pd.Series([0] * len(df)))
                df['PSAR_R'] = psar_data.get('PSARr_0.02_0.2', pd.Series([0] * len(df)))
            else:
                df['PSAR_L'] = pd.Series([0] * len(df))
                df['PSAR_S'] = pd.Series([0] * len(df))
                df['PSAR_AF'] = pd.Series([0] * len(df))
                df['PSAR_R'] = pd.Series([0] * len(df))
        except Exception as e:
            logging.error(f"Error calculating PSAR: {e}")
            df['PSAR_L'] = pd.Series([0] * len(df))
            df['PSAR_S'] = pd.Series([0] * len(df))
            df['PSAR_AF'] = pd.Series([0] * len(df))
            df['PSAR_R'] = pd.Series([0] * len(df))

        # EMA 200
        try:
            df['EMA200'] = ta.ema(df['close'], length=200) if len(df) > 200 else None
        except Exception as e:
            logging.error(f"Error calculating EMA200: {e}")
            df['EMA200'] = pd.Series([0] * len(df))

        try:
            df['EMA21'] = ta.ema(df['close'], length=21) if len(df) > 21 else None
        except Exception as e:
            logging.error(f"Error calculating EMA21: {e}")
            df['EMA21'] = pd.Series([0] * len(df))

        try:
            df['EMA9'] = ta.ema(df['close'], length=9) if len(df) > 9 else None
        except Exception as e:
            logging.error(f"Error calculating EMA9: {e}")
            df['EMA9'] = pd.Series([0] * len(df))

        try:
            df['EMA5'] = ta.ema(df['close'], length=5) if len(df) > 5 else None
        except Exception as e:
            logging.error(f"Error calculating EMA5: {e}")
            df['EMA5'] = pd.Series([0] * len(df))

        try:
            df['EMA4'] = ta.ema(df['close'], length=4) if len(df) > 4 else None
        except Exception as e:
            logging.error(f"Error calculating EMA4: {e}")
            df['EMA4'] = pd.Series([0] * len(df))

        # Calculate VWAP Slope
        try:
            df['VWAP_Slope'] = ta.slope(df['VWAP'], length=10)
        except Exception as e:
            logging.error(f"Error calculating VWAP Slope: {e}")
            df['VWAP_Slope'] = pd.Series([0] * len(df))

        # Volume Ratio
        df = calculate_vr(df)

        # ROC
        try:
            df['ROC'] = ta.roc(df['close'], length=14)
        except Exception as e:
            logging.error(f"Error calculating ROC: {e}")
            df['ROC'] = pd.Series([0] * len(df))

        # Williams %R
        try:
            df['Williams_R'] = ta.willr(df['high'], df['low'], df['close'], length=14)
        except Exception as e:
            logging.error(f"Error calculating Williams %R: {e}")
            df['Williams_R'] = pd.Series([0] * len(df))

        # Calculate ATR
        try:
            df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14, mamode='sma')
        except Exception as e:
            logging.error(f"Error calculating ATR: {e}")
            df['ATR'] = pd.Series([0] * len(df))

        # HOD (High of Day)
        try:
            df['HOD'] = df['high'].expanding().max()
        except Exception as e:
            logging.error(f"Error calculating HOD: {e}")
            df['HOD'] = pd.Series([0] * len(df))

        # ATR to HOD
        try:
            df['ATR_to_HOD'] = abs(df['HOD'] - df['close']) / df['ATR']
            df['ATR_to_HOD'] = np.where(df['ATR'] < 0.001, 1000, abs(df['HOD'] - df['close']) / df['ATR'])
        except Exception as e:
            logging.error(f"Error calculating ATR to HOD: {e}")
            df['ATR_to_HOD'] = pd.Series([0] * len(df))

        # ATR to VWAP
        try:
            df['ATR_to_VWAP'] = abs(df['close'] - df['VWAP']) / df['ATR']
            df['ATR_to_VWAP'] = np.where(df['ATR'] < 0.001, 1000, abs(df['close'] - df['VWAP']) / df['ATR'])
        except Exception as e:
            logging.error(f"Error calculating ATR to VWAP: {e}")
            df['ATR_to_VWAP'] = pd.Series([0] * len(df))

        try:
            df['ZenP'] = np.where(df['ATR'] > 0, (df['high'] - df['low']) / df['ATR'], 0)
        except Exception as e:
            logging.error(f"Error calculating ZenP: {e}")
            df['ZenP'] = pd.Series([0] * len(df))

        # RVOL
        try:
            volume_ma = df['volume'].shift().rolling(window=14).mean()
            df['RVol'] = np.where(volume_ma == 0, 0, df['volume'] / volume_ma)
        except Exception as e:
            logging.error(f"Error calculating RVol: {e}")
            df['RVol'] = pd.Series([0] * len(df))

        # Bollinger Band
        try:
            bbands = ta.bbands(df['close'], 20)
            if bbands is not None:
                df['BB_lower'] = bbands.get('BBL_20_2.0', pd.Series([0] * len(df)))
                df['BB_mid'] = bbands.get('BBM_20_2.0', pd.Series([0] * len(df)))
                df['BB_upper'] = bbands.get('BBU_20_2.0', pd.Series([0] * len(df)))
            else:
                df['BB_lower'] = pd.Series([0] * len(df))
                df['BB_mid'] = pd.Series([0] * len(df))
                df['BB_upper'] = pd.Series([0] * len(df))
        except Exception as e:
            logging.error(f"Error calculating Bollinger Band: {e}")
            df['BB_lower'] = pd.Series([0] * len(df))
            df['BB_mid'] = pd.Series([0] * len(df))
            df['BB_upper'] = pd.Series([0] * len(df))

        # Fill NaN values with 0
        df = df.fillna(0)

        # Get ask and bid price from last orderbook snapshot
        orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
        if orderbook:
            ask_price = orderbook['asks'][0][0]
            bid_price = orderbook['bids'][0][0]
        else:
            ask_price = 0
            bid_price = 0

        try:
            ATR_Spread = abs(ask_price - bid_price) / df['ATR'].iloc[-1]
            ATR_Spread = min(ATR_Spread, 1000)
        except Exception as e:
            logging.error(f"Error calculating ATR Spread: {e}")
            ATR_Spread = 0

        levels_data = calculate_key_levels(df['close'].tolist(), df['volume'].tolist())
        key_levels = levels_data.get('key_levels', [])
        support_resistance = levels_data.get('support_resistance', [])

        # Create Redis pipeline
        pipe = redis_manager.redis_client.pipeline()

        pipe.delete(f'stocks:{ticker}:VWAP')
        pipe.rpush(f"stocks:{ticker}:VWAP", *df['VWAP'].tolist())

        pipe.delete(f'stocks:{ticker}:RSI')
        pipe.rpush(f"stocks:{ticker}:RSI", *df['RSI'].tolist())

        pipe.delete(f'stocks:{ticker}:StochRSI_K')
        pipe.rpush(f"stocks:{ticker}:StochRSI_K", *df['StochRSI_K'].tolist())

        pipe.delete(f'stocks:{ticker}:StochRSI_D')
        pipe.rpush(f"stocks:{ticker}:StochRSI_D", *df['StochRSI_D'].tolist())

        pipe.delete(f'stocks:{ticker}:MACD')
        pipe.rpush(f"stocks:{ticker}:MACD", *df['MACD'].tolist())

        pipe.delete(f'stocks:{ticker}:MACD_signal')
        pipe.rpush(f"stocks:{ticker}:MACD_signal", *df['MACD_signal'].tolist())

        pipe.delete(f'stocks:{ticker}:MACD_hist')
        pipe.rpush(f"stocks:{ticker}:MACD_hist", *df['MACD_hist'].tolist())

        pipe.delete(f'stocks:{ticker}:ADX')
        pipe.rpush(f"stocks:{ticker}:ADX", *df['ADX'].tolist())

        pipe.delete(f'stocks:{ticker}:DMP')
        pipe.rpush(f"stocks:{ticker}:DMP", *df['DMP'].tolist())

        pipe.delete(f'stocks:{ticker}:DMN')
        pipe.rpush(f"stocks:{ticker}:DMN", *df['DMN'].tolist())

        pipe.delete(f'stocks:{ticker}:Supertrend')
        pipe.rpush(f"stocks:{ticker}:Supertrend", *df['Supertrend'].tolist())

        pipe.delete(f'stocks:{ticker}:Trend')
        pipe.rpush(f"stocks:{ticker}:Trend", *df['Trend'].tolist())

        pipe.delete(f'stocks:{ticker}:PSAR_L')
        pipe.rpush(f"stocks:{ticker}:PSAR_L", *df['PSAR_L'].tolist())

        pipe.delete(f'stocks:{ticker}:PSAR_S')
        pipe.rpush(f"stocks:{ticker}:PSAR_S", *df['PSAR_S'].tolist())

        pipe.delete(f'stocks:{ticker}:PSAR_R')
        pipe.rpush(f"stocks:{ticker}:PSAR_R", *df['PSAR_R'].tolist())

        pipe.delete(f'stocks:{ticker}:EMA200')
        pipe.rpush(f"stocks:{ticker}:EMA200", *df['EMA200'].tolist())

        pipe.delete(f'stocks:{ticker}:EMA21')
        pipe.rpush(f"stocks:{ticker}:EMA21", *df['EMA21'].tolist())

        pipe.delete(f'stocks:{ticker}:EMA9')
        pipe.rpush(f"stocks:{ticker}:EMA9", *df['EMA9'].tolist())

        pipe.delete(f'stocks:{ticker}:EMA4')
        pipe.rpush(f"stocks:{ticker}:EMA4", *df['EMA4'].tolist())

        pipe.delete(f'stocks:{ticker}:EMA5')
        pipe.rpush(f"stocks:{ticker}:EMA5", *df['EMA5'].tolist())

        pipe.delete(f'stocks:{ticker}:VWAP_Slope')
        pipe.rpush(f"stocks:{ticker}:VWAP_Slope", *df['VWAP_Slope'].tolist())

        pipe.delete(f'stocks:{ticker}:Volume_Ratio')
        pipe.rpush(f"stocks:{ticker}:Volume_Ratio", *df['Volume_Ratio'].tolist())

        pipe.delete(f'stocks:{ticker}:ROC')
        pipe.rpush(f"stocks:{ticker}:ROC", *df['ROC'].tolist())

        pipe.delete(f'stocks:{ticker}:Williams_R')
        pipe.rpush(f"stocks:{ticker}:Williams_R", *df['Williams_R'].tolist())

        pipe.delete(f'stocks:{ticker}:ATR')
        pipe.rpush(f"stocks:{ticker}:ATR", *df['ATR'].tolist())

        pipe.delete(f'stocks:{ticker}:HOD')
        pipe.rpush(f"stocks:{ticker}:HOD", *df['HOD'].tolist())

        pipe.delete(f'stocks:{ticker}:ATR_to_HOD')
        pipe.rpush(f"stocks:{ticker}:ATR_to_HOD", *df['ATR_to_HOD'].tolist())

        pipe.delete(f'stocks:{ticker}:ATR_to_VWAP')
        pipe.rpush(f"stocks:{ticker}:ATR_to_VWAP", *df['ATR_to_VWAP'].tolist())

        pipe.delete(f'stocks:{ticker}:ZenP')
        pipe.rpush(f"stocks:{ticker}:ZenP", *df['ZenP'].tolist())

        pipe.delete(f'stocks:{ticker}:RVol')
        pipe.rpush(f"stocks:{ticker}:RVol", *df['RVol'].tolist())

        pipe.delete(f'stocks:{ticker}:BB_lower')
        pipe.rpush(f"stocks:{ticker}:BB_lower", *df['BB_lower'].tolist())

        pipe.delete(f'stocks:{ticker}:BB_mid')
        pipe.rpush(f"stocks:{ticker}:BB_mid", *df['BB_mid'].tolist())

        pipe.delete(f'stocks:{ticker}:BB_upper')
        pipe.rpush(f"stocks:{ticker}:BB_upper", *df['BB_upper'].tolist())

        pipe.set(f"stocks:{ticker}:ATR_Spread", ATR_Spread)

        pipe.set(f"stocks:{ticker}:key_levels", json.dumps(key_levels))

        pipe.set(f"stocks:{ticker}:support_resistance", json.dumps(support_resistance))

        # Execute pipeline
        pipe.execute()

        update_technical_scores(ticker)

    except Exception as e:
        logging.error(f"Error getting technical analysis: {e}")
        # If pipeline exists but wasn't executed due to error
        if 'pipe' in locals():
            pipe.reset()

def update_technical_scores(ticker: str):
    try:
        pipe = redis_manager.redis_client.pipeline()

        # Volume Score
        volume_score = calculate_volume_score(ticker)
        pipe.set(f"stocks:{ticker}:volume_score", volume_score)
        
        # Momentum Score
        momentum_score = calculate_momentum_score(ticker)
        pipe.set(f"stocks:{ticker}:momentum_score", momentum_score)
        
        # Trend Score
        trend_score = calculate_trend_score(ticker)
        pipe.set(f"stocks:{ticker}:trend_score", trend_score)

        # Volatility Score
        volatility_score = calculate_volatility_score(ticker)
        pipe.set(f"stocks:{ticker}:volatility_score", volatility_score)
        
        # Calculate technical score
        total_score = volume_score * 3.0 + momentum_score * 2.0 + trend_score * 1.5
        total_weight = 6.5
        technical_score = total_score / total_weight if total_weight > 0 else 0
        pipe.set(f"stocks:{ticker}:technical_score", round(technical_score, 2))

        # Calculate confirmation score
        confirmation_score = trend_score * 0.3 + momentum_score * 0.3 + volume_score * 0.2 + volatility_score * 0.2
        pipe.set(f"stocks:{ticker}:confirmation_score", round(confirmation_score, 2))

        pipe.execute()

    except Exception as e:
        logging.error(f"Error calculating scores: {e}")

def is_choppy_market(ticker, x=0.05, n=7):
    try:
        candles = redis_manager.get_last_n_candles(ticker, n)
        vwaps = redis_manager.get_technical_indicator(ticker, 'VWAP', n)
        atrs = redis_manager.get_technical_indicator(ticker, 'ATR', n)
        if len(candles) < n or len(vwaps) < n or len(atrs) < n:
            return False

        # Calculate the average of the last n candles
        closes = np.array([candle['close'] for candle in candles])
        vwaps = np.array(vwaps)
        atrs = np.array(atrs)

        # Calculate the average of the last n vwaps
        diffs = np.abs(closes - vwaps)
        threshold = x * atrs

        # Check if all the differences exceed the threshold
        return np.all(diffs < threshold)
    except Exception as e:
        logging.error(f"Error in is_choppy_market: {e}")
        return False

def calculate_liquidity_absorption(ticker):
    """
    Calculate liquidity absorption score (0-1)
    """
    try:
        orderbooks = redis_manager.get_orderbook(ticker)
        avg_30d_volume = redis_manager.get_avg_30d_volume(ticker)
        if len(orderbooks) < 2 or not avg_30d_volume:
            return 0.0

        # Large Print Threshold
        lpt = int(avg_30d_volume) / 5000

        current_window = [item for item in orderbooks if item['timestamp'] >= time.time() - 30]

        if len(current_window) < 2:
            return 0.0

        current_offers_top5 = sum(ask[1] for ask in current_window[-1]['asks'][:5])
        prior_offers_top5 = sum(ask[1] for ask in current_window[0]['asks'][:5])

        if current_offers_top5 <= 0 or prior_offers_top5 <= 0:
            return 0.0

        offers_decrease_pct = ((prior_offers_top5 - current_offers_top5) / prior_offers_top5) * 100

        # Check for new block offers
        no_new_block_offers = True
        for ask in orderbooks[-1]['asks']:
            if ask[1] > 2 * lpt:
                no_new_block_offers = False
                break

        if offers_decrease_pct >= 25 and no_new_block_offers:
            return 1.0
        elif offers_decrease_pct >= 10:
            return 0.6
        else:
            return 0.0

    except Exception as e:
        logging.error(f"Error calculating liquidity absorption: {e}")
        return 0.0

def calculate_trend_score(ticker):
    score = 0
    signals = []
    try:
        # Get all required data
        ema21 = redis_manager.get_technical_indicator(ticker, 'EMA21', 2)
        ema9 = redis_manager.get_technical_indicator(ticker, 'EMA9', 2)
        vwap = redis_manager.get_technical_indicator(ticker, 'VWAP', 1)
        adx = redis_manager.get_technical_indicator(ticker, 'ADX', 1)
        current_price = redis_manager.get_stock_price(ticker)

        # EMA 9/21 Crossover
        if len(ema9) >= 2 and len(ema21) >= 2:
            ema9_current = ema9[-1]
            ema21_current = ema21[-1]
            ema9_prev = ema9[-2]
            ema21_prev = ema21[-2]

            if ema9_current > ema21_current and ema9_current > ema9_prev:
                signals.append(('EMA9>EMA21 with positive slope', 1))
            elif ema9_current > ema21_current:
                signals.append(('EMA9>EMA21', 0.5))
            else:
                signals.append(('EMA9<=EMA21', 0))

        # VWAP
        if vwap:
            if current_price > vwap:
                signals.append(('Price > VWAP', 1))
            else:
                signals.append(('Price <= VWAP', 0))

        # ADX
        if adx:
            if adx > 25:
                signals.append(('Strong trend (ADX>25)', 1))
            else:
                signals.append(('Moderate trend', 0))

        # Choppy market
        if is_choppy_market(ticker):
            signals.append(('Choppy market', 0))
        else:
            signals.append(('No choppy market', 1))

        # Calculate trend score
        if signals:
            trend_score = sum(signal[1] for signal in signals) / len(signals)
            score = min(1, trend_score)

        return score
    except Exception as e:
        logging.error(f"Error in calculate_trend_score {ticker}: {e}")
        return 0

def calculate_momentum_score(ticker):
    score = 0
    try:
        ema4 = redis_manager.get_technical_indicator(ticker, 'EMA4', 1)
        ema5 = redis_manager.get_technical_indicator(ticker, 'EMA5', 1)
        vwap = redis_manager.get_technical_indicator(ticker, 'VWAP', 1)
        adx = redis_manager.get_technical_indicator(ticker, 'ADX', 1)
        rvol = redis_manager.get_technical_indicator(ticker, 'RVol', 1)
        roc = redis_manager.get_technical_indicator(ticker, 'ROC', 1)
        orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
        tick_data = redis_manager.get_tick(ticker)
        if ema4 > vwap and ema5 > vwap:
            score += 0.15
        if adx >= 30:
            score += 0.15
        if rvol >= 3:
            score += 0.2
        if len(tick_data):
            buy_volume = sum([tick['volume'] for tick in tick_data if tick['ticker_direction'] == 'BUY'])
            sell_volume = sum([tick['volume'] for tick in tick_data if tick['ticker_direction'] == 'SELL'])
            volume_delta = buy_volume - sell_volume
            score += 0.15 if volume_delta > 0 else 0
        if orderbook and orderbook['imbalance'] > 0.3:
            score += 0.15
        if roc > 0:
            score += 0.1
        if calculate_liquidity_absorption(ticker) > 0.5:
            score += 0.1

        return score

    except Exception as e:
        logging.error(f"Error in calculate_momentum_score {ticker}: {e}")
        return 0

def _volume_ratio_n_period(ticker, n):
    try:
        candles = redis_manager.get_last_n_candles(ticker, n)
        ratio = 0
        if len(candles) == n:
            current_volume = candles[-1]['volume']
            avg_volume = sum([candle['volume'] for candle in candles[:-1]]) / len(candles[:-1])
            if avg_volume > 0:
                ratio = current_volume / avg_volume

        return ratio
    except Exception as e:
        logging.error(f"Error in _volume_ratio_n_period {ticker} {n}: {e}")
        return 0

def calculate_volume_score(ticker):
    score = 0
    signals = []
    try:
        # Volume Spike Ratio
        volume_ratio = _volume_ratio_n_period(ticker, 10)
        if volume_ratio >= 2.0:
            signals.append(('Volume spike 2x+', 1))
        elif volume_ratio >= 1.5:
            signals.append(('Volume spike 1.5x+', 0.75))
        elif volume_ratio >= 1.2:
            signals.append(('Volume spike 1.2x+', 0.5))
        else:
            signals.append(('Normal volume', 0))

        orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
        # Bid/Ask Volume Ratio (A2V) - from orderbook
        if orderbook:
            bid_volume = orderbook['bid_volume']
            ask_volume = orderbook['ask_volume']

            if ask_volume > 0:
                a2v_ratio = bid_volume / ask_volume
                if a2v_ratio >= 2.0:
                    signals.append(('A2V ratio 2.0+', 1))
                elif a2v_ratio >= 1.5:
                    signals.append(('A2V ratio 1.5+', 0.75))
                elif a2v_ratio >= 1.2:
                    signals.append(('A2V ratio 1.2+', 0.5))
                else:
                    signals.append(('A2V ratio < 1.2', 0))

        # Liquidity Absorption Score
        absorption_score = calculate_liquidity_absorption(ticker)
        if absorption_score >= 0.8:
            signals.append(('High absorption (80%+)', 1))
        elif absorption_score >= 0.6:
            signals.append(('Moderate absorption (60%+)', 0.5))
        else:
            signals.append(('Low absorption', 0))

        # Calculate volume/microstructure score
        if signals:
            volume_score = sum(signal[1] for signal in signals) / len(signals)
            score = max(-1, min(1, volume_score))

        return score

    except Exception as e:
        logging.error(f"Error in calculate_volume_score {ticker}: {e}")
        return 0

def calculate_volatility_score(ticker):
    score = 0
    signals = []
    try:
        # Bollinger Bands
        bb_upper = redis_manager.get_technical_indicator(ticker, 'BB_upper', 1)
        bb_lower = redis_manager.get_technical_indicator(ticker, 'BB_lower', 1)
        volume_ratio = _volume_ratio_n_period(ticker, 10)
        current_price = redis_manager.get_stock_price(ticker)
        if bb_upper and bb_lower:
            if current_price > bb_upper and volume_ratio > 1.5:
                signals.append(('BB breakout with volume surge', 1))
            elif current_price < bb_lower:
                signals.append(('BB breakdown', -1))
            else:
                signals.append(('BB within bands', 0))

        # ATR (14)
        ATRs = redis_manager.get_technical_indicator(ticker, 'ATR', 2)
        if ATRs:
            atr_current = ATRs[-1]
            atr_prev = ATRs[-2]

            if atr_current > atr_prev:
                signals.append(('ATR rising', 1))
            elif atr_current < atr_prev:
                signals.append(('ATR falling', -1))
            else:
                signals.append(('ATR stable', 0))

        # Calculate volatility score
        if signals:
            volatility_score = sum(signal[1] for signal in signals) / len(signals)
            score = max(-1, min(1, volatility_score))

        return score

    except Exception as e:
        logging.error(f"Error in calculate_volatility_score {ticker}: {e}")
        return 0
