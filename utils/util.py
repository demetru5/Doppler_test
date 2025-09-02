import pytz
from datetime import datetime

def get_current_session() -> str:
    """Determine current market session"""
    est = pytz.timezone('US/Eastern')
    now = datetime.now(est)
    hour = now.hour
    minute = now.minute
    
    if hour == 4 or (hour == 9 and minute <= 30) or (4 < hour < 9):
        return 'premarket'
    elif (hour == 9 and minute > 30) or (9 < hour < 16) or (hour == 16 and minute == 0):
        return 'regular'
    elif (16 <= hour < 20) or (hour == 20 and minute == 0):
        return 'afterhours'
    else:
        return 'closed'

def get_session_from_time(time):
    est = pytz.timezone('US/Eastern')
    time = est.localize(time)
    hour = time.hour
    minute = time.minute

    # Check for premarket session (4:00 AM to 9:30 AM)
    if hour == 4 or (hour == 9 and minute <= 30) or (4 < hour < 9):
        return 'premarket'

    # Check for regular session (9:30 AM to 4:00 PM)
    elif (hour == 9 and minute > 30) or (9 < hour < 16) or (hour == 16 and minute == 0):
        return 'regular'

    # Check for afterhours session (4:00 PM to 8:00 PM)
    elif (16 <= hour < 20) or (hour == 20 and minute == 0):
        return 'afterhours'

    # Outside of trading hours
    else:
        return 'closed'

def get_today_session_point_time(session_name, point, as_string=False):
    """
    Get the time of a session point
    session_name: 'premarket', 'regular', 'afterhours'
    point: 'open', 'close'
    """
    est = pytz.timezone('US/Eastern')
    today = datetime.now(est)
    today_session_point_time = None
    if session_name == 'premarket':
        if point == 'open':
            today_session_point_time = datetime(today.year, today.month, today.day, 4, 1, 0)
        elif point == 'close':
            today_session_point_time = datetime(today.year, today.month, today.day, 9, 30, 0)
    elif session_name == 'regular':
        if point == 'open':
            today_session_point_time = datetime(today.year, today.month, today.day, 9, 31, 0)
        elif point == 'close':
            today_session_point_time = datetime(today.year, today.month, today.day, 16, 0, 0)
    elif session_name == 'afterhours':
        if point == 'open':
            today_session_point_time = datetime(today.year, today.month, today.day, 16, 1, 0)
        elif point == 'close':
            today_session_point_time = datetime(today.year, today.month, today.day, 20, 0, 0)

    if as_string:
        return today_session_point_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return today_session_point_time

def get_current_time():
    est = pytz.timezone('US/Eastern')
    return datetime.now(est)

def apply_offset_est(time):
    est = pytz.timezone('US/Eastern')
    return est.localize(time)

def get_moomoo_ticker(ticker):
    return ticker if ticker.startswith('US.') else f"US.{ticker}"

def get_short_ticker(ticker):
    return ticker.split('.')[1] if ticker.startswith('US.') else ticker

def get_index(list_data, element):
    try:
        return list_data.index(element)
    except:
        return None

def get_minute_string(second_string):
    timestamp = datetime.strptime(second_string, '%Y-%m-%d %H:%M:%S')
    timestamp = timestamp.replace(second=0)
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')