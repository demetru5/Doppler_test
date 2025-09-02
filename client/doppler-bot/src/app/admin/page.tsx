'use client';

import { 
  Container, 
  Typography, 
  Box,
  Card,
  CardContent,
  Grid,
  Button,
  Paper,
  Divider,
  Chip,
  Avatar,
} from '@mui/material';
import { 
  Security,
  TrendingUp,
  AccountBalance,
  People,
  Assessment,
  Settings,
  Dashboard as DashboardIcon,
  BarChart,
  Timeline,
  Notifications,
} from '@mui/icons-material';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import AdminRoute from '@/components/AdminRoute';

export default function AdminDashboard() {
  const { user } = useAuth();

  const adminFeatures = [
    {
      title: 'Account Management',
      description: 'Review and manage moomoo account connection requests',
      icon: <AccountBalance sx={{ fontSize: 40, color: 'primary.main' }} />,
      href: '/admin/moomoo-accounts',
      color: 'primary',
      count: 'Pending Requests'
    },
    {
      title: 'Daily Overview',
      description: 'View daily trading performance across all accounts',
      icon: <BarChart sx={{ fontSize: 40, color: 'success.main' }} />,
      href: '/admin/daily-overview',
      color: 'success',
      count: 'All Accounts'
    },
    // {
    //   title: 'Trading Analytics',
    //   description: 'Advanced analytics and performance metrics',
    //   icon: <TrendingUp sx={{ fontSize: 40, color: 'info.main' }} />,
    //   href: '/admin/analytics',
    //   color: 'info',
    //   count: 'Coming Soon'
    // },
    // {
    //   title: 'User Management',
    //   description: 'Manage user accounts and permissions',
    //   icon: <People sx={{ fontSize: 40, color: 'warning.main' }} />,
    //   href: '/admin/users',
    //   color: 'warning',
    //   count: 'Coming Soon'
    // },
    // {
    //   title: 'System Settings',
    //   description: 'Configure system-wide trading parameters',
    //   icon: <Settings sx={{ fontSize: 40, color: 'secondary.main' }} />,
    //   href: '/admin/settings',
    //   color: 'secondary',
    //   count: 'Coming Soon'
    // },
    // {
    //   title: 'Notifications',
    //   description: 'Manage system alerts and notifications',
    //   icon: <Notifications sx={{ fontSize: 40, color: 'error.main' }} />,
    //   href: '/admin/notifications',
    //   color: 'error',
    //   count: 'Coming Soon'
    // }
  ];

  return (
    <AdminRoute>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Security sx={{ fontSize: 48, color: 'primary.main', mr: 2 }} />
            <Box>
              <Typography variant="h4" component="h1" gutterBottom>
                Admin Dashboard
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Welcome back, {user?.firstName}! Manage your trading platform
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Quick Stats */}
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
                      12
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
                      3
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Pending Requests
                    </Typography>
                  </Box>
                  <People sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      $45.2K
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Total Volume
                    </Typography>
                  </Box>
                  <TrendingUp sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={3}>
            <Card sx={{ 
              background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                      +12.5%
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.8 }}>
                      Daily P&L
                    </Typography>
                  </Box>
                  <BarChart sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Admin Features Grid */}
        <Grid container spacing={3}>
          {adminFeatures.map((feature, index) => (
            <Grid size={4} key={index}>
              <Card 
                sx={{ 
                  height: '100%',
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
                  }
                }}
              >
                <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {feature.icon}
                    <Box sx={{ ml: 2 }}>
                      <Typography variant="h6" component="h3" gutterBottom>
                        {feature.title}
                      </Typography>
                      <Chip 
                        label={feature.count} 
                        color={feature.color as any}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3, flexGrow: 1 }}>
                    {feature.description}
                  </Typography>
                  
                  <Box sx={{ mt: 'auto' }}>
                    {feature.href !== '#' ? (
                      <Link href={feature.href} passHref>
                        <Button 
                          variant="contained" 
                          fullWidth
                          sx={{ 
                            background: `linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)`,
                            '&:hover': {
                              background: `linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)`,
                            }
                          }}
                        >
                          Access {feature.title}
                        </Button>
                      </Link>
                    ) : (
                      <Button 
                        variant="outlined" 
                        fullWidth
                        disabled
                        sx={{ 
                          borderColor: 'rgba(0, 242, 195, 0.5)',
                          color: 'rgba(0, 242, 195, 0.8)',
                        }}
                      >
                        Coming Soon
                      </Button>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </AdminRoute>
  );
} 