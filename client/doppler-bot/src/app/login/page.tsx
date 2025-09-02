'use client';

import { useState } from 'react';
import { 
  Container, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Alert,
  Link as MuiLink,
  Divider,
  Paper,
} from '@mui/material';
import { 
  Visibility, 
  VisibilityOff, 
  Email, 
  Lock,
  Google,
  GitHub,
} from '@mui/icons-material';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isLoading, setIsLoading] = useState(false);
  const [loginError, setLoginError] = useState('');
  const router = useRouter();

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
    setLoginError('');
  };

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const { login } = useAuth();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setLoginError('');

    try {
      const success = await login(formData.email, formData.password);
      
      if (success) {
        // Redirect to home page after successful login
        router.push('/');
      } else {
        setLoginError('Invalid email or password. Please try again.');
      }
    } catch (error) {
      setLoginError('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialLogin = (provider: string) => {
    // TODO: Implement social login logic
    console.log(`Logging in with ${provider}`);
  };

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
          Welcome Back
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Sign in to access your trading dashboard
        </Typography>
      </Box>

      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        {loginError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {loginError}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={formData.email}
            onChange={handleInputChange('email')}
            error={!!errors.email}
            helperText={errors.email}
            margin="normal"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Email color="action" />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />

          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={formData.password}
            onChange={handleInputChange('password')}
            error={!!errors.password}
            helperText={errors.password}
            margin="normal"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Lock color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
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
              mb: 2,
              background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
              }
            }}
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </Button>
        </Box>

        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="body2" color="text.secondary">
            Don't have an account?{' '}
            <Link href="/register" passHref>
              <MuiLink component="span" sx={{ cursor: 'pointer' }}>
                Sign up here
              </MuiLink>
            </Link>
          </Typography>
        </Box>

        <Divider sx={{ my: 3 }}>
          <Typography variant="body2" color="text.secondary">
            OR
          </Typography>
        </Divider>

        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<Google />}
            onClick={() => handleSocialLogin('Google')}
            sx={{ py: 1.5 }}
          >
            Google
          </Button>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<GitHub />}
            onClick={() => handleSocialLogin('GitHub')}
            sx={{ py: 1.5 }}
          >
            GitHub
          </Button>
        </Box>

        <Box sx={{ textAlign: 'center' }}>
          <Link href="/forgot-password" passHref>
            <MuiLink component="span" variant="body2" sx={{ cursor: 'pointer' }}>
              Forgot your password?
            </MuiLink>
          </Link>
        </Box>
      </Paper>
    </Container>
  );
} 