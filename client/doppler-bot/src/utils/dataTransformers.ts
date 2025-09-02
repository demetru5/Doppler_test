export const transformPendingRequests = (data: any) => {
  if (!data || !data.requests) return [];
  
  return data.requests.map((req: any) => ({
    ...req,
    createdAt: req.createdAt ? new Date(req.createdAt).toISOString() : '',
    tradingAccount: req.tradingAccount || 'cash',
  }));
};

export const transformAccounts = (data: any) => {
  if (!data || !data.accounts) return [];
  
  return data.accounts.map((acc: any) => ({
    ...acc,
    createdAt: acc.createdAt ? new Date(acc.createdAt).toISOString() : '',
    approvedAt: acc.approvedAt ? new Date(acc.approvedAt).toISOString() : undefined,
    rejectedAt: acc.rejectedAt ? new Date(acc.rejectedAt).toISOString() : undefined,
    tradingAccount: acc.tradingAccount || 'cash',
  }));
};
