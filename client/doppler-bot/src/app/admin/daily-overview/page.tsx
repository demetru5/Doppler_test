'use client';

import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  AccountBalance,
  AttachMoney,
  Percent,
  Timeline,
} from '@mui/icons-material';
import AdminRoute from '@/components/AdminRoute';
import { adminApi } from '@/utils/api';

interface DailyOverview {
  accountId: string;
  userId: string;
  userName: string;
  userEmail: string;
  totalAmount: number;
  totalPnL: number;
  totalPnLPercent: number;
  positions: Position[];
  orders: Order[];
  tradingEnabled: boolean;
  lastUpdated: string;
}

interface Position {
  ticker: string;
  qty: number;
  averageCost: number;
  currentPrice: number;
  plRatio: number;
  plVal: number;
  todayPlVal: number;
  todayTrdVal: number;
  todayBuyQty: number;
  todayBuyVal: number;
  todaySellQty: number;
  todaySellVal: number;
}

interface Order {
  ticker: string;
  trdSide: string;
  orderType: string;
  orderStatus: string;
  orderId: string;
  qty: number;
  price: number;
  createTime: string;
  updatedTime: string;
  dealtQty: number;
  dealtAvgPrice: number;
  session: string;
}

export default function DailyOverview() {
  const [dailyOverview, setDailyOverview] = useState<DailyOverview[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDailyOverview();
  }, []);

  const loadDailyOverview = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await adminApi.getDailyOverview();
      if (response.success && response.data) {
        setDailyOverview(response.data.overview);
      } else {
        setError(response.error || 'Failed to load daily overview');
      }
    } catch (error) {
      console.error('Error loading daily overview:', error);
      setError('Failed to load daily overview');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadDailyOverview();
  };

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'success' : 'error';
  };

  const getPnLIcon = (pnl: number) => {
    return pnl >= 0 ? <TrendingUp /> : <TrendingDown />;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatPercent = (percent: number) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const calculateTotalStats = () => {
    const totalAmount = dailyOverview.reduce((sum, account) => sum + account.totalAmount, 0);
    const totalPnL = dailyOverview.reduce((sum, account) => sum + account.totalPnL, 0);
    const totalPnLPercent = totalAmount > 0 ? (totalPnL / totalAmount) * 100 : 0;

    return { totalAmount, totalPnL, totalPnLPercent };
  };

  const { totalAmount, totalPnL, totalPnLPercent } = calculateTotalStats();

  if (loading) {
    return (
      <AdminRoute>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress />
          </Box>
        </Container>
      </AdminRoute>
    );
  }

  return (
    <AdminRoute>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Timeline sx={{ fontSize: 48, color: 'primary.main', mr: 2 }} />
              <Box>
                <Typography variant="h4" component="h1" gutterBottom>
                  Daily Trading Overview
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Real-time trading performance across all accounts
                </Typography>
              </Box>
            </Box>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={handleRefresh}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Overall Stats */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={3}>
            <Card sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      {dailyOverview.length}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Active Accounts
                    </Typography>
                  </Box>
                  <AccountBalance sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={3}>
            <Card sx={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      {formatCurrency(totalAmount)}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Total Amount
                    </Typography>
                  </Box>
                  <AttachMoney sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={3}>
            <Card sx={{
              background: getPnLColor(totalPnL) === 'success'
                ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)'
                : 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      {formatCurrency(totalPnL)}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Total P&L
                    </Typography>
                  </Box>
                  {getPnLIcon(totalPnL)}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={3}>
            <Card sx={{
              background: getPnLColor(totalPnLPercent) === 'success'
                ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
                : 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      {formatPercent(totalPnLPercent)}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      P&L %
                    </Typography>
                  </Box>
                  <Percent sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Accounts Overview */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Account Performance
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {dailyOverview.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  No trading data available
                </Typography>
              </Box>
            ) : (
              dailyOverview.map((account, index) => (
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', borderBottom: '1px solid rgb(48, 48, 48)', padding: 2, marginBottom: 1 }} key={index}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">
                      {account.userName}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {account.userEmail}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Chip
                      label={account.tradingEnabled ? 'Trading Enabled' : 'Trading Disabled'}
                      color={account.tradingEnabled ? 'success' : 'default'}
                      size="small"
                    />
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Total Amount</Typography>
                      <Typography variant="body2" color='text.primary'>
                        {formatCurrency(account.totalAmount)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">Today P/L</Typography>
                      <Typography variant="body2" color={getPnLColor(account.totalPnL) === 'success' ? 'success' : 'error'}>
                        {formatCurrency(account.totalPnL)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">P/L %</Typography>
                      <Typography variant="body2" color={getPnLColor(account.totalPnLPercent) === 'success' ? 'success' : 'error'}>
                        {formatPercent(account.totalPnLPercent)}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              ))
            )}
          </CardContent>
        </Card>
      </Container>
    </AdminRoute>
  );
} 