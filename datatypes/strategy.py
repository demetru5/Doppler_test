from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, field

class StrategyState:
    ANALYZING = "ANALYZING"
    LOCKED = "LOCKED"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"

@dataclass
class TargetLevel:
    price: float
    timestamp: datetime = None
    achieved: bool = False
    achieved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'price': self.price,
            'timestamp': self.timestamp if self.timestamp else None,
            'achieved': self.achieved,
            'achieved_at': self.achieved_at if self.achieved_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TargetLevel':
        target = cls(price=data['price'], achieved=data.get('achieved', False))
        if 'timestamp' in data and data['timestamp']:
            target.timestamp = data['timestamp']
        if 'achieved_at' in data and data['achieved_at']:
            target.achieved_at = data['achieved_at']
        return target

@dataclass
class Strategy:
    name: str
    state: str = StrategyState.ANALYZING
    entry_price: float = 0.0
    target_price: float = 0.0
    stop_price: float = 0.0
    lock_time: Optional[datetime] = None
    buy_time: Optional[datetime] = None
    hold_time: Optional[datetime] = None
    probability: float = 0.0
    match_score: float = 0.0
    pattern_type: str = ""
    description: str = ""
    completion_type: Optional[str] = None
    completion_time: Optional[datetime] = None
    target_history: List[TargetLevel] = field(default_factory=list)
    current_target_index: int = 0
    max_targets: int = 3  # Limit the number of targets to prevent excessive growth
    # indicators
    VWAP: float = 0.0
    RSI: float = 0.0
    StochRSI_K: float = 0.0
    StochRSI_D: float = 0.0
    MACD: float = 0.0
    MACD_signal: float = 0.0
    MACD_hist: float = 0.0
    ADX: float = 0.0
    DMP: float = 0.0
    DMN: float = 0.0
    Supertrend: float = 0.0
    Trend: float = 0.0
    PSAR_L: float = 0.0
    PSAR_S: float = 0.0
    PSAR_R: float = 0.0
    EMA200: float = 0.0
    EMA21: float = 0.0
    EMA9: float = 0.0
    EMA4: float = 0.0
    EMA5: float = 0.0
    VWAP_Slope: float = 0.0
    Volume_Ratio: float = 0.0
    ROC: float = 0.0
    Williams_R: float = 0.0
    ATR: float = 0.0
    HOD: float = 0.0
    ATR_to_HOD: float = 0.0
    ATR_to_VWAP: float = 0.0
    ZenP: float = 0.0
    RVol: float = 0.0
    BB_lower: float = 0.0
    BB_mid: float = 0.0
    BB_upper: float = 0.0
    ATR_Spread: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'state': self.state,
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_price': self.stop_price,
            'lock_time': self.lock_time if self.lock_time else None,
            'buy_time': self.buy_time if self.buy_time else None,
            'hold_time': self.hold_time if self.hold_time else None,
            'probability': self.probability,
            'match_score': self.match_score,
            'pattern_type': self.pattern_type,
            'description': self.description,
            'completion_type': self.completion_type,
            'completion_time': self.completion_time if self.completion_time else None,
            'target_history': [target.to_dict() for target in self.target_history],
            'current_target_index': self.current_target_index,
            'VWAP': self.VWAP,
            'RSI': self.RSI,
            'StochRSI_K': self.StochRSI_K,
            'StochRSI_D': self.StochRSI_D,
            'MACD': self.MACD,
            'MACD_signal': self.MACD_signal,
            'MACD_hist': self.MACD_hist,
            'ADX': self.ADX,
            'DMP': self.DMP,
            'DMN': self.DMN,
            'Supertrend': self.Supertrend,
            'Trend': self.Trend,
            'PSAR_L': self.PSAR_L,
            'PSAR_S': self.PSAR_S,
            'PSAR_R': self.PSAR_R,
            'EMA200': self.EMA200,
            'EMA21': self.EMA21,
            'EMA9': self.EMA9,
            'EMA4': self.EMA4,
            'EMA5': self.EMA5,
            'VWAP_Slope': self.VWAP_Slope,
            'Volume_Ratio': self.Volume_Ratio,
            'ROC': self.ROC,
            'Williams_R': self.Williams_R,
            'ATR': self.ATR,
            'HOD': self.HOD,
            'ATR_to_HOD': self.ATR_to_HOD,
            'ATR_to_VWAP': self.ATR_to_VWAP,
            'ZenP': self.ZenP,
            'RVol': self.RVol,
            'BB_lower': self.BB_lower,
            'BB_mid': self.BB_mid,
            'BB_upper': self.BB_upper,
            'ATR_Spread': self.ATR_Spread,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Strategy':
        # Handle target history
        target_history = []
        if 'target_history' in data and data['target_history']:
            target_history = [TargetLevel.from_dict(target) for target in data['target_history']]
            
        # Remove these fields from data dict before unpacking
        target_data = data.copy()
        if 'target_history' in target_data:
            del target_data['target_history']
            
        # Create strategy instance
        strategy = cls(**target_data)
        strategy.target_history = target_history
        
        # Initialize target history if empty but we have a target price
        if not strategy.target_history and strategy.target_price > 0:
            strategy.target_history = [TargetLevel(
                price=strategy.target_price,
                timestamp=datetime.now().isoformat()
            )]
        
        return strategy
        
    def update_target(self, new_target: float, reason: str = "price action") -> bool:
        """Add a new target level when the current one is achieved"""
        if not self.target_history:
            # Initialize with the current target if history is empty
            self.target_history = [TargetLevel(
                price=self.target_price,
                timestamp=datetime.now().isoformat()
            )]
            return False
            
        # Check if we need to mark current target as achieved
        current_target = self.target_history[self.current_target_index]
        if not current_target.achieved and new_target > current_target.price:
            current_target.achieved = True
            current_target.achieved_at = datetime.now().isoformat()
            
            # Add new target if we haven't reached the maximum
            if len(self.target_history) < self.max_targets:
                self.target_history.append(TargetLevel(
                    price=new_target,
                    timestamp=datetime.now().isoformat()
                ))
                self.current_target_index = len(self.target_history) - 1
                self.target_price = new_target
                return True
                
        return False 