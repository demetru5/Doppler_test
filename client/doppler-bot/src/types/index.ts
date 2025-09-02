export interface CoachingNarrative {
    state: string;
    message: string;
    context: any;
    timestamp: number;
    confidence: number;
}

export interface MarketNote {
    message: string;
    type: string;
    priority: string;
    icon: string;
    is_strategy: boolean;
    strategy_details: any;
    timestamp: number;
}

export interface Stock {
    mode: string[];
    ticker: string;
    float_share?: number;
    avg_30d_volume?: number;
    prev_close_price?: number;
    price?: number;
    volume?: number;
    candles?: {
        close: number;
        open: number;
        high: number;
        low: number;
        volume: number;
        timestamp: string;
    }[];
    orderbook?: any;
    indicators?: any;
    scores?: any;
    fire_emoji_status?: boolean;
    explosion_emoji_status?: boolean;
    strategy?: any;
    narrative?: CoachingNarrative;
    market_notes?: MarketNote[];
    _lastUpdate?: number; // Optional timestamp for re-render tracking
    _types?: string[]; // Priority types this stock belongs to
}

export interface User {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    isAdmin?: boolean;
    moomooAccount?: MoomooAccount;
}

export interface MoomooAccount {
    id: string;
    accountId: string;
    email: string;
    phone: string;
    status: string;
    tradingEnabled: boolean;
    tradingAmount: number;
}

export interface PendingRequest {
  id: string;
  userId: string;
  userEmail: string;
  userName: string;
  accountId: string;
  email?: string;
  phone?: string;
  createdAt: string;
  host?: string;
  port?: number;
  cashAccountId?: number;
  marginAccountId?: number;
  tradingAccount?: string;
}

export interface Account {
  id: string;
  userId: string;
  userEmail: string;
  userName: string;
  accountId: string;
  email?: string;
  phone?: string;
  status: 'pending' | 'approved' | 'rejected';
  tradingEnabled: boolean;
  tradingAmount: number;
  createdAt: string;
  approvedAt?: string;
  rejectedAt?: string;
  rejectionReason?: string;
  host?: string;
  port?: number;
  cashAccountId?: number;
  marginAccountId?: number;
  tradingAccount: 'cash' | 'margin';
  maxDailyLoss?: number;
  riskPerTrade?: number;
}
