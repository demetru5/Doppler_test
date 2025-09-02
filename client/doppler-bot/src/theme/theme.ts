import { createTheme } from '@mui/material/styles';

// Create a dark theme instance
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00f2c3',
      light: '#4df5d1',
      dark: '#00c9a3',
    },
    secondary: {
      main: '#f48fb1',
      light: '#f8bbd9',
      dark: '#ec407a',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b3b3b3',
    },
    divider: '#333333',
    action: {
      hover: 'rgba(255, 255, 255, 0.08)',
      selected: 'rgba(255, 255, 255, 0.16)',
    },
  },
  typography: {
    fontFamily: [
      'var(--font-geist-sans)',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
      color: '#ffffff',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      color: '#ffffff',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      color: '#ffffff',
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      color: '#ffffff',
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      color: '#ffffff',
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      color: '#ffffff',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 500,
        },
        contained: {
          boxShadow: '0 2px 8px rgba(0, 242, 195, 0.3)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0, 242, 195, 0.4)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
          border: '1px solid #333333',
          backgroundColor: '#1a1a1a',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: '#1a1a1a',
          border: '1px solid #333333',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1a1a1a',
          borderBottom: '1px solid #333333',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          backgroundColor: '#2a2a2a',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #333333',
        },
        head: {
          backgroundColor: '#2a2a2a',
          color: '#ffffff',
          fontWeight: 600,
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.04)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 500,
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        root: {
          '& .MuiSwitch-switchBase.Mui-checked': {
            color: '#00f2c3',
          },
          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
            backgroundColor: '#00f2c3',
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          border: '1px solid',
        },
      },
    },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0 2px 4px rgba(0, 0, 0, 0.3)',
    '0 4px 8px rgba(0, 0, 0, 0.3)',
    '0 6px 12px rgba(0, 0, 0, 0.3)',
    '0 8px 16px rgba(0, 0, 0, 0.3)',
    '0 10px 20px rgba(0, 0, 0, 0.3)',
    '0 12px 24px rgba(0, 0, 0, 0.3)',
    '0 14px 28px rgba(0, 0, 0, 0.3)',
    '0 16px 32px rgba(0, 0, 0, 0.3)',
    '0 18px 36px rgba(0, 0, 0, 0.3)',
    '0 20px 40px rgba(0, 0, 0, 0.3)',
    '0 22px 44px rgba(0, 0, 0, 0.3)',
    '0 24px 48px rgba(0, 0, 0, 0.3)',
    '0 26px 52px rgba(0, 0, 0, 0.3)',
    '0 28px 56px rgba(0, 0, 0, 0.3)',
    '0 30px 60px rgba(0, 0, 0, 0.3)',
    '0 32px 64px rgba(0, 0, 0, 0.3)',
    '0 34px 68px rgba(0, 0, 0, 0.3)',
    '0 36px 72px rgba(0, 0, 0, 0.3)',
    '0 38px 76px rgba(0, 0, 0, 0.3)',
    '0 40px 80px rgba(0, 0, 0, 0.3)',
    '0 42px 84px rgba(0, 0, 0, 0.3)',
    '0 44px 88px rgba(0, 0, 0, 0.3)',
    '0 46px 92px rgba(0, 0, 0, 0.3)',
    '0 48px 96px rgba(0, 0, 0, 0.3)',
  ],
});

export default theme; 