import { useTheme } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';

// Custom hook for responsive breakpoints
export const useResponsive = () => {
  const theme = useTheme();
  
  return {
    isMobile: useMediaQuery(theme.breakpoints.down('sm')),
    isTablet: useMediaQuery(theme.breakpoints.between('sm', 'md')),
    isDesktop: useMediaQuery(theme.breakpoints.up('md')),
    isLargeScreen: useMediaQuery(theme.breakpoints.up('lg')),
  };
};

// Common spacing values
export const spacing = {
  xs: 1,
  sm: 2,
  md: 3,
  lg: 4,
  xl: 5,
};

// Common border radius values
export const borderRadius = {
  small: 4,
  medium: 8,
  large: 12,
  xl: 16,
};

// Common shadow values
export const shadows = {
  light: '0 2px 4px rgba(0,0,0,0.1)',
  medium: '0 4px 8px rgba(0,0,0,0.15)',
  heavy: '0 8px 16px rgba(0,0,0,0.2)',
}; 