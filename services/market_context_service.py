import logging
import pytz
import finnhub
import pandas as pd
from datetime import datetime
import logging
from finvizfinance.util import web_scrap
from utils.util import get_current_time

def get_market_time_overview():
    """Get current market time status"""
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    pre_market_start = datetime(now_est.year, now_est.month, now_est.day, 4, 0, 0, tzinfo=est)
    market_open = datetime(now_est.year, now_est.month, now_est.day, 9, 30, 0, tzinfo=est)
    market_close = datetime(now_est.year, now_est.month, now_est.day, 16, 0, 0, tzinfo=est)
    post_market_close = datetime(now_est.year, now_est.month, now_est.day, 20, 0, 0, tzinfo=est)

    return now_est, pre_market_start, market_open, market_close, post_market_close


# Initialize Finnhub client
finnhub_client = finnhub.Client(api_key="cu9nrnhr01qnf5nnh5o0cu9nrnhr01qnf5nnh5og")

##################  1. Intraday S&P 500 Trend (15-min EMA 9 vs. EMA 20)  ###########################
def calculate_intraday_emas(ticker='SPY', interval='15', short_window=9, long_window=20):
    try:
        # Get timestamp for last 5 days
        end_timestamp = int(datetime.now().timestamp())
        start_timestamp = end_timestamp - (5 * 24 * 60 * 60)
        
        # Fetch data from Finnhub
        data = finnhub_client.stock_candles(ticker, interval, start_timestamp, end_timestamp)
        
        if data['s'] != 'ok' or not data['c']:
            return False
            
        # Convert to DataFrame
        df = pd.DataFrame({'Close': data['c']})
        df['Short_EMA'] = df['Close'].ewm(span=short_window, adjust=False).mean()
        df['Long_EMA'] = df['Close'].ewm(span=long_window, adjust=False).mean()
        
        return True if df['Short_EMA'].iloc[-1] > df['Long_EMA'].iloc[-1] else False
    except Exception as e:
        logging.error(f"Error in calculate_intraday_emas: {e}")
        return False

##################  2. NASDAQ & Dow Jones Confirmation (15-min SMA 50) ###########################
def check_intraday_indices_above_moving_average(moving_average_days=50):
    indices = ['QQQ', 'DIA']  # Using ETFs instead of indices
    status = []
    
    end_timestamp = int(datetime.now().timestamp())
    start_timestamp = end_timestamp - (5 * 24 * 60 * 60)
    
    for index in indices:
        try:
            data = finnhub_client.stock_candles(index, '15', start_timestamp, end_timestamp)
            if data['s'] == 'ok' and data['c']:
                df = pd.DataFrame({'Close': data['c']})
                df['50_SMA'] = df['Close'].rolling(window=moving_average_days).mean()
                df = df.dropna()
                
                if not df.empty:
                    last_close = float(df['Close'].iloc[-1])
                    last_sma = float(df['50_SMA'].iloc[-1])
                    status.append(last_close > last_sma)
        except Exception as e:
            logging.error(f"Error fetching data for {index}: {e}")
            
    return all(status)

##################  3. Real-Time VIX Monitoring (5-min Updates) ###########################
def analyze_intraday_vix():
    try:
        end_timestamp = int(datetime.now().timestamp())
        start_timestamp = end_timestamp - (24 * 60 * 60)  # Last 24 hours
        
        data = finnhub_client.stock_candles('UVXY', '5', start_timestamp, end_timestamp)  # Using UVXY as VIX proxy
        
        if data['s'] != 'ok' or not data['c']:
            return 10
            
        first_close = data['c'][0]
        last_close = data['c'][-1]
        current_vix_change = ((last_close - first_close) / first_close) * 100
        
        if current_vix_change < -5:
            return 20
        elif current_vix_change > 10:
            return 0
        else:
            return 10
    except Exception as e:
        logging.error(f"Error in analyze_intraday_vix: {e}")
        return 10

##################  4. Real-Time Market Breadth (A/D Ratio & Put/Call Ratio) ###########################
def get_realtime_ad_ratio():
    try:
        advancing_stocks = web_scrap("https://finviz.com/screener.ashx?v=111&f=ta_change_u&ft=4")
        declining_stocks = web_scrap("https://finviz.com/screener.ashx?v=111&f=ta_change_d&ft=4")
        advancers = int(advancing_stocks.find(id="screener-total").text.split("/")[1].strip())
        decliners = int(declining_stocks.find(id="screener-total").text.split("/")[1].strip())
        return advancers / decliners if decliners > 0 else 1
    except:
        return 1

##################  5. Intraday Sector Strength Analysis (15-min EMA 9 vs. EMA 20) ###########################
def analyze_intraday_sector_strength():
    sectors = ["XLE", "XLF", "XLK", "XLY", "XLV", "XLI"]
    sector_scores = []
    
    end_timestamp = int(datetime.now().timestamp())
    start_timestamp = end_timestamp - (5 * 24 * 60 * 60)
    
    for sector in sectors:
        try:
            data = finnhub_client.stock_candles(sector, '15', start_timestamp, end_timestamp)
            
            if data['s'] == 'ok' and data['c']:
                df = pd.DataFrame({'Close': data['c']})
                df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
                df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
                
                if df['EMA9'].iloc[-1] > df['EMA20'].iloc[-1]:
                    sector_scores.append(10)
        except Exception as e:
            logging.error(f"Error analyzing sector {sector}: {e}")
            
    return sum(sector_scores)

##################  6. Intraday Macro Score Calculation ###########################
def intraday_macro_analysis():
    score = 0
    intraday_emas = calculate_intraday_emas()
    intraday_indices = check_intraday_indices_above_moving_average()
    intraday_vix = analyze_intraday_vix()
    intraday_ad_ratio = get_realtime_ad_ratio()
    intraday_sector_strength = analyze_intraday_sector_strength()
    
    if intraday_emas:
        score += 25
    if intraday_indices:
        score += 20
    score += intraday_vix
    score += intraday_ad_ratio * 10  # A/D ratio scaled to a score
    score += intraday_sector_strength
    
    if score >= 80:
        signal = "Best Momentum Conditions (STRONG_BUY)"
    elif score >= 60:
        signal = "Good Momentum Conditions (BUY)"
    elif score >= 41:
        signal = "Neutral / Mixed Market (HOLD)"
    elif score >= 21:
        signal = "Good Bearish Conditions (WEAK_SELL)"
    else:
        signal = "Best Bearish Conditions (SELL)"
    
    return {
        'score': score,
        'signal': signal,
        'timestamp': get_current_time().strftime('%Y-%m-%d %H:%M:%S'),
        'components': {
            'momentum': intraday_emas,
            'nasdaq_dow': intraday_indices,
            'vix': intraday_vix,
            'breadth': intraday_ad_ratio,
            'sector_strength': intraday_sector_strength
        }
    }