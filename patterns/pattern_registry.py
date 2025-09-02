from typing import Dict, Type, List
from .base_pattern import BasePattern

class PatternRegistry:
    """Registry for managing available trading patterns"""
    
    _patterns: Dict[str, Type[BasePattern]] = {}
    
    @classmethod
    def register(cls, pattern_class: Type[BasePattern]) -> Type[BasePattern]:
        """Register a new pattern class"""
        cls._patterns[pattern_class.__name__] = pattern_class
        return pattern_class
    
    @classmethod
    def get_pattern(cls, pattern_name: str) -> Type[BasePattern]:
        """Get a pattern class by name"""
        return cls._patterns.get(pattern_name)
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, Type[BasePattern]]:
        """Get all registered patterns"""
        return cls._patterns.copy()

    @classmethod
    def get_patterns_by_category(cls, category: str) -> List[Type[BasePattern]]:
        """Get patterns filtered by category"""
        return [p for p in cls._patterns.values() if category in p.categories] 