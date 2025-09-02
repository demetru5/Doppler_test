'use client';

import {
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  Box,
  Avatar,
  Divider,
  Chip,
} from '@mui/material';
import {
  AccountCircle,
  TrendingUp,
  TrendingDown,
  Settings,
  Security,
  AccountBalance,
} from '@mui/icons-material';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Dashboard() {
  const { user, isLoading, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Image
            src="/logo.png"
            alt="Doppler Bot Logo"
            width={180}
            height={45}
            style={{
              filter: 'drop-shadow(0 2px 4px rgba(0, 242, 195, 0.3))',
              maxWidth: '100%',
              height: 'auto'
            }}
          />
        </Box>
        <Typography variant="h4" gutterBottom>
          Welcome back, {user.firstName}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's your trading dashboard overview
        </Typography>
      </Box>

      {/* User Profile Card */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar
              sx={{
                width: 64,
                height: 64,
                bgcolor: 'rgba(0, 242, 195, 0.2)',
                fontSize: '1.5rem'
              }}
            >
              {user.firstName.charAt(0)}
            </Avatar>
            <Box>
              <Typography variant="h6">
                {user.firstName} {user.lastName}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {user.email}
              </Typography>
              <Chip
                label="Active Account"
                color="success"
                size="small"
                sx={{ mt: 1 }}
              />
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Trading Features Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3, mb: 4 }}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingUp sx={{ mr: 1, color: 'success.main' }} />
              <Typography variant="h6">
                Momentum Trading
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Real-time scanning of market movements and identifying potential opportunities for momentum-based trading strategies.
            </Typography>
            <Link href="/momentum-trading" passHref>
              <Button
                variant="contained"
                fullWidth
                sx={{
                  background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                  }
                }}
              >
                Open Momentum Scanner
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TrendingDown sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6">
                Dip Trading
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Identify market dips and potential buying opportunities with advanced technical analysis and real-time alerts.
            </Typography>
            <Button
              variant="contained"
              fullWidth
              disabled
              sx={{
                background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                }
              }}
            >
              Coming Soon
            </Button>
          </CardContent>
        </Card>
      </Box>

      {/* Account Management */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Account Management
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<AccountCircle />}
              fullWidth
              sx={{
                borderColor: 'rgba(0, 242, 195, 0.5)',
                color: 'rgba(0, 242, 195, 0.8)',
                '&:hover': {
                  borderColor: 'rgba(0, 242, 195, 0.8)',
                  backgroundColor: 'rgba(0, 242, 195, 0.1)',
                }
              }}
            >
              Profile Settings
            </Button>
            <Button
              variant="outlined"
              startIcon={<Security />}
              fullWidth
              sx={{
                borderColor: 'rgba(0, 242, 195, 0.5)',
                color: 'rgba(0, 242, 195, 0.8)',
                '&:hover': {
                  borderColor: 'rgba(0, 242, 195, 0.8)',
                  backgroundColor: 'rgba(0, 242, 195, 0.1)',
                }
              }}
            >
              Security Settings
            </Button>
            <Link href="/moomoo-account" passHref>
              <Button
                variant="outlined"
                startIcon={<AccountBalance />}
                fullWidth
                sx={{
                  borderColor: 'rgba(0, 242, 195, 0.5)',
                  color: 'rgba(0, 242, 195, 0.8)',
                  '&:hover': {
                    borderColor: 'rgba(0, 242, 195, 0.8)',
                    backgroundColor: 'rgba(0, 242, 195, 0.1)',
                  }
                }}
              >
                Moomoo Account
              </Button>
            </Link>
            <Button
              variant="outlined"
              startIcon={<Settings />}
              fullWidth
              sx={{
                borderColor: 'rgba(0, 242, 195, 0.5)',
                color: 'rgba(0, 242, 195, 0.8)',
                '&:hover': {
                  borderColor: 'rgba(0, 242, 195, 0.8)',
                  backgroundColor: 'rgba(0, 242, 195, 0.1)',
                }
              }}
            >
              Trading Settings
            </Button>
          </Box>
        </CardContent>
      </Card>

      {isAdmin && (
        <Box sx={{ mt: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Security sx={{ fontSize: 40, color: 'primary.main', mr: 2 }} />
                <Typography variant="h6">Admin Panel</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={3}>
                Manage moomoo account requests and system settings
              </Typography>
              <Button
                variant="contained"
                component={Link}
                href="/admin"
                startIcon={<Security />}
                fullWidth
              >
                Access Admin Dashboard
              </Button>
            </CardContent>
          </Card>
        </Box>
      )}
    </Container>
  );
} 