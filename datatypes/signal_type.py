from enum import Enum

class SignalType(Enum):
    PULLBACK = "Pullback"
    BULLISH_REVERSAL = "Bullish Reversal"
    BEARISH_REVERSAL = "Bearish Reversal"
    ACCUMULATION = "Institutional Accumulation"
    DISTRIBUTION = "Institutional Distribution"
    BREAKOUT_IMMINENT = "Breakout Imminent"
    MOMENTUM_SURGE = "Momentum Surge"
    EXHAUSTION = "Exhaustion Point"
    LIQUIDITY_GRAB = "Liquidity Grab"
    NO_SIGNAL = "No Signal"