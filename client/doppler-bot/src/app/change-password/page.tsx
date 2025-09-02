'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import {
  Container,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  Box,
  Divider,
} from '@mui/material';

export default function ChangePassword() {
  const { changePassword } = useAuth();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    const result = await changePassword(oldPassword, newPassword);
    setLoading(false);
    if (result) {
      setSuccess('Password changed successfully');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } else {
      setError('Failed to change password');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Change Password
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Update your account password below.
        </Typography>
      </Box>
      <Card>
        <CardContent>
          <form onSubmit={handleSubmit}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
                {success}
              </Alert>
            )}
            <TextField
              label="Current Password"
              type="password"
              value={oldPassword}
              onChange={e => setOldPassword(e.target.value)}
              fullWidth
              required
              margin="normal"
            />
            <TextField
              label="New Password"
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              fullWidth
              required
              margin="normal"
              helperText="Password must be at least 8 characters"
            />
            <TextField
              label="Confirm New Password"
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              fullWidth
              required
              margin="normal"
            />
            <Divider sx={{ my: 2 }} />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={loading}
              sx={{
                background: 'linear-gradient(45deg, #00f2c3 30%, #0098f7 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #00d4a8 30%, #0080d4 90%)',
                }
              }}
            >
              {loading ? 'Changing...' : 'Change Password'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </Container>
  );
} 