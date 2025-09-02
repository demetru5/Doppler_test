from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

class NoteType(Enum):
    POSITIVE = "positive"
    WARNING = "warning"
    DANGER = "danger"

class NotePriority(Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    NORMAL = "normal"

@dataclass
class MarketNote:
    message: str
    type: NoteType
    priority: NotePriority
    icon: Optional[str] = None
    is_strategy: bool = False
    strategy_details: Optional[Dict] = None
    timestamp: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            'message': self.message,
            'type': self.type.value,
            'priority': self.priority.value,
            'icon': self.icon,
            'is_strategy': self.is_strategy,
            'strategy_details': self.strategy_details,
            'timestamp': self.timestamp
        } 