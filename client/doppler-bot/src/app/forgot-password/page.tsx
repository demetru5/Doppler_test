'use client';

import { useState } from 'react';
import { 
  Container, 
  Typography, 
  Button, 
  Box,
  TextField,
  InputAdornment,
  Alert,
  Link as MuiLink,
  Paper,
} from '@mui/material';
import { 
  Email,
  ArrowBack,
} from '@mui/icons-material';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const router = useRouter();

  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(event.target.value);
    setError('');
  };

  const validateEmail = () => {
    if (!email) {
      setError('Email is required');
      return false;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('Please enter a valid email address');
      return false;
    }
    return true;
  };

  const { forgotPassword } = useAuth();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateEmail()) {
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const success = await forgotPassword(email);
      
      if (success) {
        setIsSubmitted(true);
      } else {
        setError('Failed to send reset email. Please try again.');
      }
    } catch (error) {
      setError('Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
            <Image
              src="/logo.png"
              alt="Doppler Bot Logo"
              width={200}
              height={50}
              priority
              style={{ 
                filter: 'drop-shadow(0 4px 8px rgba(0, 242, 195, 0.3))',
                maxWidth: '100%',
                height: 'auto'
              }}
            />
          </Box>
        </Box>

        <Paper elevation={3} sx={{ p: 4, borderRadius: 2, textAlign: 'center' }}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h4" component="h1" gutterBottom>
              Check Your Email
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              We've sent a password reset link to:
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 3 }}>
              {email}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
              Click the link in the email to reset your password. The link will expire in 1 hour.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Didn't receive the email? Check your spam folder or try again.
            </Typography>
            <Button
              variant="outlined"
              onClick={() => {
                setIsSubmitted(false);
                setEmail('');
              }}
              sx={{ mr: 2 }}
            >
              Try Again
            </Button>
          </Box>

          <Box>
            <Link href="/login" passHref>
              <MuiLink component="span" sx={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center' }}>
                <ArrowBack sx={{ mr: 1, fontSize: 16 }} />
                Back to Sign In
              </MuiLink>
            </Link>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
          <Image
            src="/logo.png"
            alt="Doppler Bot Logo"
            width={200}
            height={50}
            priority
            style={{ 
              filter: 'drop-shadow(0 4px 8px rgba(0, 242, 195, 0.3))',
              maxWidth: '100%',
              height: 'auto'
            }}
          />
        </Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Forgot Password
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Enter your email address and we'll send you a link to reset your password
        </Typography>
      </Box>

      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={email}
            onChange={handleEmailChange}
            error={!!error}
            margin="normal"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Email color="action" />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 3 }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={isLoading}
            sx={{ 
              py: 1.5,
              mb: 3,
              background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
              }
            }}
          >
            {isLoading ? 'Sending...' : 'Send Reset Link'}
          </Button>
        </Box>

        <Box sx={{ textAlign: 'center' }}>
          <Link href="/login" passHref>
            <MuiLink component="span" sx={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center' }}>
              <ArrowBack sx={{ mr: 1, fontSize: 16 }} />
              Back to Sign In
            </MuiLink>
          </Link>
        </Box>
      </Paper>
    </Container>
  );
} 