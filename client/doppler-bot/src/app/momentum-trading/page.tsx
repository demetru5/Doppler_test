'use client';

import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Grid,
  Button,
  Switch,
  FormControlLabel,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useSocket } from '@/context/SocketProvider';
import { useAuth } from '@/context/AuthContext';
import CandlestickChart from '@/components/CandlestickChart';
import StockDescription from '@/components/StockDescription';
import { Stock } from '@/types';
import { getIndicatorColor, formatNumber, formatLargeNumber, checkAllGreen, getGreenIndicatorCount, humanReadableDateTime } from '@/utils/helpers';

export default function MomentumTrading() {
  const { user } = useAuth();
  const moomooAccount = user?.moomooAccount;
  const { socket } = useSocket();

  const [marketContext, setMarketContext] = useState<any>({
    score: 0,
    signal: '',
    timestamp: '',
    components: {
      momentum: false,
      nasdaq_dow: false,
      vix: 0,
      breadth: 0,
      sector_strength: 0
    }
  });
  const [positions, setPositions] = useState<any>({});
  const [buyFeaturesEnabled, setBuyFeaturesEnabled] = useState<boolean>(true);
  const [toggleLoading, setToggleLoading] = useState<boolean>(false);
  const [candleLoading, setCandleLoading] = useState<string[]>([]);

  const [stocks, setStocks] = useState<{
    [key: string]: Stock;
  }>({});
  const [displayStocks, setDisplayStocks] = useState<Stock[]>([]);
  const [selectedTickers, setSelectedTickers] = useState<string[]>([]);

  // Filter stocks to display
  useEffect(() => {
    const stockArray = Object.values(stocks);

    // VWAP candidate stocks
    const vwapCandidates = stockArray
      .filter(stock => stock?.mode?.includes('vwap_candidate') && stock?.indicators?.EMA5 < stock?.indicators?.VWAP)
      .map(stock => stock.ticker);

    // Calculate session gainers (price change from prev_close)
    const sessionGainers = stockArray
      .filter(stock => stock?.mode?.includes('session_gainer'))
      .filter(stock => stock.prev_close_price && stock.price && stock.price > 0)
      .sort((a, b) => {
        if (a.prev_close_price && b.prev_close_price && a.price && b.price) {
          return (b.price - b.prev_close_price) / b.prev_close_price - (a.price - a.prev_close_price) / a.prev_close_price;
        }
        return a.ticker.localeCompare(b.ticker);
      })
      .map(stock => stock.ticker)
      .slice(0, 3);

    // All green stocks - sorted by green indicator count (desc) then tech score (desc)
    const allGreenStocks = stockArray
      .filter(stock => checkAllGreen(stock))
      .sort((a, b) => {
        const aGreenCount = getGreenIndicatorCount(a);
        const bGreenCount = getGreenIndicatorCount(b);
        const aTechScore = a?.scores?.technical_score || 0;
        const bTechScore = b?.scores?.technical_score || 0;

        // First sort by green indicator count (descending)
        if (aGreenCount !== bGreenCount) {
          return bGreenCount - aGreenCount;
        }
        // Then by tech score (descending)
        return bTechScore - aTechScore;
      })
      .map(stock => stock.ticker);

    // Rapid gainers with 5+ green indicators - sorted by green indicator count (desc) then tech score (desc)
    const rapidGainersWith5Green = stockArray
      .filter(stock =>
        stock?.mode?.includes('rapid_gainer') &&
        getGreenIndicatorCount(stock) >= 5
      )
      .sort((a, b) => {
        const aGreenCount = getGreenIndicatorCount(a);
        const bGreenCount = getGreenIndicatorCount(b);
        const aTechScore = a?.scores?.technical_score || 0;
        const bTechScore = b?.scores?.technical_score || 0;

        // First sort by green indicator count (descending)
        if (aGreenCount !== bGreenCount) {
          return bGreenCount - aGreenCount;
        }
        // Then by tech score (descending)
        return bTechScore - aTechScore;
      })
      .map(stock => stock.ticker);

    // Top 5 minute gainers - sorted by tech score (desc)
    const top5MinuteGainers = stockArray
      .filter(stock => stock?.mode?.includes('five_minute_gainer'))
      .sort((a, b) => {
        const aTechScore = a?.scores?.technical_score || 0;
        const bTechScore = b?.scores?.technical_score || 0;
        return bTechScore - aTechScore;
      })
      .map(stock => stock.ticker);

    // All rapid gainers - sorted by tech score (desc)
    const rapidGainers = stockArray
      .filter(stock => stock?.mode?.includes('rapid_gainer'))
      .sort((a, b) => {
        const aTechScore = a?.scores?.technical_score || 0;
        const bTechScore = b?.scores?.technical_score || 0;
        return bTechScore - aTechScore;
      })
      .map(stock => stock.ticker);

    // Build final list with priority order and track types
    const selectedTickers: string[] = [];
    const stockTypes: { [key: string]: string[] } = {};

    // #1 Add all green stocks (sorted by green count then tech score)
    allGreenStocks.forEach(ticker => {
      if (selectedTickers.length < 20) {
        selectedTickers.push(ticker);
      }
      if (!stockTypes[ticker]) stockTypes[ticker] = [];
      stockTypes[ticker].push('all_green');
    });

    // #2 Add rapid gainers with 5+ green indicators (sorted by green count then tech score)
    rapidGainersWith5Green.forEach(ticker => {
      if (selectedTickers.length < 20 && !selectedTickers.includes(ticker)) {
        selectedTickers.push(ticker);
      }
      if (!stockTypes[ticker]) stockTypes[ticker] = [];
      stockTypes[ticker].push('rapid_5green');
    });

    // #3 Add top 5 minute gainers (sorted by tech score)
    top5MinuteGainers.forEach(ticker => {
      if (selectedTickers.length < 20 && !selectedTickers.includes(ticker)) {
        selectedTickers.push(ticker);
      }
      if (!stockTypes[ticker]) stockTypes[ticker] = [];
      stockTypes[ticker].push('top_5m');
    });

    // #4 Always add top 3 session gainers
    sessionGainers.forEach(ticker => {
      if (!selectedTickers.includes(ticker)) selectedTickers.push(ticker);
      stockTypes[ticker] = ['session_gainer'];
    });

    // #5 Add remaining rapid gainers (sorted by tech score)
    rapidGainers.forEach(ticker => {
      if (selectedTickers.length < 20 && !selectedTickers.includes(ticker)) {
        selectedTickers.push(ticker);
      }
      if (!stockTypes[ticker]) stockTypes[ticker] = [];
      stockTypes[ticker].push('rapid');
    });

    // #6 Add vwap candidates
    vwapCandidates.forEach(ticker => {
      if (!selectedTickers.includes(ticker)) {
        selectedTickers.push(ticker);
      }
      if (!stockTypes[ticker]) stockTypes[ticker] = [];
      stockTypes[ticker].push('vwap_candidate');
    });

    // Final stocks to display sort by selected tickers
    const displayStocks = selectedTickers.map(ticker => ({
      ...stocks[ticker],
      _types: stockTypes[ticker] || []
    }));

    setDisplayStocks(displayStocks);
  }, [stocks]);

  useEffect(() => {
    if (socket) {
      const handleStockUpdate = (data: Stock) => {
        console.log('Received stock update:', data.ticker, data);
        setStocks(prevStocks => {
          // Check if this ticker already exists
          const existingStock = prevStocks[data.ticker];
          if (existingStock) {
            console.log(`Updating existing stock: ${data.ticker}`);
          } else {
            console.log(`Adding new stock: ${data.ticker}`);
          }

          // Create a new object to ensure React detects the change
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...data,
            _lastUpdate: Date.now() // Add timestamp to force re-render
          };

          return newStocks;
        });
      };

      const handleIndicatorsUpdate = (data: any) => {
        console.log('Received technical analysis update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            indicators: data.indicators
          };
          return newStocks;
        });
      };

      const handleScoresUpdate = (data: any) => {
        console.log('Received technical analysis update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            scores: data.scores
          };
          return newStocks;
        });
      };

      const handleStockPriceUpdate = (data: any) => {
        console.log('Received stock price update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            price: data.price
          };
          return newStocks;
        });
      };

      const handleStockVolumeUpdate = (data: any) => {
        console.log('Received stock volume update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            volume: data.volume
          };
          return newStocks;
        });
      };

      const handleCandleUpdate = (data: {
        ticker: string;
        candle: {
          open: number;
          close: number;
          high: number;
          low: number;
          volume: number;
          timestamp: string;
        };
      }) => {
        console.log('Received candle update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          if (newStocks[data.ticker]?.candles) {
            if (newStocks[data.ticker]?.candles?.map(candle => candle.timestamp).includes(data.candle.timestamp)) {
              newStocks[data.ticker] = {
                ...newStocks[data.ticker],
                candles: newStocks[data.ticker]?.candles?.map((candle: { open: number, close: number, high: number, low: number, volume: number, timestamp: string }) => {
                  if (candle.timestamp === data.candle.timestamp) {
                    return {
                      ...candle,
                      close: data.candle.close,
                      open: data.candle.open,
                      high: data.candle.high,
                      low: data.candle.low,
                      volume: data.candle.volume
                    };
                  }
                  return candle;
                })
              };
            } else {
              newStocks[data.ticker] = {
                ...newStocks[data.ticker],
                candles: [...(newStocks[data.ticker]?.candles || []), data.candle]
              };
            }
          }
          return newStocks;
        });
      };

      const handleMarketContextUpdate = (data: any) => {
        console.log('Received market context update:', data);
        setMarketContext(data);
      };

      const handleFireEmojiStatusUpdate = (data: any) => {
        console.log('Received fire emoji status update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            fire_emoji_status: data.fire_emoji_status
          };
          return newStocks;
        });
      };

      const handleExplosionEmojiStatusUpdate = (data: any) => {
        console.log('Received explosion emoji status update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            explosion_emoji_status: data.explosion_emoji_status
          };
          return newStocks;
        });
      };

      const handleCoachingNarrativeUpdate = (data: any) => {
        console.log('Received coaching narrative update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            narrative: data.narrative
          };
          return newStocks;
        });
      };

      const handleStrategyUpdate = (data: any) => {
        console.log('Received strategy update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            strategy: data.strategy
          };
          return newStocks;
        });
      };

      const handlePrevClosePriceUpdate = (data: any) => {
        console.log('Received prev close price update:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            prev_close_price: data.prev_close_price
          };
          return newStocks;
        });
      };

      const handleUnsubscribe = (data: any) => {
        console.log('Received unsubscribe:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          delete newStocks[data.ticker];
          return newStocks;
        });
      };

      const handleOrderbook = (data: any) => {
        console.log('Received orderbook:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[data.ticker] = {
            ...newStocks[data.ticker],
            orderbook: data.orderbook
          };
          return newStocks;
        });
      }

      socket.on('market_context', handleMarketContextUpdate);
      socket.on('stock_update', handleStockUpdate);
      socket.on('indicators', handleIndicatorsUpdate);
      socket.on('scores', handleScoresUpdate);
      socket.on('stock_price', handleStockPriceUpdate);
      socket.on('stock_volume', handleStockVolumeUpdate);
      socket.on('candle', handleCandleUpdate);
      socket.on('fire_emoji_status', handleFireEmojiStatusUpdate);
      socket.on('explosion_emoji_status', handleExplosionEmojiStatusUpdate);
      socket.on('coaching_narrative', handleCoachingNarrativeUpdate);
      socket.on('strategy', handleStrategyUpdate);
      socket.on('prev_close_price', handlePrevClosePriceUpdate);
      socket.on('unsubscribe', handleUnsubscribe);
      socket.on('orderbook', handleOrderbook)

      // Cleanup function
      return () => {
        socket.off('market_context', handleMarketContextUpdate);
        socket.off('stock_update', handleStockUpdate);
        socket.off('indicators', handleIndicatorsUpdate);
        socket.off('scores', handleScoresUpdate);
        socket.off('stock_price', handleStockPriceUpdate);
        socket.off('stock_volume', handleStockVolumeUpdate);
        socket.off('candle', handleCandleUpdate);
        socket.off('fire_emoji_status', handleFireEmojiStatusUpdate);
        socket.off('explosion_emoji_status', handleExplosionEmojiStatusUpdate);
        socket.off('coaching_narrative', handleCoachingNarrativeUpdate);
        socket.off('strategy', handleStrategyUpdate);
        socket.off('prev_close_price', handlePrevClosePriceUpdate);
        socket.off('unsubscribe', handleUnsubscribe);
      };
    }
  }, [socket]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_market_context`)
      .then(response => response.json())
      .then(data => {
        console.log('Received market context:', data);
        setMarketContext(data);
      });

    fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_stock_data`)
      .then(response => response.json())
      .then(data => {
        const stock_data = data.reduce((acc: { [key: string]: Stock }, stock: Stock) => {
          acc[stock.ticker] = stock;
          return acc;
        }, {});
        setStocks(stock_data);
      });
  }, []);

  // Only fetch positions and allow trading toggle if moomooAccount exists
  useEffect(() => {
    if (moomooAccount) {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_positions`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('doppler_token')}` }
      })
        .then(response => response.json())
        .then(data => {
          setPositions({ ...data });
        });
    } else {
      setPositions({});
    }
  }, [moomooAccount]);

  useEffect(() => {
    // Fetch initial buy features state only if moomooAccount exists
    if (moomooAccount) {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_buy_features_status`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('doppler_token')}` }
      })
        .then(response => response.json())
        .then(data => {
          setBuyFeaturesEnabled(data.enabled);
        })
        .catch(error => {
          console.error('Error fetching buy features status:', error);
        });
    } else {
      setBuyFeaturesEnabled(false);
    }
  }, [moomooAccount]);

  useEffect(() => {
    if (moomooAccount && socket) {
      const handlePositionsUpdate = (data: any) => {
        console.log('Received positions update:', data);
        setPositions({ ...data });
      };
      socket.on(`positions_update_${moomooAccount.id}`, handlePositionsUpdate);
      return () => {
        socket.off(`positions_update_${moomooAccount.id}`);
      };
    }
  }, [moomooAccount, socket]);

  const handleBuyFeaturesToggle = async (enabled: boolean) => {
    setToggleLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/toggle_buy_features`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('doppler_token')}`
        },
        body: JSON.stringify({ enabled }),
      });
      if (response.ok) {
        setBuyFeaturesEnabled(enabled);
      } else {
        console.error('Failed to toggle buy features');
      }
    } catch (error) {
      console.error('Error toggling buy features:', error);
    } finally {
      setToggleLoading(false);
    }
  };

  const handleSelectStock = (ticker: string) => {
    setCandleLoading(prev => [...prev, ticker]);
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_candles?ticker=${ticker}`)
      .then(response => response.json())
      .then(data => {
        console.log('Received candle data:', data);
        setStocks(prevStocks => {
          const newStocks = { ...prevStocks };
          newStocks[ticker] = {
            ...newStocks[ticker],
            candles: data
          };
          return newStocks;
        });
        setCandleLoading(prev => prev.filter(ticker => ticker !== ticker));
        setSelectedTickers(prev => [...prev, ticker]);
      });
  };

  const handleSellStock = async (ticker: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/exit_position`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('doppler_token')}`
      },
      body: JSON.stringify({ ticker }),
    });
    if (response.ok) {
      console.log('Stock sold successfully');
    } else {
      console.error('Failed to sell stock');
    }
  };

  return (
    <Container maxWidth={false} sx={{ py: 4, maxWidth: '1700px' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Momentum Trading
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          Real-time momentum analysis and automated trading signals
        </Typography>

        {/* Buy Features Toggle */}
        {moomooAccount && (
          <Paper sx={{ p: 2, mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="h6" gutterBottom>
                  Macro Score: {marketContext?.score} - {marketContext?.signal && marketContext?.signal}
                </Typography>
                <Box className='flex gap-2'>
                  <Typography variant='body2' fontWeight='bold'> Breadth: {marketContext?.components?.breadth} </Typography>
                  <Typography variant='body2' fontWeight='bold'> Momentum: {marketContext?.components?.momentum ? 'True' : 'False'} </Typography>
                  <Typography variant='body2' fontWeight='bold'> Nasdaq/Dow: {marketContext?.components?.nasdaq_dow ? 'True' : 'False'} </Typography>
                  <Typography variant='body2' fontWeight='bold'> VIX: {marketContext?.components?.vix} </Typography>
                  <Typography variant='body2' fontWeight='bold'> Sector Strength: {marketContext?.components?.sector_strength} </Typography>
                </Box>
              </Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={buyFeaturesEnabled}
                    onChange={() => handleBuyFeaturesToggle(!buyFeaturesEnabled)}
                    disabled={toggleLoading}
                    color="primary"
                    size="medium"
                  />
                }
                label={
                  <Typography variant="body1" fontWeight="medium">
                    {buyFeaturesEnabled ? 'Buy Features Enabled' : 'Buy Features Disabled'}
                  </Typography>
                }
              />
            </Box>
          </Paper>
        )}
      </Box>

      {/* Selected Stocks Candlestick Chart and Description */}
      {
        displayStocks
          .filter(stock => selectedTickers.includes(stock.ticker))
          .map((stock) => (
            <Box key={stock.ticker} sx={{ mb: 4 }}>
              <Grid container spacing={2}>
                <Grid size={8}>
                  <CandlestickChart stock={stock} />
                </Grid>
                <Grid size={4}>
                  <StockDescription stock={stock} onUnselect={() => setSelectedTickers(prev => prev.filter(ticker => ticker !== stock.ticker))} />
                </Grid>
              </Grid>
            </Box>
          ))
      }

      {/* Candidate Stocks Table */}
      <Paper sx={{ mb: 4 }}>
        <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">
            Candidate Stocks
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell align="right">Conf Score</TableCell>
                <TableCell align="right">Price</TableCell>
                <TableCell align="right">Tech Score</TableCell>
                <TableCell align="center">RVOL</TableCell>
                <TableCell align="center">A2V</TableCell>
                <TableCell align="center">Vol Ratio</TableCell>
                <TableCell align="center">HOD</TableCell>
                <TableCell align="center">Slope</TableCell>
                <TableCell align="center">Volatility</TableCell>
                <TableCell align="center">ATR Spread</TableCell>
                <TableCell align="center">ROC</TableCell>
                <TableCell align="center">ADX</TableCell>
                <TableCell align="right">Float</TableCell>
                <TableCell align="center">Volume</TableCell>
                <TableCell align="center">View</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {
                displayStocks
                  .map((stock) => {
                    const isAboveVWAP = stock?.price && stock.price > (stock?.indicators?.VWAP || 0);
                    const isAllGreen = checkAllGreen(stock);
                    return (
                      <TableRow
                        key={stock.ticker}
                        hover
                        sx={{
                          backgroundColor: isAllGreen
                            ? '#4ddf5330'
                            : isAboveVWAP
                              ? 'action.hover'
                              : 'inherit',
                          '&:hover': {
                            backgroundColor: isAllGreen
                              ? 'success.main'
                              : isAboveVWAP
                                ? 'action.selected'
                                : undefined,
                          },
                        }}
                      >
                        {/* Symbol */}
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle2" fontWeight="bold">
                              {
                                stock.explosion_emoji_status ? '💥' : stock.fire_emoji_status ? '🔥' : ''
                              }
                              {stock.ticker.replace('US.', '')}
                              {
                                stock?.indicators?.Trend === 1 ? '🟢' : stock?.indicators?.Trend === -1 ? '🔴' : ''
                              }
                            </Typography>
                            {stock._types?.map((type, index) => {
                              let color = 'default';
                              let label = '';

                              switch (type) {
                                case 'session_gainer':
                                  color = 'error';
                                  label = 'SG';
                                  break;
                                case 'all_green':
                                  color = 'success';
                                  label = 'AG';
                                  break;
                                case 'rapid_5green':
                                  color = 'warning';
                                  label = 'R+5';
                                  break;
                                case 'rapid':
                                  color = 'info';
                                  label = 'R';
                                  break;
                                case 'top_5m':
                                  color = 'secondary';
                                  label = '5M';
                                  break;
                                case 'vwap_candidate':
                                  color = 'primary';
                                  label = 'VWAP';
                                  break;
                              }

                              return (
                                <Box
                                  key={index}
                                  sx={{
                                    backgroundColor: `${color}.main`,
                                    color: `${color}.contrastText`,
                                    px: 0.5,
                                    py: 0.25,
                                    borderRadius: 0.5,
                                    fontSize: '0.7rem',
                                    fontWeight: 'bold',
                                    minWidth: '20px',
                                    textAlign: 'center'
                                  }}
                                  title={type.replace('_', ' ')}
                                >
                                  {label}
                                </Box>
                              );
                            })}
                          </Box>
                        </TableCell>
                        {/* Confirmation Score */}
                        <TableCell align="right">
                          <Typography variant="caption">
                            {formatNumber(stock?.scores?.confirmation_score * 100 || 0)}
                          </Typography>
                        </TableCell>
                        {/* Price */}
                        <TableCell align="right">
                          <Typography variant="caption">
                            ${formatNumber(stock.price || 0, 4)}
                          </Typography>
                        </TableCell>
                        {/* Technical Score */}
                        <TableCell align="right">
                          <Typography
                            variant="caption"
                            sx={{
                              color: getIndicatorColor('technical_score', stock?.scores?.technical_score * 100),
                            }}
                          >
                            {formatNumber(stock?.scores?.technical_score * 100 || 0)}
                          </Typography>
                        </TableCell>
                        {/* RVOL */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                            sx={{
                              color: getIndicatorColor('rvol', stock?.indicators?.RVol || 0)
                            }}
                          >
                            {formatNumber(stock?.indicators?.RVol || 0)}
                          </Typography>
                        </TableCell>
                        {/* ATR_to_VWAP */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                            sx={{
                              color: getIndicatorColor('a2v', stock?.indicators?.ATR_to_VWAP || 0)
                            }}
                          >
                            {formatNumber(stock?.indicators?.ATR_to_VWAP || 0, 4)}
                          </Typography>
                        </TableCell>
                        {/* Volume Ratio */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                            sx={{
                              color: getIndicatorColor('volume_ratio', stock?.indicators?.Volume_Ratio || 0)
                            }}
                          >
                            {formatNumber(stock?.indicators?.Volume_Ratio || 0)}
                          </Typography>
                        </TableCell>
                        {/* HOD */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                            sx={{
                              color: getIndicatorColor('atr_hod', stock?.indicators?.ATR_to_HOD || 0)
                            }}
                          >
                            {formatNumber(stock?.indicators?.ATR_to_HOD || 0)}
                          </Typography>
                        </TableCell>
                        {/* VWAP Slope */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                            sx={{
                              color: getIndicatorColor('vwap_slope', stock?.indicators?.VWAP_Slope || 0)
                            }}
                          >
                            {formatNumber(stock?.indicators?.VWAP_Slope || 0, 4)}
                          </Typography>
                        </TableCell>
                        {/* Volatility */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                            sx={{
                              color: getIndicatorColor('zenp', stock?.indicators?.ZenP || 0)
                            }}
                          >
                            {formatNumber(stock?.indicators?.ZenP || 0)}
                          </Typography>
                        </TableCell>
                        {/* ATR Spread */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                            sx={{
                              color: getIndicatorColor('atr_spread', stock?.indicators?.ATR_Spread || 0)
                            }}
                          >
                            {formatNumber(stock?.indicators?.ATR_Spread || 0)}
                          </Typography>
                        </TableCell>
                        {/* ROC */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                          >
                            {formatNumber(stock?.indicators?.ROC || 0)}
                          </Typography>
                        </TableCell>
                        {/* ADX */}
                        <TableCell align="center">
                          <Typography
                            variant="caption"
                          >
                            {formatNumber(stock?.indicators?.ADX || 0)}
                          </Typography>
                        </TableCell>
                        {/* Float */}
                        <TableCell align="right">
                          <Typography
                            variant="caption"
                          >
                            {formatLargeNumber(stock.float_share || 0)}
                          </Typography>
                        </TableCell>
                        {/* Volume */}
                        <TableCell align="center">
                          <Typography variant="caption">
                            {formatLargeNumber(stock.volume || 0)}
                          </Typography>
                        </TableCell>
                        {/* View */}
                        <TableCell align="center">
                          <Button variant="contained" color="primary" onClick={() => handleSelectStock(stock.ticker)}>
                            {candleLoading.includes(stock.ticker) ? 'Loading...' : 'Select'}
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
              }
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Positions Table */}
      {
        moomooAccount && buyFeaturesEnabled && (
          <Paper sx={{ mb: 4 }}>
            <Box sx={{ p: 3, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6">
                Positions
              </Typography>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell align="center">Symbol</TableCell>
                    <TableCell align="center">Quantity</TableCell>
                    <TableCell align="center">Average Cost</TableCell>
                    <TableCell align="center">PL Value</TableCell>
                    <TableCell align="center">Sell Value</TableCell>
                    <TableCell align="center">Initial Time</TableCell>
                    <TableCell align="center">Action</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.values(positions).map((item: any, index: number) => (
                    <TableRow key={index} hover>
                      <TableCell align="center" sx={{ padding: '5px' }}>
                        <Typography variant='caption'>
                          {item.ticker.replace('US.', '')}
                        </Typography>
                      </TableCell>
                      <TableCell align="center" sx={{ padding: '5px' }}>
                        <Typography variant='caption'>
                          {formatLargeNumber(item.qty)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center" sx={{ padding: '5px' }}>
                        <Typography variant='caption'>
                          {formatNumber(item.average_cost)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center" sx={{ padding: '5px' }}>
                        <Typography variant='caption'>
                          {formatNumber(item.today_pl_val)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center" sx={{ padding: '5px' }}>
                        <Typography variant='caption'>
                          {formatNumber(item.today_sell_val)}
                        </Typography>
                      </TableCell>
                      <TableCell align="center" sx={{ padding: '5px' }}>
                        <Typography variant='caption'>
                          {
                            humanReadableDateTime(item.orders?.filter((order: any) => order?.order_status === 'FILLED_ALL')[0]?.create_time || '')
                          }
                        </Typography>
                      </TableCell>
                      <TableCell align="center" sx={{ padding: '5px' }}>
                        <Button variant="contained" color="primary" onClick={() => handleSellStock(item.ticker)}>
                          Sell
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        )
      }
    </Container>
  );
} 