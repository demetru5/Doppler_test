'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { 
  Container, 
  Typography, 
  Box, 
  Alert,
  CircularProgress 
} from '@mui/material';
import { Security } from '@mui/icons-material';

interface AdminRouteProps {
  children: React.ReactNode;
}

export default function AdminRoute({ children }: AdminRouteProps) {
  const { user, isLoading, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.push('/login');
      } else if (!isAdmin) {
        router.push('/dashboard');
      }
    }
  }, [user, isLoading, isAdmin, router]);

  if (isLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (!user) {
    return null; // Will redirect to login
  }

  if (!isAdmin) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" flexDirection="column" alignItems="center" minHeight="400px">
          <Security sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Access Denied
          </Typography>
          <Alert severity="error" sx={{ maxWidth: 500, mb: 2 }}>
            You don't have permission to access this page. Admin privileges are required.
          </Alert>
          <Typography variant="body1" color="text.secondary">
            Redirecting to dashboard...
          </Typography>
        </Box>
      </Container>
    );
  }

  return <>{children}</>;
} 