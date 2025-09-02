import logging
import time
import random
from typing import Dict, List, Optional, Tuple
from datatypes.coaching_narrative import CoachingNarrative, NarrativeState
from datatypes.strategy import StrategyState
from services.redis_manager import redis_manager

class TradingCoachingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        self.narrative_templates = {
            NarrativeState.ANALYZING: [
                "I'm carefully scanning the market right now, looking for the perfect setup for you. I'll let you know as soon as I find something promising.",
                "Hey there! I'm analyzing all the data streams right now. Give me a moment while I look for high-probability trades.",
                "Looking at the market for you right now. I'm checking both price action and order flow to find the best opportunity.",
                "I'm on the hunt for a great setup. Let me analyze the current conditions and I'll have something for you shortly.",
                "Just a sec while I process the latest market data. I'm searching for the perfect trading opportunity for you."
            ],
            NarrativeState.SETUP_WEAK: [
                "I don't think this setup is strong enough for us. I see {order_flow_weakness} in the order flow. Let's wait for a better opportunity.",
                "I'm not confident in this opportunity right now. {setup_weakness}. I'll keep looking for stronger candidates.",
                "This setup isn't meeting our criteria. The probability is too low, so I recommend we avoid this trade and wait for something better."
            ],
            NarrativeState.STRATEGY_FOUND: [
                "Great news! I've found a solid {strategy_name} opportunity. I recommend buying at ${entry_price}, with a stop at ${stop_price} and target at ${target_price}. The reward/risk is {risk_reward}:1.",
                "I've just identified a promising setup! It's a {strategy_name} pattern with a {probability}% success rate. Buy zone: ${entry_price}, protect with a stop at ${stop_price}, and aim for ${target_price}.",
                "Found something good for you! This {strategy_name} setup looks really promising. I suggest entering at ${entry_price}, placing your stop at ${stop_price}, and targeting ${target_price}."
            ],
            NarrativeState.WAITING_FOR_ENTRY: [
                "I'm keeping a close eye on our entry zone. We're currently at ${current_price}, which is {price_distance}% away from our ideal entry at ${entry_price}. I'll let you know when it's time to act.",
                "We're approaching our entry zone. The current price is ${current_price}, and we're looking to enter at ${entry_price}. I'm watching this carefully and will alert you when it's time to buy.",
                "Let's be patient here. Our target entry is at ${entry_price}, and the market is currently at ${current_price}. I'm monitoring this closely and will tell you exactly when to enter."
            ],
            NarrativeState.ENTRY_ZONE: [
                "ACTION NEEDED: It's time to buy now! We've reached our entry zone at ${current_price}. Place your order right away, with a stop at ${stop_price} and target at ${target_price}. I'm seeing good confirmation from buyer activity.",
                "ACTION NEEDED: This is it – time to execute! We've hit our entry zone at ${current_price}. Go ahead and buy now. I've already worked out your stop at ${stop_price} and target at ${target_price}.",
                "ACTION NEEDED: We have liftoff! Our entry zone at ${current_price} has been reached. Go ahead and place your buy order now. Your stop should be at ${stop_price} and target at ${target_price}."
            ],
            NarrativeState.ENTRY_APPROACHING: [
                "Get ready! We're getting close to our entry zone at ${entry_price}. Currently, we're just {price_distance}% away. I'm watching all the indicators and will give you a clear signal when it's time to act.",
                "Entry approaching! We're getting close to our buy zone at ${entry_price}. The current price is ${current_price}. I'm analyzing the order flow and will alert you when conditions are perfect.",
                "We're closing in on our entry point at ${entry_price}. Price is currently at ${current_price}, {price_distance}% away. Stay ready – I'll give you a clear signal when it's time to buy."
            ],
            NarrativeState.IN_POSITION: [
                "Looking good! We're up {gain_percentage}% so far. I'm keeping my eye on our target at ${target_price}, which is still {target_distance}% away. Just hold steady – I'm monitoring everything.",
                "Our position is performing as expected. We're up {gain_percentage}% with our target at ${target_price} still {target_distance}% away. I'm watching all the signals closely for you.",
                "Nice progress so far! We're up {gain_percentage}% and moving toward our target of ${target_price}. I'm keeping a close eye on support at ${current_support}. Just sit tight."
            ],
            NarrativeState.POSITION_BUILDING: [
                "This is looking really good! We're up {gain_percentage}% and building solid momentum toward our target of ${target_price}. I'm seeing strong buying pressure in the order flow.",
                "Great progress! We're up {gain_percentage}% and everything is confirming our trade. Let's hold for our target at ${target_price}. I'm watching all the indicators closely.",
                "We're really picking up steam now! Up {gain_percentage}% with good volume coming in. Let's stay focused on our target at ${target_price}. I'm monitoring everything for you."
            ],
            NarrativeState.APPROACHING_TARGET: [
                "We're getting close to our target! ${target_price} is just {target_distance}% away, and we're up {gain_percentage}% already. I'm watching for any signs of resistance before we get there.",
                "Almost there! Our target of ${target_price} is {target_distance}% away. We're up {gain_percentage}% already. I'll let you know when it's time to take profits.",
                "Target approaching! We're {target_distance}% away from our price target of ${target_price}. Current gain is {gain_percentage}%. I'm watching closely to make sure we exit at the optimal point."
            ],
            NarrativeState.APPROACHING_STOP: [
                "CAUTION: We're getting close to our stop at ${stop_price}. We're just {stop_distance}% away. I'm watching the order flow carefully to see if we need to take action.",
                "Heads up! Price is moving toward our stop at ${stop_price} ({stop_distance}% away). This is normal volatility, but I'm monitoring closely to protect your capital.",
                "Be aware: We're {stop_distance}% from our stop loss at ${stop_price}. I'm analyzing the order flow to see if this is just a shakeout or if our thesis is being invalidated."
            ],
            NarrativeState.TRADE_UNDER_PRESSURE: [
                "Our trade is under some pressure right now. We're down {loss_percentage}% at ${current_price}. I'm carefully evaluating if our original thesis still holds. Stay calm – this happens in trading.",
                "We're seeing some unexpected movement against our position. Down {loss_percentage}% now. I'm checking the order flow to determine if we should stay in or exit. Capital protection is our priority.",
                "This trade is facing some headwinds. We're down {loss_percentage}% currently. I'm assessing whether this is a temporary pullback or if something has changed. I'll guide you through this."
            ],
            NarrativeState.EXIT_WARNING: [
                "WARNING: {warning_reason}. I'm seeing some concerning signals. Consider securing some profits or adjusting your position. I'll continue to monitor the situation.",
                "CAUTION ADVISED: {warning_reason}. We're still up {gain_percentage}%, but I'm seeing some warning signs. It might be prudent to consider taking partial profits.",
                "ALERT: {warning_reason}. I'm concerned about what I'm seeing in the data. Let's consider taking protective action while we're still up {gain_percentage}%."
            ],
            NarrativeState.STRATEGY_FAILED: [
                "ACTION NEEDED: Our stop has been triggered. Please exit your position now at market price. Remember, preserving capital is our priority. Even the best traders have losing trades.",
                "ACTION NEEDED: Unfortunately, our strategy has been invalidated. Please close the position now. Our stop at ${stop_price} has been breached. This is normal in trading – we'll find the next opportunity.",
                "ACTION NEEDED: It's time to exit this trade. Our thesis is no longer valid. Let's accept this loss, protect your capital, and move on to the next opportunity. Everyone experiences losing trades."
            ],
            NarrativeState.STRATEGY_COMPLETE: [
                "ACTION NEEDED: Target achieved! Fantastic! It's time to take profits at ${target_price} for a {gain_percentage}% gain. Great job sticking to the plan.",
                "ACTION NEEDED: Success! Let's lock in this {gain_percentage}% gain at ${target_price}. You executed this trade perfectly. If you want, you could trail a small portion to see if we get more upside.",
                "ACTION NEEDED: We did it! It's time to sell at ${target_price} for a {gain_percentage}% profit. Well done on following the strategy. This is exactly how successful trading works."
            ],
            NarrativeState.SCALING_OPPORTUNITY: [
                "I'm seeing a good opportunity to add to our position at ${current_price}. The order flow is showing strong support. If you add here, keep your overall stop at ${stop_price}.",
                "This pullback looks like a perfect chance to enhance our position at ${current_price}. I'm seeing healthy buying interest in the order book. This would improve your overall risk/reward.",
                "I think we have a nice scaling opportunity here at ${current_price}. I'm seeing signs of accumulation. Adding here would improve your average entry while maintaining your stop at ${stop_price}."
            ],
            NarrativeState.MARKET_SHIFT: [
                "I'm noticing a shift in market conditions: {market_change}. I'm adjusting my analysis accordingly. This could impact our current strategy, so I'm watching it carefully.",
                "The market environment is changing: {market_change}. I'm evaluating what this means for our position. I'll keep you updated if we need to adjust our approach.",
                "Heads up – I'm seeing a significant change in the market: {market_change}. I'm reassessing our strategy in light of these new conditions. Stay tuned for updates."
            ]
        }
        
        # Psychological support messages
        self.psychological_support = {
            "LOSING_TRADE": [
                "It's completely normal to feel uncomfortable with losses. Stay disciplined and focus on proper execution – that's what professional traders do.",
                "Remember, one trade doesn't define your performance. Emotional control during drawdowns is what separates successful traders from the rest.",
                "Even the most successful traders have losing trades. What matters is how you respond – by protecting capital and staying focused on the next opportunity."
            ],
            "WINNING_TRADE": [
                "Great job sticking to the plan! Remember that consistent execution is what builds exceptional returns over time.",
                "You're doing this exactly right. Discipline is just as important when taking profits as it is when cutting losses.",
                "This is how successful trading works – follow your system, execute with precision, and let the probabilities work in your favor."
            ],
            "VOLATILE_TRADE": [
                "Market volatility is actually creating our opportunity. I'm here to guide you through the noise and help you focus on what matters.",
                "Stay focused despite the volatility. Trust your analysis and the system – don't let short-term fluctuations distract you from the bigger picture.",
                "Volatility can be uncomfortable, but it's completely normal. The most successful traders maintain their composure during volatile periods."
            ],
            "NEUTRAL": [
                "Trading is ultimately about probabilities, not certainties. Trust the process and focus on perfect execution.",
                "Your edge comes from consistently following your strategy across many trades, not from trying to predict individual outcomes.",
                "Remember that patience is a serious competitive advantage in trading. Most people can't maintain it – but you can."
            ]
        }
        
        # Order flow insight templates
        self.order_flow_templates = {
            "BULLISH": [
                "I'm seeing strong buying interest in the order book",
                "I can see significant accumulation happening behind the scenes",
                "I'm noticing large hidden buy orders providing support",
                "I'm seeing signs of institutional buying in the order flow"
            ],
            "BEARISH": [
                "I'm seeing selling pressure building in the order book",
                "I'm noticing a distribution pattern forming in the order flow",
                "I can see resistance strengthening above us",
                "I'm detecting institutional selling in the order flow"
            ],
            "NEUTRAL": [
                "The order flow is showing a balanced picture right now",
                "I'm seeing mixed signals in the order book data",
                "The order flow is neutral without a clear directional bias",
                "I'm waiting for a clearer direction in the order flow"
            ]
        }
        
        # Order book insight templates
        self.order_book_templates = {
            "BULLISH": [
                "I see strong support forming at ${current_support}",
                "I'm noticing buy orders stacking up at key levels",
                "I can see demand exceeding supply in the order book",
                "I'm seeing a solid wall of bids providing support"
            ],
            "BEARISH": [
                "I'm noticing resistance forming at ${current_resistance}",
                "I'm seeing sell orders dominating the order book",
                "I can see supply exceeding demand at current levels",
                "I'm noticing a wall of asks creating overhead resistance"
            ],
            "NEUTRAL": [
                "The order book structure looks balanced right now",
                "I'm not seeing any significant imbalance in the order book",
                "I'm seeing an equal distribution of bids and asks",
                "The order book is showing a consolidation pattern"
            ]
        }

    def generate_narrative(self, ticker: str) -> CoachingNarrative:
        """Generate narrative using the original template system"""
        try:
            # Determine narrative state
            narrative_state = self._determine_narrative_state(ticker)
            
            # Get template for current state
            templates = self.narrative_templates[narrative_state]
            template = self._select_template(templates)
            
            # Generate context data with enhanced insights
            context = self._generate_context_data(ticker, narrative_state)
            
            # Fill template with context
            message = self._fill_template(template, context)
            
            # Calculate confidence and probability
            confidence = self._calculate_confidence(ticker)
            probability = self._calculate_success_probability(ticker, narrative_state)
            
            # Create narrative
            narrative = CoachingNarrative(
                state=narrative_state,
                message=message,
                context=context,
                timestamp=time.time(),
                confidence=confidence,
                warning_reason=self._get_warning_reason(ticker),
                probability=probability
            )
            
            return narrative
            
        except Exception as e:
            self.logger.error(f"Error generating template narrative: {e}")
            return CoachingNarrative(
                state=NarrativeState.ANALYZING,
                message="Analyzing market conditions...",
                context={},
                timestamp=time.time()
            )
    
    def _dict_to_narrative(self, narrative_dict: Dict) -> CoachingNarrative:
        """Convert a dictionary to a CoachingNarrative object"""
        try:
            state_str = narrative_dict.get('state', NarrativeState.ANALYZING.value)
            
            # Convert string state to enum
            state = NarrativeState.ANALYZING
            for s in NarrativeState:
                if s.value == state_str:
                    state = s
                    break
            
            return CoachingNarrative(
                state=state,
                message=narrative_dict.get('message', ''),
                context=narrative_dict.get('context', {}),
                timestamp=narrative_dict.get('timestamp', time.time()),
                confidence=narrative_dict.get('confidence', 0.0),
                warning_reason=narrative_dict.get('warning_reason'),
                order_flow_insights=narrative_dict.get('order_flow_insights'),
                technical_insights=narrative_dict.get('technical_insights'),
                recommendations=narrative_dict.get('recommendations'),
                exit_strategy=narrative_dict.get('exit_strategy'),
                probability=narrative_dict.get('probability', 0.65)
            )
        except Exception as e:
            self.logger.error(f"Error converting dict to narrative: {e}")
            return CoachingNarrative(
                state=NarrativeState.ANALYZING,
                message="Analyzing market conditions...",
                context={},
                timestamp=time.time()
            )

    def _determine_narrative_state(self, ticker: str) -> NarrativeState:
        """Determine the current narrative state with advanced order flow integration"""
        try:
            strategy = redis_manager.get_current_strategy(ticker)
            current_price = redis_manager.get_stock_price(ticker)
            
            # Check if we have a valid strategy
            if not strategy:
                return NarrativeState.ANALYZING
            
            # Get critical strategy data
            strategy_state = strategy.get('state')
            entry_price = float(strategy.get('entry_price', 0))
            target_price = float(strategy.get('target_price', 0))
            stop_price = float(strategy.get('stop_price', 0))

            buying_pressure = 0
            orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
            if orderbook:
                bid_volume = orderbook.get('bid_volume', 0)
                ask_volume = orderbook.get('ask_volume', 0)
                buying_pressure = bid_volume / (bid_volume + ask_volume) if bid_volume + ask_volume > 0 else 0
            
            # If strategy is locked
            if strategy_state == StrategyState.LOCKED:
                # Calculate price distances
                entry_distance_pct = abs((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 100
                stop_distance_pct = abs((current_price - stop_price) / stop_price * 100) if stop_price > 0 else 100
                target_distance_pct = abs((current_price - target_price) / target_price * 100) if target_price > 0 else 100
                
                # Calculate gain/loss percentage
                gain_percentage = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                
                # Determine if in position
                is_in_position = current_price >= entry_price # or redis_manager.get_position(ticker)
                
                # If in position
                if is_in_position:
                    # If at or past target
                    if current_price >= target_price:
                        return NarrativeState.STRATEGY_COMPLETE
                    
                    # If at or below stop (strategy failed)
                    if current_price <= stop_price:
                        return NarrativeState.STRATEGY_FAILED
                    
                    # If close to stop loss (within 1.5%)
                    if stop_distance_pct < 1.5 and current_price < entry_price:
                        return NarrativeState.APPROACHING_STOP
                    
                    # If trade under pressure (down 3% but not yet at stop)
                    if gain_percentage < -3 and current_price > stop_price:
                        return NarrativeState.TRADE_UNDER_PRESSURE
                    
                    # If close to target (within 2%)
                    if target_distance_pct < 2:
                        return NarrativeState.APPROACHING_TARGET
                    
                    # Check for warning conditions
                    warning_reason = self._get_warning_reason(ticker)
                    if warning_reason:
                        return NarrativeState.EXIT_WARNING
                    
                    # Check for position strengthening
                    orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
                    if orderbook:
                        bid_volume = orderbook.get('bid_volume', 0)
                        ask_volume = orderbook.get('ask_volume', 0)
                        buying_pressure = bid_volume / (bid_volume + ask_volume) if bid_volume + ask_volume > 0 else 0
                        if buying_pressure > 0.65 and gain_percentage > 2:
                            return NarrativeState.POSITION_BUILDING
                        
                    # Default state for position
                    return NarrativeState.IN_POSITION
                
                # Not in position yet
                else:
                    # If entry price reached
                    if entry_distance_pct < 0.5:
                        if buying_pressure > 0.65:
                            return NarrativeState.ENTRY_ZONE
                        else:
                            return NarrativeState.ENTRY_APPROACHING
                    
                    # If close to entry (within 2%)
                    if entry_distance_pct < 2:
                        return NarrativeState.ENTRY_APPROACHING
                    
                    # Default waiting state
                    return NarrativeState.WAITING_FOR_ENTRY
            
            # If strategy is found but not locked
            elif strategy and entry_price > 0:
                return NarrativeState.STRATEGY_FOUND
            
            # If strategy is completed
            elif strategy_state == StrategyState.COMPLETED:
                return NarrativeState.STRATEGY_COMPLETE
            
            # Default analyzing state
            return NarrativeState.ANALYZING
            
        except Exception as e:
            self.logger.error(f"Error determining narrative state: {e}")
            return NarrativeState.ANALYZING

    def _select_template(self, templates: list) -> str:
        """Select a template randomly from available templates"""
        return random.choice(templates)

    def _generate_context_data(self, ticker: str, state: NarrativeState) -> Dict:
        """Generate enhanced context data with real-time order flow and technical insights"""
        context = {}
        
        # Get base strategy data
        strategy = redis_manager.get_current_strategy(ticker)
        current_price = redis_manager.get_stock_price(ticker)
        
        # Extract basic strategy information
        if strategy:
            # Price targets
            context['strategy_name'] = strategy.get('name', 'Active Strategy')
            context['entry_price'] = f"{float(strategy.get('entry_price', current_price)):.2f}"
            context['target_price'] = f"{float(strategy.get('target_price', current_price * 1.03)):.2f}"
            context['stop_price'] = f"{float(strategy.get('stop_price', current_price * 0.97)):.2f}"
            
            # Current price and distance metrics
            context['current_price'] = f"{current_price:.2f}"
            
            # Calculate distances to key price points (as percentages)
            entry_price = float(strategy.get('entry_price', current_price))
            if entry_price > 0:
                entry_distance = abs((current_price - entry_price) / entry_price * 100)
                context['price_distance'] = f"{entry_distance:.1f}"
                
                # Calculate gain/loss percentage
                gain_percentage = ((current_price - entry_price) / entry_price * 100)
                context['gain_percentage'] = f"{gain_percentage:.2f}"
                if gain_percentage < 0:
                    context['loss_percentage'] = f"{abs(gain_percentage):.2f}"
            
            target_price = float(strategy.get('target_price', current_price * 1.03))
            if target_price > 0:
                target_distance = abs((target_price - current_price) / current_price * 100)
                context['target_distance'] = f"{target_distance:.1f}"
            
            stop_price = float(strategy.get('stop_price', current_price * 0.97))
            if stop_price > 0:
                stop_distance = abs((current_price - stop_price) / current_price * 100)
                context['stop_distance'] = f"{stop_distance:.1f}"
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_price)
            reward = abs(target_price - entry_price)
            if risk > 0:
                context['risk_reward'] = f"{(reward/risk):.1f}"
        
        # Get strategy probability
        probability = strategy.get('probability', 0.65) if strategy else 0.65
        context['probability'] = f"{probability * 100:.0f}"
        
        # Add order flow context
        orderbook = redis_manager.get_last_orderbook_snapshot(ticker)
        if orderbook:
            bid_volume = orderbook.get('bid_volume', 0)
            ask_volume = orderbook.get('ask_volume', 0)
            buying_pressure = bid_volume / (bid_volume + ask_volume) if bid_volume + ask_volume > 0 else 0
            selling_pressure = ask_volume / (bid_volume + ask_volume) if bid_volume + ask_volume > 0 else 0
            context['buying_pressure'] = f"{buying_pressure:.0f}"
            context['selling_pressure'] = f"{selling_pressure:.0f}"

            order_flow_sentiment = "NEUTRAL"
            if buying_pressure > 0.65:
                order_flow_sentiment = "BULLISH"
            elif selling_pressure > 0.65:
                order_flow_sentiment = "BEARISH"
            context['order_flow_status'] = order_flow_sentiment
            
            # Add order flow insight
            context['order_flow_status'] = f"{order_flow_sentiment.lower()} signals"
            context['order_flow_insight'] = random.choice(self.order_flow_templates[order_flow_sentiment])
            
            # Add order book insight
            context['order_book_insight'] = random.choice(self.order_book_templates[order_flow_sentiment])
            
        indicators = redis_manager.get_technical_indicators(ticker)
        # Add volume context
        volume_ratio = indicators.get('Volume_Ratio', 1)
        if not volume_ratio:
            volume_ratio = 1
        
        # Volume description
        if volume_ratio > 2.5:
            context['volume_description'] = "extreme volume"
        elif volume_ratio > 1.5:
            context['volume_description'] = "high volume"
        elif volume_ratio > 0.8:
            context['volume_description'] = "average volume"
        else:
            context['volume_description'] = "low volume"
        
        # Volume insight
        if volume_ratio > 3:
            context['volume_insight'] = f"Exceptional volume: {volume_ratio:.1f}x average"
        elif volume_ratio > 2:
            context['volume_insight'] = f"Strong volume confirmation: {volume_ratio:.1f}x average"
        elif volume_ratio > 1.5:
            context['volume_insight'] = f"Good volume support: {volume_ratio:.1f}x average"
        elif volume_ratio < 0.7:
            context['volume_insight'] = f"Low volume caution: {volume_ratio:.1f}x average"
        else:
            context['volume_insight'] = f"Normal volume levels: {volume_ratio:.1f}x average"
        
        # Add support/resistance levels
        support_resistance = redis_manager.get_support_resistance(ticker)
        if support_resistance:
            # Get nearest support below current price
            supports = [level for level in support_resistance if level['type'] == 'support' and level['price'] < current_price]
            if supports:
                nearest_support = max(supports, key=lambda x: x['price'])
                context['current_support'] = f"{nearest_support['price']:.2f}"
            
            # Get nearest resistance above current price
            resistances = [level for level in support_resistance if level['type'] == 'resistance' and level['price'] > current_price]
            if resistances:
                nearest_resistance = min(resistances, key=lambda x: x['price'])
                context['current_resistance'] = f"{nearest_resistance['price']:.2f}"
        
        # Add technical indicators context
        if indicators:
            rsi = indicators['RSI'] if indicators['RSI'] is not None else 50
            macd = indicators['MACD'] if indicators['MACD'] is not None else 0
            if rsi > 70:
                context['technical_warning'] = "overbought conditions"
            elif rsi < 30:
                context['technical_warning'] = "oversold conditions"
            
            context['rsi'] = f"{rsi:.0f}"
            context['macd'] = f"{macd:.4f}"
        
        # Add psychological support
        if 'gain_percentage' in context:
            gain_pct = float(context['gain_percentage'])
            context['psychological_support'] = self._get_psychological_support(state, gain_pct)
        
        # Add target evolution message if available
        target_evolution_message = self._get_target_evolution_message(ticker)
        context['target_evolution_message'] = target_evolution_message
        
        # Ensure all template variables have fallback values
        self._ensure_template_variables(context)
        
        return context

    def _ensure_template_variables(self, context: Dict) -> None:
        """Ensure all template variables have fallback values"""
        defaults = {
            'strategy_name': 'Active Strategy',
            'entry_price': '0.00',
            'target_price': '0.00',
            'stop_price': '0.00',
            'current_price': '0.00',
            'price_distance': '0.0',
            'gain_percentage': '0.00',
            'loss_percentage': '0.00',
            'target_distance': '0.0',
            'stop_distance': '0.0',
            'risk_reward': '1.0',
            'probability': '65',
            'buying_pressure': '50',
            'selling_pressure': '50',
            'institutional_insight': 'monitoring institutional activity',
            'order_flow_confirmation': 'analyzing order flow',
            'order_flow_status': 'neutral signals',
            'order_flow_insight': 'neutral order flow pattern',
            'order_book_insight': 'analyzing order book structure',
            'order_flow_weakness': 'insufficient order flow confirmation',
            'setup_weakness': 'inadequate setup alignment',
            'volume_description': 'average volume',
            'volume_insight': 'monitoring volume patterns',
            'current_support': '0.00',
            'current_resistance': '0.00',
            'technical_warning': 'monitoring technical indicators',
            'rsi': '50',
            'macd': '0.0000',
            'psychological_support': 'Execute with precision and discipline',
            'market_change': 'shifting market conditions',
            'warning_reason': 'changing market conditions'
        }
        
        for key, value in defaults.items():
            if key not in context or not context[key]:
                context[key] = value

    def _fill_template(self, template: str, context: Dict) -> str:
        """Fill template with context data"""
        try:
            return template.format(**context)
        except KeyError as e:
            self.logger.error(f"Missing context key for template: {e}")
            return "Analyzing market conditions..."

    def _calculate_confidence(self, ticker: str) -> float:
        """Calculate confidence level for current narrative using advanced metrics"""
        try:
            strategy = redis_manager.get_current_strategy(ticker)
            
            # Base confidence from strategy
            base_confidence = float(strategy.get('probability', 0.5)) if strategy else 0.5
            
            # Adjust based on technical indicators
            indicators = redis_manager.get_technical_indicators(ticker)
            scores = redis_manager.get_technical_scores(ticker)
            tech_confidence = 0.5
            
            if indicators and scores:
                # Get key indicators
                rsi = indicators['RSI'] if indicators['RSI'] is not None else 50
                macd = indicators['MACD'] if indicators['MACD'] is not None else 0
                macd_signal = indicators['MACD_signal'] if indicators['MACD_signal'] is not None else 0
                technical_score = scores.get('technical_score', 0)
                
                # Calculate technical confidence (normalized to 0-1)
                tech_factors = []
                
                # RSI factor
                if rsi > 70:
                    tech_factors.append(0.7)  # Strong but potentially overbought
                elif rsi > 60:
                    tech_factors.append(0.9)  # Strong but not overbought
                elif rsi < 30:
                    tech_factors.append(0.3)  # Weak and potentially oversold
                elif rsi < 40:
                    tech_factors.append(0.4)  # Weak but not deeply oversold
                else:
                    tech_factors.append(0.5)  # Neutral
                
                # MACD factor
                if macd > macd_signal and macd > 0:
                    tech_factors.append(0.9)  # Strong bullish signal
                elif macd > macd_signal:
                    tech_factors.append(0.7)  # Bullish signal but not strongly positive
                elif macd < macd_signal and macd < 0:
                    tech_factors.append(0.2)  # Strong bearish signal
                elif macd < macd_signal:
                    tech_factors.append(0.3)  # Bearish signal
                else:
                    tech_factors.append(0.5)  # Neutral
                
                # Final technical score factor
                if technical_score > 0.8:
                    tech_factors.append(0.9)
                elif technical_score > 0.6:
                    tech_factors.append(0.7)
                elif technical_score < 0.3:
                    tech_factors.append(0.2)
                elif technical_score < 0.5:
                    tech_factors.append(0.4)
                else:
                    tech_factors.append(0.5)
                
                # Average technical factors
                tech_confidence = sum(tech_factors) / len(tech_factors) if tech_factors else 0.5
            
            # Combine all confidences with weighted average
            confidence = (
                base_confidence * 0.7 +    # Strategy base confidence (70%)
                tech_confidence * 0.3     # Technical indicators (30%)
            )
            
            # Ensure confidence is within bounds
            return min(0.99, max(0.01, confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 0.5

    def _get_warning_reason(self, ticker: str) -> Optional[str]:
        """Determine if there are any warnings with enhanced detection"""
        try:
            strategy = redis_manager.get_current_strategy(ticker)
            if not strategy:
                return None
            
            current_price = redis_manager.get_stock_price(ticker)
            
            # Warning categories
            price_warnings = []
            technical_warnings = []
            order_flow_warnings = []
            volume_warnings = []
            
            # 1. Check price warnings
            stop_price = float(strategy.get('stop_price', 0))
            if stop_price > 0:
                distance_to_stop = (current_price - stop_price) / stop_price
                if 0 < distance_to_stop < 0.01:  # Within 1% of stop
                    price_warnings.append("Price approaching stop loss")
            
            # 2. Check technical warnings
            indicators = redis_manager.get_technical_indicators(ticker)
            if indicators:
                rsi = indicators.get('RSI', 50)
                macd = indicators.get('MACD', 0)
                macd_signal = indicators.get('MACD_signal', 0)
                
                if rsi > 80:
                    technical_warnings.append("Extremely overbought conditions")
                elif rsi > 70:
                    technical_warnings.append("Overbought conditions")
                
                if macd_signal > macd > 0:
                    technical_warnings.append("MACD bearish crossover forming")
            
            # 3. Check volume warnings
            if indicators:
                volume_ratio = indicators.get('Volume_Ratio', 1)
                if volume_ratio < 0.5:
                    volume_warnings.append("Unusually low volume")
            
            # Compile all warnings and prioritize
            all_warnings = (
                price_warnings +       # Price warnings are highest priority
                technical_warnings +   # Technical warnings are second priority
                volume_warnings        # Volume warnings are lowest priority
            )
            
            return all_warnings[0] if all_warnings else None
            
        except Exception as e:
            self.logger.error(f"Error detecting warnings: {e}")
            return None
    
    def _get_psychological_support(self, state: NarrativeState, gain_pct: float) -> str:
        """Generate appropriate psychological support message based on trade state"""
        try:
            support_type = 'NEUTRAL'
            
            # Determine the trade emotional state
            if gain_pct < 0:
                if state in [NarrativeState.APPROACHING_STOP, NarrativeState.STRATEGY_FAILED, 
                           NarrativeState.TRADE_UNDER_PRESSURE]:
                    support_type = 'LOSING_TRADE'
                elif abs(gain_pct) > 5:
                    support_type = 'VOLATILE_TRADE'
            elif gain_pct > 0:
                if state in [NarrativeState.APPROACHING_TARGET, NarrativeState.STRATEGY_COMPLETE,
                           NarrativeState.POSITION_BUILDING]:
                    support_type = 'WINNING_TRADE'
                elif gain_pct > 5:
                    support_type = 'VOLATILE_TRADE'
            
            # Select random support message from appropriate category
            support_messages = self.psychological_support.get(support_type, self.psychological_support['NEUTRAL'])
            return random.choice(support_messages)
            
        except Exception as e:
            self.logger.error(f"Error generating psychological support: {e}")
            return "Remember to focus on disciplined execution - that's what separates professional traders from the rest."
    
    def _calculate_success_probability(self, ticker: str, state: NarrativeState) -> float:
        """Calculate the probability of trade success based on real-time data"""
        try:
            strategy = redis_manager.get_current_strategy(ticker)
            base_probability = float(strategy.get('probability', 0.65)) if strategy else 0.65
            
            # Different factors affect probability based on narrative state
            modifiers = []
            
            # Get key data
            indicators = redis_manager.get_technical_indicators(ticker)
            scores = redis_manager.get_technical_scores(ticker)
            current_price = redis_manager.get_stock_price(ticker)
            entry_price = float(strategy.get('entry_price', 0)) if strategy else 0
           
            # Technical factors (moderate impact)
            if indicators and scores:
                rsi = indicators['RSI'] if indicators['RSI'] is not None else 50
                # RSI extremes reduce probability
                if rsi > 80 or rsi < 20:
                    modifiers.append(-0.05)  # -5%
                    
                # Positive trends increase probability
                trend_score = scores.get('trend_score', 50)
                modifiers.append((trend_score - 50) / 500)  # +/- 10% max
            
            # Current state modifiers
            if state in [NarrativeState.APPROACHING_TARGET, NarrativeState.POSITION_BUILDING]:
                modifiers.append(0.05)  # +5% for positive progress
            elif state in [NarrativeState.TRADE_UNDER_PRESSURE, NarrativeState.APPROACHING_STOP]:
                modifiers.append(-0.1)  # -10% for negative conditions
            elif state == NarrativeState.IN_POSITION and current_price > entry_price:
                modifiers.append(0.03)  # +3% for being in profit
            
            # Apply all modifiers to base probability
            final_probability = base_probability
            for modifier in modifiers:
                final_probability += modifier
            
            # Ensure probability stays within reasonable bounds
            return min(0.95, max(0.05, final_probability))
            
        except Exception as e:
            self.logger.error(f"Error calculating success probability: {e}")
            return 0.65

    def _get_target_evolution_message(self, ticker: str):
        """Generate a message about target evolution"""
        try:
            strategy = redis_manager.get_current_strategy(ticker)
            if not strategy:
                return ""
                
            target_history = strategy.get('target_history', [])
            current_target_index = strategy.get('current_target_index', 0)
            
            if len(target_history) <= 1 or current_target_index == 0:
                return ""
                
            # Get the previous and current targets
            previous_target = target_history[current_target_index - 1]
            current_target = target_history[current_target_index]
            
            if previous_target.get('achieved', False) and previous_target.get('achieved_at'):
                # Convert timestamp to datetime
                achieved_time = previous_target.get('achieved_at')
                if isinstance(achieved_time, str):
                    from datetime import datetime
                    achieved_time = datetime.fromisoformat(achieved_time)
                    
                # Check if the target was achieved recently (within the last hour)
                from datetime import datetime, timedelta
                if datetime.now() - achieved_time < timedelta(hours=1):
                    price_diff = current_target.get('price', 0) - previous_target.get('price', 0)
                    price_diff_percent = price_diff / previous_target.get('price', 1) * 100
                    
                    return f"TARGET ACHIEVED at ${previous_target.get('price', 0):.2f}! New target set at ${current_target.get('price', 0):.2f} (+{price_diff_percent:.1f}%). Continue holding for additional gains."
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error generating target evolution message: {e}")
            return "" 
        
trading_coach_service = TradingCoachingService()