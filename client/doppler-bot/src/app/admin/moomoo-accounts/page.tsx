'use client';

import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Pending,
  Refresh,
  Edit,
  Settings,
  Warning,
  PlayArrow,
  Pause,
  ExitToApp,
  Security,
  Replay,
  Sync,
  AccountBalance,
  AccountBalanceWallet,
} from '@mui/icons-material';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { adminApi } from '@/utils/api';
import AdminRoute from '@/components/AdminRoute';
import AccountDetailsCard from '@/components/admin/AccountDetailsCard';
import { transformPendingRequests, transformAccounts } from '@/utils/dataTransformers';
import { PendingRequest, Account } from "@/types";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function AdminMoomooAccountsPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [tabValue, setTabValue] = useState(0);
  const [pendingRequests, setPendingRequests] = useState<PendingRequest[]>([]);
  const [allAccounts, setAllAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Dialog states
  const [rejectDialog, setRejectDialog] = useState<{
    open: boolean;
    accountId: string;
    userName: string;
    reason: string;
  }>({
    open: false,
    accountId: '',
    userName: '',
    reason: '',
  });

  const [openDAssignDialog, setOpenDAssignDialog] = useState<{
    open: boolean;
    accountId: string;
    userName: string;
    host: string;
    port: string;
  }>({
    open: false,
    accountId: '',
    userName: '',
    host: '',
    port: '',
  });

  const [tradingSettingsDialog, setTradingSettingsDialog] = useState<{
    open: boolean;
    accountId: string;
    userName: string;
    tradingEnabled: boolean;
    tradingAmount: number;
    tradingAccount: 'cash' | 'margin';
  }>({
    open: false,
    accountId: '',
    userName: '',
    tradingEnabled: false,
    tradingAmount: 0,
    tradingAccount: 'cash',
  });

  // Fix: Add individual loading states for better UX
  const [operationLoading, setOperationLoading] = useState<Record<string, boolean>>({});

  const setLoadingForOperation = (operation: string, loading: boolean) => {
    setOperationLoading(prev => ({ ...prev, [operation]: loading }));
  };

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user, tabValue]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');

      if (tabValue === 0) {
        const response = await adminApi.getPendingRequests();
        if (response.success && response.data) {
          setPendingRequests(transformPendingRequests(response.data));
        }
      } else if (tabValue === 1) {
        const response = await adminApi.getAllAccounts();
        if (response.success && response.data) {
          setAllAccounts(transformAccounts(response.data));
        }
      }
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    try {
      setLoadingForOperation('reject', true);
      setError('');

      const response = await adminApi.rejectAccount(
        rejectDialog.accountId,
        rejectDialog.reason
      );

      if (response.success) {
        setSuccess('Account rejected successfully');
        setRejectDialog({ open: false, accountId: '', userName: '', reason: '' });
        loadData();
      } else {
        setError(response.error || 'Failed to reject account');
      }
    } catch (error) {
      console.error('Error rejecting account:', error);
      setError('Failed to reject account');
    } finally {
      setLoadingForOperation('reject', false);
    }
  };

  const openRejectDialog = (accountId: string, userName: string) => {
    setRejectDialog({
      open: true,
      accountId,
      userName,
      reason: '',
    });
  };

  const activeOpenDAssignDialog = (accountId: string, userName: string) => {
    setOpenDAssignDialog({
      open: true,
      accountId,
      userName,
      host: '',
      port: '',
    });
  };

  const handleAssignSubmit = async () => {
    try {
      setLoadingForOperation('assign', true);
      setError('');
      const response = await adminApi.assignOpenD(openDAssignDialog.accountId, openDAssignDialog.host, openDAssignDialog.port);
      if (response.success) {
        setSuccess('OpenD host and port assigned successfully');
        setOpenDAssignDialog({ open: false, accountId: '', userName: '', host: '', port: '' });
        loadData();
      } else {
        setError(response.error || 'Failed to assign OpenD host and port');
      }
    } catch (error) {
      console.error('Error assigning OpenD host and port:', error);
      setError('Failed to assign OpenD host and port');
    } finally {
      setLoadingForOperation('assign', false);
    }
  };

  const handleApprove = async (accountId: string) => {
    try {
      setLoadingForOperation('approve', true);
      setError('');
      const response = await adminApi.approveAccount(accountId);
      if (response.success) {
        setSuccess('Account approved successfully');
        loadData();
      } else {
        setError(response.error || 'Failed to approve account');
      }
    } catch (error) {
      console.error('Error approving account:', error);
      setError('Failed to approve account');
    } finally {
      setLoadingForOperation('approve', false);
    }
  };

  const openTradingSettingsDialog = (account: Account) => {
    setTradingSettingsDialog({
      open: true,
      accountId: account.id,
      userName: account.userName,
      tradingEnabled: account.tradingEnabled,
      tradingAmount: account.tradingAmount,
      tradingAccount: account.tradingAccount,
    });
  };

  const handleTradingSettingsUpdate = async () => {
    try {
      setLoadingForOperation('update_trading', true);
      setError('');

      const response = await adminApi.updateAccountTradingSettings(
        tradingSettingsDialog.accountId,
        {
          trading_enabled: tradingSettingsDialog.tradingEnabled,
          trading_amount: tradingSettingsDialog.tradingAmount,
        }
      );

      if (response.success) {
        // Also update account type if changed
        if (tradingSettingsDialog.tradingAccount !== 'cash') {
          await adminApi.switchAccountType(tradingSettingsDialog.accountId, tradingSettingsDialog.tradingAccount);
        }

        setSuccess('Trading settings updated successfully');
        setTradingSettingsDialog({ open: false, accountId: '', userName: '', tradingEnabled: false, tradingAmount: 0, tradingAccount: 'cash' });
        loadData();
      } else {
        setError(response.error || 'Failed to update trading settings');
      }
    } catch (error) {
      console.error('Error updating trading settings:', error);
      setError('Failed to update trading settings');
    } finally {
      setLoadingForOperation('update_trading', false);
    }
  };

  const handleAccountAction = (action: string, accountId: string, data?: any) => {
    switch (action) {
      case 'edit_trading':
        const account = allAccounts.find(acc => acc.id === accountId);
        if (account) {
          openTradingSettingsDialog(account);
        }
        break;
      default:
        console.warn('Unknown action:', action);
    }
  };

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <LinearProgress />
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  return (
    <AdminRoute>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Moomoo Account Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Comprehensive management of moomoo account connections and trading operations
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}

        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label={`Pending Requests (${pendingRequests.length})`} />
            <Tab label="All Accounts" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          {/* Pending Requests tab remains the same */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Pending Account Requests</Typography>
                <Button
                  startIcon={<Refresh />}
                  onClick={loadData}
                  disabled={loading}
                >
                  Refresh
                </Button>
              </Box>

              {pendingRequests.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary">
                    No pending requests
                  </Typography>
                </Box>
              ) : (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>User</TableCell>
                        <TableCell>Account ID</TableCell>
                        <TableCell>Contact</TableCell>
                        <TableCell>Requested</TableCell>
                        <TableCell>Host</TableCell>
                        <TableCell>Port</TableCell>
                        <TableCell>Cash Account ID</TableCell>
                        <TableCell>Margin Account ID</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {pendingRequests.map((request) => (
                        <TableRow key={request.id}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="bold">
                                {request.userName}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {request.userEmail}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>{request.accountId}</TableCell>
                          <TableCell>
                            {request.email && (
                              <Typography variant="body2">{request.email}</Typography>
                            )}
                            {request.phone && (
                              <Typography variant="body2">{request.phone}</Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            {new Date(request.createdAt).toLocaleDateString()}
                          </TableCell>
                          <TableCell>{request.host}</TableCell>
                          <TableCell>{request.port}</TableCell>
                          <TableCell>{request.cashAccountId}</TableCell>
                          <TableCell>{request.marginAccountId}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Tooltip title="Assign OpenD Configuration">
                                <IconButton
                                  color="primary"
                                  onClick={() => activeOpenDAssignDialog(request.id, request.userName)}
                                  disabled={loading || operationLoading.assign}
                                >
                                  <Settings />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Approve">
                                <IconButton
                                  color="success"
                                  onClick={() => handleApprove(request.id)}
                                  disabled={loading || operationLoading.approve}
                                >
                                  <CheckCircle />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Reject">
                                <IconButton
                                  color="error"
                                  onClick={() => openRejectDialog(request.id, request.userName)}
                                  disabled={loading || operationLoading.reject}
                                >
                                  <Cancel />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* All Accounts tab - Now using AccountDetailsCard components */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">All Moomoo Accounts</Typography>
                <Button
                  startIcon={<Refresh />}
                  onClick={loadData}
                  disabled={loading}
                >
                  Refresh
                </Button>
              </Box>

              {allAccounts.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary">
                    No accounts found
                  </Typography>
                </Box>
              ) : (
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  {allAccounts.map((account) => (
                      <Grid size={4}>
                    <AccountDetailsCard
                      key={account.id}
                      account={account}
                      onAction={handleAccountAction}
                      loading={loading}
                    />
                      </Grid>
                  ))}
                </Grid>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        {/* Reject Dialog */}
        <Dialog
          open={rejectDialog.open}
          onClose={() => setRejectDialog({ open: false, accountId: '', userName: '', reason: '' })}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Reject Account Request</DialogTitle>
          <DialogContent>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Reject account request for <strong>{rejectDialog.userName}</strong>?
            </Typography>
            <TextField
              fullWidth
              label="Rejection Reason"
              multiline
              rows={3}
              value={rejectDialog.reason}
              onChange={(e) => setRejectDialog({ ...rejectDialog, reason: e.target.value })}
              margin="normal"
              required
              helperText="Please provide a reason for rejection"
            />
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setRejectDialog({ open: false, accountId: '', userName: '', reason: '' })}
            >
              Cancel
            </Button>
            <Button
              onClick={handleReject}
              variant="contained"
              color="error"
              disabled={loading || !rejectDialog.reason.trim() || operationLoading.reject}
            >
              {loading || operationLoading.reject ? 'Rejecting...' : 'Reject'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* OpenD Assign Dialog */}
        <Dialog
          open={openDAssignDialog.open}
          onClose={() => setOpenDAssignDialog({ open: false, accountId: '', userName: '', host: '', port: '' })}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Assign OpenD Configuration</DialogTitle>
          <DialogContent>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Assign OpenD host and port for <strong>{openDAssignDialog.userName}</strong>
            </Typography>
            <TextField
              fullWidth
              label="Host"
              value={openDAssignDialog.host}
              onChange={(e) => setOpenDAssignDialog({ ...openDAssignDialog, host: e.target.value })}
              margin="normal"
              required
              placeholder="e.g., 127.0.0.1"
            />
            <TextField
              fullWidth
              label="Port"
              value={openDAssignDialog.port}
              onChange={(e) => setOpenDAssignDialog({ ...openDAssignDialog, port: e.target.value })}
              margin="normal"
              required
              type="number"
              placeholder="e.g., 11111"
            />
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setOpenDAssignDialog({ open: false, accountId: '', userName: '', host: '', port: '' })}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAssignSubmit}
              variant="contained"
              color="success"
              disabled={loading || !openDAssignDialog.host.trim() || !openDAssignDialog.port.trim() || operationLoading.assign}
            >
              {loading || operationLoading.assign ? 'Assigning...' : 'Assign Configuration'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Trading Settings Dialog */}
        <Dialog
          open={tradingSettingsDialog.open}
          onClose={() => setTradingSettingsDialog({ open: false, accountId: '', userName: '', tradingEnabled: false, tradingAmount: 0, tradingAccount: 'cash' })}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Update Trading Settings</DialogTitle>
          <DialogContent>
            <Typography variant="body1" sx={{ mb: 2 }}>
              Update trading settings for <strong>{tradingSettingsDialog.userName}</strong>
            </Typography>

            <Box sx={{ mb: 3 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={tradingSettingsDialog.tradingEnabled}
                    onChange={(e) => setTradingSettingsDialog({
                      ...tradingSettingsDialog,
                      tradingEnabled: e.target.checked
                    })}
                  />
                }
                label="Enable Trading"
              />
              <Typography variant="body2" color="text.secondary">
                Allow this user to perform automated trading
              </Typography>
            </Box>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Account Type</InputLabel>
              <Select
                value={tradingSettingsDialog.tradingAccount}
                onChange={(e) => setTradingSettingsDialog({
                  ...tradingSettingsDialog,
                  tradingAccount: e.target.value as 'cash' | 'margin'
                })}
                label="Account Type"
              >
                <MenuItem value="cash">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <AccountBalance sx={{ mr: 1 }} />
                    Cash Account
                  </Box>
                </MenuItem>
                <MenuItem value="margin">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <AccountBalanceWallet sx={{ mr: 1 }} />
                    Margin Account
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Trading Amount ($)"
              type="number"
              value={tradingSettingsDialog.tradingAmount}
              onChange={(e) => setTradingSettingsDialog({
                ...tradingSettingsDialog,
                tradingAmount: Number(e.target.value)
              })}
              margin="normal"
              required
              inputProps={{ min: 0, step: 0.01 }}
              helperText="Maximum amount per trade"
            />
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => setTradingSettingsDialog({ open: false, accountId: '', userName: '', tradingEnabled: false, tradingAmount: 0, tradingAccount: 'cash' })}
            >
              Cancel
            </Button>
            <Button
              onClick={handleTradingSettingsUpdate}
              variant="contained"
              color="primary"
              disabled={loading || tradingSettingsDialog.tradingAmount <= 0 || operationLoading.update_trading}
            >
              {loading || operationLoading.update_trading ? 'Updating...' : 'Update Settings'}
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </AdminRoute>
  );
}