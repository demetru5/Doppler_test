interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  status?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    // Fix: Add fallback and proper URL construction
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
    
    // Ensure the base URL doesn't end with a slash
    if (this.baseUrl && this.baseUrl.endsWith('/')) {
      this.baseUrl = this.baseUrl.slice(0, -1);
    }
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('doppler_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  // Fix: Add better error handling
  private async handleResponse<T>(response: Response): Promise<ApiResponse<T>> {
    try {
      const data = await response.json();
      
      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
          status: response.status,
        };
      }

      return {
        success: true,
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        success: false,
        error: 'Failed to parse response',
        status: response.status,
      };
    }
  }

  async get<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      return this.handleResponse<T>(response);
    } catch (error) {
      console.error('API GET request failed:', error);
      return {
        success: false,
        error: 'Network error occurred',
      };
    }
  }

  async post<T = any>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('API POST request failed:', error);
      return {
        success: false,
        error: 'Network error occurred',
      };
    }
  }

  async put<T = any>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('API PUT request failed:', error);
      return {
        success: false,
        error: 'Network error occurred',
      };
    }
  }

  async delete<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders(),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('API DELETE request failed:', error);
      return {
        success: false,
        error: 'Network error occurred',
      };
    }
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Helper functions for common API calls
export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post('/auth/login', { email, password }),

  register: (userData: {
    firstName: string;
    lastName: string;
    email: string;
    password: string;
  }) => apiClient.post('/auth/register', userData),

  verify: () => apiClient.get('/auth/verify'),

  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }),

  resetPassword: (token: string, newPassword: string) =>
    apiClient.post('/auth/reset-password', { token, newPassword }),

  getProfile: () => apiClient.get('/auth/profile'),

  updateProfile: (profileData: { firstName?: string; lastName?: string }) =>
    apiClient.put('/auth/profile', profileData),

  logout: () => apiClient.post('/auth/logout', {}),

  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.post('/auth/change-password', { oldPassword, newPassword }),
};

export const tradingApi = {
  getMarketContext: () => apiClient.get('/get_market_context'),
  getStockData: () => apiClient.get('/get_stock_data'),
  getCandles: (ticker: string) => apiClient.get(`/get_candles?ticker=${ticker}`),
  getPositions: () => apiClient.get('/get_positions'),
  getBuyFeaturesStatus: () => apiClient.get('/get_buy_features_status'),
  toggleBuyFeatures: (enabled: boolean) =>
    apiClient.post('/toggle_buy_features', { enabled }),
};

export const moomooAccountApi = {
  connectAccount: (accountData: {
    accountId: string;
    email?: string;
    phone?: string;
    password: string;
    tradingPassword: string;
  }) => apiClient.post('/moomoo/connect', accountData),

  getAccount: () => apiClient.get('/moomoo/account'),

  updateSettings: (settings: {
    tradingEnabled?: boolean;
    tradingAmount?: number;
    tradingAccount?: string;
  }) => apiClient.put('/moomoo/settings', settings),

  deleteAccount: () => apiClient.delete('/moomoo/account'),
};

export const adminApi = {
  // Existing functions that match backend endpoints
  getPendingRequests: () => apiClient.get('/admin/moomoo/pending'),
  assignOpenD: (accountId: string, host: string, port: string) => apiClient.post(`/admin/moomoo/assign/${accountId}`, { host, port }),
  approveAccount: (accountId: string) => apiClient.post(`/admin/moomoo/approve/${accountId}`, {}),
  rejectAccount: (accountId: string, reason: string) =>
    apiClient.post(`/admin/moomoo/reject/${accountId}`, { reason }),
  getAllAccounts: () => apiClient.get('/admin/moomoo/accounts'),
  getDailyOverview: () => apiClient.get('/admin/daily-overview'),
  updateAccountTradingSettings: (accountId: string, settings: { trading_enabled?: boolean; trading_amount?: number }) =>
    apiClient.put(`/admin/moomoo/accounts/${accountId}/trading-settings`, settings),
  
  // Additional functions that match actual backend endpoints
  getSystemStatus: () => apiClient.get('/admin/system/status'),
  
  switchAccountType: (accountId: string, accountType: string) =>
    apiClient.put(`/admin/moomoo/accounts/${accountId}/account-type`, { account_type: accountType }),
};