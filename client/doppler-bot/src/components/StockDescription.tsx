'use client';

import { Box, Typography, Card, CardContent, Chip, Divider, Button, Grid, Tooltip, Paper } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { Stock } from '@/types';
import { formatNumber, getIndicatorColor } from '@/utils/helpers';
import useTypewriter from '@/context/useTypewriter'

interface StockDescriptionProps {
  stock: Stock;
  onUnselect?: () => void;
}

const StockDescription = ({ stock, onUnselect }: StockDescriptionProps) => {
  const { displayedText, isTyping, cursor } = useTypewriter(stock?.narrative?.message);

  const priceChange = (stock.price || 0) - (stock.prev_close_price || 0);
  const priceChangePercent = priceChange > 0 && (stock.prev_close_price || 0) > 0 ? (priceChange / (stock.prev_close_price || 0)) * 100 : 0;

  return (
    <Card sx={{ backgroundColor: '#1e1e1e', color: '#ffffff' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" fontWeight="bold">
            {stock.explosion_emoji_status ? '💥' : stock.fire_emoji_status ? '🔥' : ''}
            {stock.ticker.replace('US.', '')}
            {stock?.indicators?.supertrend === 1 ? '🟢' : stock?.indicators?.supertrend === -1 ? '🔴' : ''}
          </Typography>
          {onUnselect && (
            <Button onClick={onUnselect} variant="contained">Close</Button>
          )}
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="h4" fontWeight="bold" sx={{ color: priceChange >= 0 ? '#4caf50' : '#f44336' }}>
            ${formatNumber(stock.price || 0, 4)}
          </Typography>
          <Grid container spacing={2}>
            <Grid size={4}>
              <Typography variant="body2" sx={{ color: priceChange >= 0 ? '#4caf50' : '#f44336' }}>
                {priceChange >= 0 ? '+' : ''}{formatNumber(priceChange, 4)}
                ({priceChange >= 0 ? '+' : ''}{formatNumber(priceChangePercent, 2)}%)
              </Typography>
            </Grid>
            <Grid size={4}>
              <Typography variant="body2" align='center' sx={{ color: getIndicatorColor('technical_score', stock?.scores?.technical_score || 0) }}>
                Momentum: {stock?.scores?.technical_score ? (stock?.scores?.technical_score * 100).toFixed(0) : '-'}
              </Typography>
            </Grid>
            {
              stock.strategy && (
                <Grid size={4}>
                  <Typography variant="body2" align='center' sx={{ color: getIndicatorColor('probability', stock.strategy.probability || 0) }}>
                    Probability: {stock.strategy.probability ? (stock.strategy.probability * 100).toFixed(0) : '-'}%
                  </Typography>
                </Grid>
              )
            }
          </Grid>
        </Box>

        <Divider sx={{ backgroundColor: '#333333', mb: 2 }} />

        {/* Strategy Details Section - Updated to show target evolution */}
        {(stock.strategy && (stock.strategy.state === 'LOCKED' || stock.strategy.entry_price)) && (
          <Box sx={{ my: 2, p: 1.5, bgcolor: 'rgba(0, 242, 195, 0.1)', borderRadius: 1, border: '1px solid rgba(0, 242, 195, 0.3)' }}>
            <Typography variant="h6" fontWeight="bold" sx={{mb: 1}}>
              {stock.strategy.name}
            </Typography>

            {/* Main price chips in a single row */}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'nowrap', mb: stock.strategy.target_history?.length > 1 ? 1 : 0 }}>
              {stock.strategy.entry_price && (
                <Chip size="small" label={`Entry: $${stock.strategy.entry_price.toFixed(2)}`} />
              )}
              {stock.strategy.stop_price && (
                <Chip size="small" label={`Stop: $${stock.strategy.stop_price.toFixed(2)}`} />
              )}
              {stock.strategy.target_price && (
                <Chip
                  size="small"
                  label={`Target: $${stock.strategy.target_price.toFixed(2)}`}
                  color="primary"
                />
              )}
            </Box>

            {/* Target history in a separate row that can wrap */}
            {stock.strategy.target_history && stock.strategy.target_history.length > 1 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                <Typography variant="caption" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                  Target Evolution:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {stock.strategy.target_history.map((target: any, index: number) => {
                    // Only show achieved targets except the current one
                    const isCurrentTarget = index === stock.strategy.current_target_index;
                    if (!target.achieved && !isCurrentTarget) return null;

                    return (
                      <Tooltip
                        key={index}
                        title={target.achieved ?
                          `Target achieved on ${new Date(target.achieved_at).toLocaleString()}` :
                          "Current target"}
                      >
                        <Chip
                          size="small"
                          icon={target.achieved ? <CheckCircleOutlineIcon /> : <TrendingUpIcon />}
                          label={`$${target.price.toFixed(2)}`}
                          sx={{
                            opacity: target.achieved ? 0.7 : 1,
                            color: target.achieved ? 'text.secondary' : 'text.primary',
                            '& .MuiChip-icon': {
                              color: target.achieved ? 'success.main' : 'primary.main'
                            }
                          }}
                        />
                      </Tooltip>
                    );
                  })}
                </Box>
              </Box>
            )}
          </Box>
        )}

        <Divider sx={{ backgroundColor: '#333333', mb: 2 }} />

        {/* Coaching Narrative Section */}
        <Box sx={{ my: 2, p: 1.5, bgcolor: 'rgba(0, 242, 195, 0.1)', borderRadius: 1, border: '1px solid rgba(0, 242, 195, 0.3)' }}>
          <Typography variant="h6" fontWeight="bold">
            Trading Coach
          </Typography>
          <Paper sx={{ p: 2, bgcolor: 'background.default', minHeight: '80px', position: 'relative' }}>
            <Typography
              variant="body2"
              sx={{
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                minHeight: '60px'
              }}
            >
              {displayedText || 'Analyzing market conditions...'}
              <span
                style={{
                  opacity: isTyping ? 1 : 0,
                  transition: 'opacity 0.5s',
                  animation: 'blink 1s step-end infinite'
                }}
              >
                {cursor}
              </span>
            </Typography>
          </Paper>
        </Box>

        <Divider sx={{ backgroundColor: '#333333', mb: 2 }} />

        {/* Orderbook */}
        {stock.orderbook && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" component="h2" fontWeight="bold" sx={{ mb: 1.5 }}>
              Orderbook
            </Typography>
            <Box sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 1,
              p: 2,
              bgcolor: 'rgba(255, 255, 255, 0.05)',
              borderRadius: 1,
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              {/* Bid/Ask Ratio Bar */}
              <Box sx={{ position: 'relative', height: '10px', borderRadius: 1, overflow: 'hidden' }}>
                {(() => {
                  const bidVolume = stock.orderbook.bids[0][1];
                  const askVolume = stock.orderbook.asks[0][1];
                  const totalVolume = bidVolume + askVolume;
                  const bidPercentage = (bidVolume / totalVolume) * 100;
                  const askPercentage = (askVolume / totalVolume) * 100;

                  return (
                    <>
                      {/* Bid side (left) */}
                      <Box sx={{
                        position: 'absolute',
                        left: 0,
                        top: 0,
                        width: `${bidPercentage}%`,
                        height: '100%',
                        bgcolor: 'rgba(76, 175, 80, 0.3)',
                      }} />

                      {/* Ask side (right) */}
                      <Box sx={{
                        position: 'absolute',
                        right: 0,
                        top: 0,
                        width: `${askPercentage}%`,
                        height: '100%',
                        bgcolor: 'rgba(244, 67, 54, 0.3)',
                      }} />
                    </>
                  );
                })()}
              </Box>

              {/* Price and volume labels below the bar */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                  <Typography variant="caption" sx={{ color: '#4caf50', fontWeight: 'bold' }}>
                    Bid: ${stock.orderbook.bids[0][0]}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#4caf50' }}>
                    Size: {stock.orderbook.bids[0][1]}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                  <Typography variant="caption" sx={{ color: '#f44336', fontWeight: 'bold' }}>
                    Ask: ${stock.orderbook.asks[0][0]}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#f44336' }}>
                    Size: {stock.orderbook.asks[0][1]}
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>
        )}

        {/* Market Notes Section */}
        {stock.market_notes && stock.market_notes.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" component="h2">
              Market Notes
            </Typography>
            <Box sx={{ mt: 1 }}>
              {stock.market_notes.map((note, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    mb: 1,
                    p: 1,
                    borderRadius: 1,
                    bgcolor:
                      note.type === 'danger' ? 'rgba(211, 47, 47, 0.5)' :
                        note.type === 'warning' ? 'rgba(255, 152, 0, 0.5)' :
                          'rgba(76, 175, 80, 0.5)',
                    color: 'white',
                    alignItems: 'flex-start'
                  }}
                >
                  {note.icon && (
                    <span style={{ marginRight: '8px' }}>{note.icon}</span>
                  )}
                  <Typography variant="body2">
                    {note.message}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        )}

      </CardContent>
    </Card>
  );
};

export default StockDescription;
