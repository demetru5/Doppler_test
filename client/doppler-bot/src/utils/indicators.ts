// Technical indicator calculations
import { FasterMACD, FasterEMA, FasterRSI } from "trading-signals";

interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Calculate MACD (Moving Average Convergence Divergence)
export const calculateMACD = (prices: number[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) => {
  let data: {
    macd: number[];
    signal: number[];
    histogram: number[];
  } = {
    macd: Array(slowPeriod - 1).fill(0),
    signal: Array(slowPeriod - 1).fill(0),
    histogram: Array(slowPeriod - 1).fill(0)
  }
  const macd = new FasterMACD(new FasterEMA(fastPeriod), new FasterEMA(slowPeriod), new FasterEMA(signalPeriod));
  for (const price of prices) {
    const result = macd.update(price, false);
    if (result) {
      data.macd.push(result.macd);
      data.signal.push(result.signal);
      data.histogram.push(result.histogram);
    }
  }
  console.log(data);
  return data;
};

// Calculate VWAP (Volume Weighted Average Price)
export const calculateVWAP = (data: CandleData[]) => {
  const vwap: number[] = [];
  let cumulativeTPV = 0; // Total Price * Volume
  let cumulativeVolume = 0;
  
  data.forEach(candle => {
    const typicalPrice = (candle.high + candle.low + candle.close) / 3;
    const priceVolume = typicalPrice * candle.volume;
    
    cumulativeTPV += priceVolume;
    cumulativeVolume += candle.volume;
    
    vwap.push(cumulativeTPV / cumulativeVolume);
  });
  
  return vwap;
};

// Calculate RSI (Relative Strength Index)
export const calculateRSI = (prices: number[], period: number = 14) => {
  const rsi = new FasterRSI(period);
  const rsi_data = [];
  for (const price of prices) {
    rsi_data.push(rsi.update(price, false));
  }
  return rsi_data;
};

// Calculate EMA (Exponential Moving Average)
export const calculateEMA = (prices: number[], period: number) => {
  const ema = new FasterEMA(period);
  const ema_data = [];
  for (const price of prices) {
    ema_data.push(ema.update(price, false));
  }
  return ema_data;
};

// Calculate SMA (Simple Moving Average)
export const calculateSMA = (prices: number[], period: number) => {
  const sma: (number | null)[] = [];
  
  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      sma.push(null);
    } else {
      const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
      sma.push(sum / period);
    }
  }
  
  return sma;
};

// Calculate Bollinger Bands
export const calculateBollingerBands = (prices: number[], period: number = 20, stdDev: number = 2) => {
  const sma = calculateSMA(prices, period);
  const upper: (number | null)[] = [];
  const lower: (number | null)[] = [];
  
  for (let i = 0; i < prices.length; i++) {
    if (i < period - 1) {
      upper.push(null);
      lower.push(null);
    } else {
      const slice = prices.slice(i - period + 1, i + 1);
      const mean = sma[i];
      if (mean !== null) {
        const variance = slice.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / period;
        const standardDeviation = Math.sqrt(variance);
        
        upper.push(mean + (standardDeviation * stdDev));
        lower.push(mean - (standardDeviation * stdDev));
      } else {
        upper.push(null);
        lower.push(null);
      }
    }
  }
  
  return {
    upper,
    middle: sma,
    lower
  };
}; 