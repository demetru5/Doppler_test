'use client';

import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  TextField,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Slider,
  Alert,
  Chip,
  Divider,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Input,
  RadioGroup,
  Radio,
} from '@mui/material';
import {
  AccountCircle,
  Visibility,
  VisibilityOff,
  Delete,
  Refresh,
  CheckCircle,
  Cancel,
  Pending,
  Warning,
} from '@mui/icons-material';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { moomooAccountApi } from '@/utils/api';

interface MoomooAccount {
  id: string;
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
  tradingAccount?: string;
}

export default function MoomooAccountPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [account, setAccount] = useState<MoomooAccount | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form states
  const [showConnectForm, setShowConnectForm] = useState(false);
  const [formData, setFormData] = useState({
    accountId: '',
    email: '',
    phone: '',
    password: '',
    tradingPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showTradingPassword, setShowTradingPassword] = useState(false);
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});

  // Settings states
  const [tradingEnabled, setTradingEnabled] = useState(false);
  const [tradingAmount, setTradingAmount] = useState(10);
  const [tradingAccount, setTradingAccount] = useState('cash');
  const [settingsLoading, setSettingsLoading] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    if (user) {
      loadAccount();
    }
  }, [user]);

  const loadAccount = async () => {
    try {
      setLoading(true);
      const response = await moomooAccountApi.getAccount();

      if (response.success && response.data) {
        setAccount(response.data.account);
        setTradingEnabled(response.data.account.tradingEnabled);
        setTradingAmount(response.data.account.tradingAmount);
        setTradingAccount(response.data.account.tradingAccount);
      } else if (response.success) {
        setAccount(null);
      }
    } catch (error) {
      console.error('Error loading account:', error);
      setError('Failed to load account information');
    } finally {
      setLoading(false);
    }
  };

  const handleConnectSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    // Validate form
    const errors: { [key: string]: string } = {};
    if (!formData.accountId) errors.accountId = 'Account ID is required';
    if (!formData.password) errors.password = 'Password is required';
    if (!formData.tradingPassword) errors.tradingPassword = 'Trading password is required';
    if (!formData.email && !formData.phone) {
      errors.email = 'Either email or phone number is required';
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    try {
      setLoading(true);
      setError('');

      const response = await moomooAccountApi.connectAccount(formData);

      if (response.success) {
        setSuccess(response.data.message);
        setShowConnectForm(false);
        setFormData({
          accountId: '',
          email: '',
          phone: '',
          password: '',
          tradingPassword: '',
        });
        setFormErrors({});
        // Reload account after successful connection
        setTimeout(() => loadAccount(), 1000);
      } else {
        setError(response.error || 'Failed to connect account');
      }
    } catch (error) {
      console.error('Error connecting account:', error);
      setError('Failed to connect account');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSettings = async () => {
    try {
      setSettingsLoading(true);
      setError('');

      const response = await moomooAccountApi.updateSettings({
        tradingEnabled,
        tradingAmount,
        tradingAccount,
      });

      if (response.success) {
        setSuccess('Trading settings updated successfully');
        if (account) {
          setAccount({
            ...account,
            tradingEnabled,
            tradingAmount,
            tradingAccount,
          });
        }
      } else {
        setError(response.error || 'Failed to update settings');
      }
    } catch (error) {
      console.error('Error updating settings:', error);
      setError('Failed to update settings');
    } finally {
      setSettingsLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!confirm('Are you sure you want to delete your moomoo account connection? This action cannot be undone.')) {
      return;
    }

    try {
      setLoading(true);
      setError('');

      const response = await moomooAccountApi.deleteAccount();

      if (response.success) {
        setSuccess('Account connection deleted successfully');
        setAccount(null);
        setTradingEnabled(false);
        setTradingAmount(10);
      } else {
        setError(response.error || 'Failed to delete account');
      }
    } catch (error) {
      console.error('Error deleting account:', error);
      setError('Failed to delete account');
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'pending':
        return <Chip icon={<Pending />} label="Pending Approval" color="warning" />;
      case 'approved':
        return <Chip icon={<CheckCircle />} label="Approved" color="success" />;
      case 'rejected':
        return <Chip icon={<Cancel />} label="Rejected" color="error" />;
      default:
        return <Chip label={status} />;
    }
  };

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Moomoo Account Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Connect your Moomoo trading account and manage trading settings
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

      {!account ? (
        <Card>
          <CardContent>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <AccountCircle sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Moomoo Account Connected
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Connect your Moomoo trading account to enable automated trading features
              </Typography>
              <Button
                variant="contained"
                size="large"
                onClick={() => setShowConnectForm(true)}
                sx={{
                  background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                  }
                }}
              >
                Connect Moomoo Account
              </Button>
            </Box>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {/* Account Information */}
          <Box sx={{ width: '100%' }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Account Information</Typography>
                  <Box>
                    {getStatusChip(account.status)}
                  </Box>
                </Box>

                <Divider sx={{ mb: 2 }} />

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Account ID</Typography>
                  <Typography variant="body1">{account.accountId}</Typography>
                </Box>

                {account.email && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Email</Typography>
                    <Typography variant="body1">{account.email}</Typography>
                  </Box>
                )}

                {account.phone && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Phone</Typography>
                    <Typography variant="body1">{account.phone}</Typography>
                  </Box>
                )}

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Connected</Typography>
                  <Typography variant="body1">
                    {new Date(account.createdAt).toLocaleDateString()}
                  </Typography>
                </Box>

                {account.status === 'rejected' && account.rejectionReason && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Rejection Reason</Typography>
                    <Typography variant="body1" color="error.main">
                      {account.rejectionReason}
                    </Typography>
                  </Box>
                )}

                {account.status === 'approved' && (
                  <Box sx={{ mt: 2 }}>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<Delete />}
                      onClick={handleDeleteAccount}
                      disabled={loading}
                    >
                      Delete Account
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>

          {/* Trading Settings */}
          <Box sx={{ width: '100%' }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Trading Settings
                </Typography>

                <Divider sx={{ mb: 3 }} />

                {account.status === 'approved' ? (
                  <>
                    <Box sx={{ mb: 3 }}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={tradingEnabled}
                            onChange={(e) => setTradingEnabled(e.target.checked)}
                            disabled={settingsLoading}
                          />
                        }
                        label="Enable Automated Trading"
                      />
                      <Typography variant="body2" color="text.secondary">
                        Allow the system to place trades based on signals
                      </Typography>
                    </Box>

                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" gutterBottom>
                        Trading Amount: ${tradingAmount}
                      </Typography>
                      <Input
                        type="number"
                        value={tradingAmount}
                        onChange={(e) => setTradingAmount(Number(e.target.value))}
                        disabled={settingsLoading}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Amount of money to use per trade
                      </Typography>
                    </Box>

                    <Box sx={{ mb: 3 }}>
                      <Typography variant="body2" gutterBottom>
                        Trading Account Type
                      </Typography>
                      <RadioGroup row>
                        <FormControlLabel
                          value="cash"
                          control={<Radio checked={tradingAccount === 'cash'} onChange={(e) => setTradingAccount(e.target.value)} />}
                          label="Cash"
                        />
                        <FormControlLabel
                          value="margin"
                          control={<Radio checked={tradingAccount === 'margin'} onChange={(e) => setTradingAccount(e.target.value)} />}
                          label="Margin"
                        />
                      </RadioGroup>
                    </Box>

                    <Button
                      variant="contained"
                      onClick={handleUpdateSettings}
                      disabled={settingsLoading}
                      sx={{
                        background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                        '&:hover': {
                          background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                        }
                      }}
                    >
                      {settingsLoading ? 'Updating...' : 'Update Settings'}
                    </Button>
                  </>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Warning sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      Trading settings will be available once your account is approved
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        </Grid>
      )}

      {/* Connect Account Dialog */}
      <Dialog
        open={showConnectForm}
        onClose={() => setShowConnectForm(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Connect Moomoo Account</DialogTitle>
        <form onSubmit={handleConnectSubmit}>
          <DialogContent>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Your account connection request will be reviewed by an administrator.
              You'll be notified once it's approved or rejected.
            </Typography>

            <TextField
              fullWidth
              label="Account ID"
              value={formData.accountId}
              onChange={(e) => setFormData({ ...formData, accountId: e.target.value })}
              error={!!formErrors.accountId}
              helperText={formErrors.accountId}
              margin="normal"
              required
            />

            <TextField
              fullWidth
              label="Email (Optional if phone provided)"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              error={!!formErrors.email}
              helperText={formErrors.email}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Phone Number (Optional if email provided)"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              error={!!formErrors.password}
              helperText={formErrors.password}
              margin="normal"
              required
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                ),
              }}
            />

            <TextField
              fullWidth
              label="Trading Password"
              type={showTradingPassword ? 'text' : 'password'}
              value={formData.tradingPassword}
              onChange={(e) => setFormData({ ...formData, tradingPassword: e.target.value })}
              error={!!formErrors.tradingPassword}
              helperText={formErrors.tradingPassword}
              margin="normal"
              required
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowTradingPassword(!showTradingPassword)}
                    edge="end"
                  >
                    {showTradingPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                ),
              }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowConnectForm(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              sx={{
                background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                }
              }}
            >
              {loading ? 'Connecting...' : 'Connect Account'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Container>
  );
} 