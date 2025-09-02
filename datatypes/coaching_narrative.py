from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List, Any

class NarrativeState(Enum):
    ANALYZING = "ANALYZING"
    SETUP_WEAK = "SETUP_WEAK"
    STRATEGY_FOUND = "STRATEGY_FOUND"
    WAITING_FOR_ENTRY = "WAITING_FOR_ENTRY"
    ENTRY_APPROACHING = "ENTRY_APPROACHING"
    ENTRY_ZONE = "ENTRY_ZONE"
    IN_POSITION = "IN_POSITION"
    POSITION_BUILDING = "POSITION_BUILDING"
    APPROACHING_TARGET = "APPROACHING_TARGET"
    EXIT_WARNING = "EXIT_WARNING"
    APPROACHING_STOP = "APPROACHING_STOP"
    TRADE_UNDER_PRESSURE = "TRADE_UNDER_PRESSURE"
    STRATEGY_FAILED = "STRATEGY_FAILED"
    STRATEGY_COMPLETE = "STRATEGY_COMPLETE"
    SCALING_OPPORTUNITY = "SCALING_OPPORTUNITY"
    MARKET_SHIFT = "MARKET_SHIFT"

@dataclass
class CoachingNarrative:
    state: NarrativeState
    message: str
    context: Dict
    timestamp: float
    confidence: float = 0.0
    warning_reason: Optional[str] = None
    order_flow_insights: Optional[Dict] = None
    technical_insights: Optional[Dict] = None
    recommendations: Optional[List[str]] = None
    exit_strategy: Optional[Dict] = None
    probability: float = 0.65

    def to_dict(self) -> Dict:
        return {
            'state': self.state.value,
            'message': self.message,
            'context': self.context,
            'timestamp': self.timestamp,
            'confidence': self.confidence,
            'warning_reason': self.warning_reason,
            'order_flow_insights': self.order_flow_insights,
            'technical_insights': self.technical_insights,
            'recommendations': self.recommendations,
            'exit_strategy': self.exit_strategy,
            'probability': self.probability
        } 