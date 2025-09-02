import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
    Tooltip,
  Grid,
  LinearProgress, IconButton,
} from '@mui/material';
import {
  AccountBalance,
  AccountBalanceWallet,
    CheckCircle,
    PauseCircleFilled,
    Settings
} from '@mui/icons-material';

interface AccountDetailsCardProps {
  account: {
    id: string;
    userId: string;
    userEmail: string;
    userName: string;
    accountId: string;
    email?: string;
    phone?: string;
    status: string;
    tradingEnabled: boolean;
    tradingAmount: number;
    tradingAccount: 'cash' | 'margin';
    createdAt: string;
    approvedAt?: string;
    rejectedAt?: string;
    rejectionReason?: string;
    host?: string;
    port?: number;
    cashAccountId?: number;
    marginAccountId?: number;
    maxDailyLoss?: number;
    riskPerTrade?: number;
  };
  onAction: (action: string, accountId: string, data?: any) => void;
  loading?: boolean;
}

export default React.memo(function AccountDetailsCard({
  account,
  onAction,
  loading = false
}: AccountDetailsCardProps) {
  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              {account.userName}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Tooltip title="Edit Trading Settings">
              <IconButton
                color="primary"
                onClick={() => onAction('edit_trading', account.id)}
                disabled={loading}
                size="small"
              >
                <Settings />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Grid container spacing={2} sx={{ mb: 2 }}>
          <Grid size={4}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="h6" color="primary">
                {account.userEmail}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Email
              </Typography>
            </Box>
          </Grid>
          <Grid size={4}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="h6" color="primary">
                {account.phone || "N/A"}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Phone
              </Typography>
            </Box>
          </Grid>
          <Grid size={4}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="h6" color="primary">
                ${account.tradingAmount}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Trading Amount
              </Typography>
            </Box>
          </Grid>
          <Grid size={4}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="h6" color={account.tradingEnabled ? "primary" : "warning"}>
                {
                  account.tradingEnabled ? <CheckCircle /> : <PauseCircleFilled />
                }
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Trading Enabled
              </Typography>
            </Box>
          </Grid>
          <Grid size={4}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="h6" color={account.status == "approved" ? "primary" : "warning"}>
                {
                  account.status == "approved" ? <CheckCircle /> : <PauseCircleFilled />
                }
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Account Status
              </Typography>
            </Box>
          </Grid>
          <Grid size={4}>
            <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="h6" color={account.tradingAccount == "cash" ? "primary" : "warning"}>
                {
                  account.tradingAccount == "cash" ? "Cash" : "Margin"
                }
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Trading Account
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {loading && <LinearProgress sx={{ mt: 2 }} />}
      </CardContent>
    </Card>
  );
});
