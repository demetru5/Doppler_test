'use client';

import { 
  Container, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  Box,
  Paper,
  AppBar,
  Toolbar,
  Avatar,
  Menu,
  MenuItem,
  IconButton,
} from '@mui/material';
import { AccountCircle, Login, Logout, Dashboard, Security, KeyRounded } from '@mui/icons-material';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import { useState } from 'react';

export default function Home() {
  const { user, logout, isAdmin } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleClose();
  };
  return (
    <>
      <AppBar position="static" sx={{ background: 'transparent', boxShadow: 'none' }}>
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Image
              src="/logo.png"
              alt="Doppler Bot Logo"
              width={120}
              height={30}
              style={{ 
                filter: 'drop-shadow(0 2px 4px rgba(0, 242, 195, 0.3))',
                maxWidth: '100%',
                height: 'auto'
              }}
            />
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {user ? (
              <>
                <Typography variant="body2" color="text.secondary">
                  Welcome, {user.firstName}!
                </Typography>
                <IconButton
                  onClick={handleMenu}
                  sx={{ color: 'rgba(0, 242, 195, 0.8)' }}
                >
                  <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(0, 242, 195, 0.2)' }}>
                    {user.firstName.charAt(0)}
                  </Avatar>
                </IconButton>
                <Menu
                  anchorEl={anchorEl}
                  open={Boolean(anchorEl)}
                  onClose={handleClose}
                  anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'right',
                  }}
                  transformOrigin={{
                    vertical: 'top',
                    horizontal: 'right',
                  }}
                >
                  <MenuItem onClick={handleClose} component={Link} href="/dashboard">
                    <Dashboard sx={{ mr: 1 }} />
                    Dashboard
                  </MenuItem>
                  {isAdmin && (
                    <MenuItem onClick={handleClose} component={Link} href="/admin">
                      <Security sx={{ mr: 1 }} />
                      Admin Dashboard
                    </MenuItem>
                  )}
                  <MenuItem onClick={handleClose} component={Link} href="/change-password">
                    <KeyRounded sx={{ mr: 1 }} />
                    Change Password
                  </MenuItem>
                  <MenuItem onClick={handleLogout}>
                    <Logout sx={{ mr: 1 }} />
                    Sign Out
                  </MenuItem>
                </Menu>
              </>
            ) : (
              <>
                <Link href="/login" passHref>
                  <Button 
                    variant="outlined" 
                    startIcon={<Login />}
                    sx={{ 
                      borderColor: 'rgba(0, 242, 195, 0.5)',
                      color: 'rgba(0, 242, 195, 0.8)',
                      '&:hover': {
                        borderColor: 'rgba(0, 242, 195, 0.8)',
                        backgroundColor: 'rgba(0, 242, 195, 0.1)',
                      }
                    }}
                  >
                    Sign In
                  </Button>
                </Link>
                <Link href="/register" passHref>
                  <Button 
                    variant="contained"
                    startIcon={<AccountCircle />}
                    sx={{ 
                      background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                      '&:hover': {
                        background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                      }
                    }}
                  >
                    Sign Up
                  </Button>
                </Link>
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 6 }}>
          <Typography variant="h4" color="text.secondary" gutterBottom>
            Real-time Market Monitoring & Trading
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Advanced trading bot with intelligent market analysis and automated execution
          </Typography>
          {user ? (
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link href="/dashboard" passHref>
                <Button 
                  variant="contained" 
                  size="large"
                  startIcon={<Dashboard />}
                  sx={{ 
                    background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                    '&:hover': {
                      background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                    }
                  }}
                >
                  Go to Dashboard
                </Button>
              </Link>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link href="/login" passHref>
                <Button 
                  variant="contained" 
                  size="large"
                  startIcon={<Login />}
                  sx={{ 
                    background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                    '&:hover': {
                      background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                    }
                  }}
                >
                  Get Started
                </Button>
              </Link>
              <Link href="/register" passHref>
                <Button 
                  variant="outlined" 
                  size="large"
                  startIcon={<AccountCircle />}
                  sx={{ 
                    borderColor: 'rgba(0, 242, 195, 0.5)',
                    color: 'rgba(0, 242, 195, 0.8)',
                    '&:hover': {
                      borderColor: 'rgba(0, 242, 195, 0.8)',
                      backgroundColor: 'rgba(0, 242, 195, 0.1)',
                    }
                  }}
                >
                  Create Account
                </Button>
              </Link>
            </Box>
          )}
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 4, mb: 6 }}>
          <Card sx={{ p: 1 }}>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Momentum Trading
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Real-time scanning of market movements and identifying potential opportunities
              </Typography>
              <Link href="/momentum-trading">
                <Button variant="contained" color="primary">
                  Open Momentum Scanner
                </Button>
              </Link>
            </CardContent>
          </Card>
          
          <Card sx={{ p: 1 }}>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Dip Trading
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Real-time scanning of market movements and identifying potential opportunities
              </Typography>
              <Link href="/dip-trading">
                <Button variant="contained" color="primary">
                  Open Dip Scanner
                </Button>
              </Link>
            </CardContent>
          </Card>
        </Box>
      </Container>
    </>
  );
}
