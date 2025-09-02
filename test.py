import os
import pytz
import numpy as np
from polygon import RESTClient
from moomoo import *
import pandas_ta as ta
from utils.util import get_short_ticker, get_session_from_time

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
        df['Volume_Ratio'] = 100 * (df['TH'] * 2 + df['TQ']) / (df['TL'] * 2 + df['TQ'])

        # Clean up intermediate columns
        df.drop(['LC', 'price_rise', 'price_fall', 'price_unchanged',
                'vol_rise', 'vol_fall', 'vol_unchanged', 'TH', 'TL', 'TQ'],
                axis=1, inplace=True)

        return df

    except Exception as e:
        print(f"Error calculating VR: {e}")
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
        print(f"Error calculating custom MACD: {e}")
        return {
            'MACD': pd.Series([0] * len(df)),
            'MACD_signal': pd.Series([0] * len(df)),
            'MACD_hist': pd.Series([0] * len(df))
        }

def initialize_technical_indicators(candles):
    try:
        # Validate input data
        if not candles or not isinstance(candles, list):
            print("Candlestick data is not ready for technical indicators")
            return

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
        try:
            # Calculate VWAP for each session per day
            vwap_results = []
            for (date, session), group in df.groupby([df.index.date, 'Session']):
                if session != 'closed':  # Skip closed hours
                    vwap = ta.vwap(
                        high=group['high'],
                        low=group['low'],
                        close=group['close'],
                        volume=group['volume']
                    )
                    group['VWAP'] = vwap
                    vwap_results.append(group)

            # Combine all results back into the main DataFrame
            if vwap_results:  # Only proceed if we have valid VWAP calculations
                df_with_vwap = pd.concat(vwap_results)
                df['VWAP'] = df_with_vwap['VWAP']
            else:
                df['VWAP'] = 0
                print("No valid VWAP calculations - possibly missing session data")
        except Exception as e:
            print(f"Error calculating session VWAP: {e}")
            df['VWAP'] = 0

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
            print(f"Error calculating MACD: {e}")
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
            print(f"Error calculating ADX: {e}")
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
            print(f"Error calculating Supertrend: {e}")
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
            print(f"Error calculating PSAR: {e}")
            df['PSAR_L'] = pd.Series([0] * len(df))
            df['PSAR_S'] = pd.Series([0] * len(df))
            df['PSAR_AF'] = pd.Series([0] * len(df))
            df['PSAR_R'] = pd.Series([0] * len(df))

        # EMA 200
        try:
            df['EMA200'] = ta.ema(df['close'], length=200) if len(df) > 200 else None
        except Exception as e:
            print(f"Error calculating EMA200: {e}")
            df['EMA200'] = pd.Series([0] * len(df))

        try:
            df['EMA50'] = ta.ema(df['close'], length=50) if len(df) > 50 else None
        except Exception as e:
            print(f"Error calculating EMA50: {e}")
            df['EMA50'] = pd.Series([0] * len(df))
        try:
            df['EMA20'] = ta.ema(df['close'], length=20) if len(df) > 20 else None
        except Exception as e:
            print(f"Error calculating EMA20: {e}")
            df['EMA20'] = pd.Series([0] * len(df))

        try:
            df['EMA4'] = ta.ema(df['close'], length=4) if len(df) > 4 else None
        except Exception as e:
            print(f"Error calculating EMA4: {e}")
            df['EMA4'] = pd.Series([0] * len(df))

        try:
            df['EMA5'] = ta.ema(df['close'], length=5) if len(df) > 5 else None
        except Exception as e:
            print(f"Error calculating EMA5: {e}")
            df['EMA5'] = pd.Series([0] * len(df))

        # Calculate VWAP Slope
        try:
            df['VWAP_Slope'] = ta.slope(df['VWAP'], length=10)
        except Exception as e:
            print(f"Error calculating VWAP Slope: {e}")
            df['VWAP_Slope'] = pd.Series([0] * len(df))

        # Volume Ratio
        df = calculate_vr(df)

        # ROC
        try:
            df['ROC'] = ta.roc(df['close'], length=14)
        except Exception as e:
            print(f"Error calculating ROC: {e}")
            df['ROC'] = pd.Series([0] * len(df))

        # Williams %R
        try:
            df['Williams_R'] = ta.willr(df['high'], df['low'], df['close'], length=14)
        except Exception as e:
            print(f"Error calculating Williams %R: {e}")
            df['Williams_R'] = pd.Series([0] * len(df))

        # Calculate ATR
        try:
            df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14, mamode='sma')
        except Exception as e:
            print(f"Error calculating ATR: {e}")
            df['ATR'] = pd.Series([0] * len(df))

        # HOD (High of Day)
        try:
            df['HOD'] = df['high'].expanding().max()
        except Exception as e:
            print(f"Error calculating HOD: {e}")
            df['HOD'] = pd.Series([0] * len(df))

        # ATR to HOD
        try:
            df['ATR_to_HOD'] = abs(df['HOD'] - df['close']) / df['ATR']
        except Exception as e:
            print(f"Error calculating ATR to HOD: {e}")
            df['ATR_to_HOD'] = pd.Series([0] * len(df))

        # ATR to VWAP
        try:
            df['ATR_to_VWAP'] = abs(df['close'] - df['VWAP']) / df['ATR']
        except Exception as e:
            print(f"Error calculating ATR to VWAP: {e}")
            df['ATR_to_VWAP'] = pd.Series([0] * len(df))

        try:
            df['ZenP'] = np.where(df['ATR'] > 0, (df['high'] - df['low']) / df['ATR'], 0)
        except Exception as e:
            print(f"Error calculating ZenP: {e}")
            df['ZenP'] = pd.Series([0] * len(df))

        # RVOL
        try:
            df['RVol'] = df['volume'] / df['volume'].shift().rolling(window=14).mean()
        except Exception as e:
            print(f"Error calculating RVol: {e}")
            df['RVol'] = pd.Series([0] * len(df))

        df.fillna(0)
        return df
    except Exception as e:
        print(e)

def get_candles(ticker):
    client = RESTClient(os.getenv('POLYGON_API_KEY'))
    start = '2025-08-05'
    end = '2025-08-06'
    candles = []
    for a in client.list_aggs(
        get_short_ticker(ticker),
        1,
        "minute",
        start,
        end,
        adjusted=True,
        sort="asc"
    ):
        utc_dt = datetime.fromtimestamp(a.timestamp/1000, tz=pytz.UTC) + timedelta(minutes=1)
        est_dt = utc_dt.astimezone(pytz.timezone('US/Eastern'))
        candles.append({
            'timestamp': est_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'open': a.open,
            'high': a.high,
            'low': a.low,
            'close': a.close,
            'volume': a.volume
        })
    return candles

if __name__ == '__main__':
    SysConfig.enable_proto_encrypt(True)
    SysConfig.set_init_rsa_file("moomoo1/rsa.txt")
    quote_ctx = OpenQuoteContext('69.197.187.190', 8080)
    ticker = 'CREG'
    candles = []
    if not ticker.startswith('US.'):
        ticker = 'US.' + ticker
    ret, data, _ = quote_ctx.request_history_kline(ticker, start='2025-08-05', end='2025-08-06', ktype=KLType.K_1M, extended_time=True, max_count=None)
    if ret != RET_OK:
        print('error')
    data['timestamp'] = data['time_key']
    candles_data = data[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    candles = candles_data.to_dict(orient='records')
    # candles = get_candles(ticker)
    result = initialize_technical_indicators(candles)
    print(result)