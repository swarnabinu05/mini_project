import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Invoice APIs
export const uploadInvoice = async (invoiceFile, certificateFile, country) => {
  const formData = new FormData();
  formData.append('file', invoiceFile);
  formData.append('country', country);
  if (certificateFile) {
    formData.append('quality_certificate', certificateFile);
  }
  
  const response = await api.post('/invoice/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getAllInvoices = async () => {
  const response = await api.get('/invoices/');
  return response.data;
};

export const exportInvoices = async () => {
  const response = await api.get('/invoices/export', { responseType: 'blob' });
  return response.data;
};

export const deleteAllInvoices = async () => {
  const response = await api.delete('/invoices/');
  return response.data;
};

// Signed Invoices
export const getSignedInvoices = async () => {
  const response = await api.get('/invoices/signed');
  return response.data;
};

export const downloadSignedInvoice = (filename) => {
  return `${API_BASE_URL}/invoices/signed/${filename}`;
};

// Analytics APIs
export const getAnalyticsDashboard = async () => {
  const response = await api.get('/analytics/');
  return response.data;
};

export const getAnalyticsSummary = async () => {
  const response = await api.get('/analytics/summary');
  return response.data;
};

export const getAnalyticsByCountry = async () => {
  const response = await api.get('/analytics/by-country');
  return response.data;
};

export const getAnalyticsByCategory = async () => {
  const response = await api.get('/analytics/by-category');
  return response.data;
};

export const getAnalyticsByMonth = async (months = 12) => {
  const response = await api.get(`/analytics/by-month?months=${months}`);
  return response.data;
};

export const getTaxByProduct = async () => {
  const response = await api.get('/analytics/tax-by-product');
  return response.data;
};

export const getTopVendors = async (limit = 10) => {
  const response = await api.get(`/analytics/top-vendors?limit=${limit}`);
  return response.data;
};

export const getTopImporters = async (limit = 10) => {
  const response = await api.get(`/analytics/top-importers?limit=${limit}`);
  return response.data;
};

// Approval Workflow APIs
export const getApprovalsDashboard = async () => {
  const response = await api.get('/approvals/');
  return response.data;
};

export const getPendingApprovals = async (level = null) => {
  const url = level ? `/approvals/pending?level=${level}` : '/approvals/pending';
  const response = await api.get(url);
  return response.data;
};

export const getApprovalStatus = async (invoiceId) => {
  const response = await api.get(`/approvals/${invoiceId}`);
  return response.data;
};

export const approveInvoice = async (approvalId, approverName, comments = '') => {
  const formData = new FormData();
  formData.append('approver_name', approverName);
  if (comments) formData.append('comments', comments);
  
  const response = await api.post(`/approvals/${approvalId}/approve`, formData);
  return response.data;
};

export const rejectInvoice = async (approvalId, rejectorName, reason) => {
  const formData = new FormData();
  formData.append('rejector_name', rejectorName);
  formData.append('reason', reason);
  
  const response = await api.post(`/approvals/${approvalId}/reject`, formData);
  return response.data;
};

// Vendor & Fraud APIs
export const getVendors = async () => {
  const response = await api.get('/vendors/');
  return response.data;
};

export const getVendorDetails = async (vendorName) => {
  const response = await api.get(`/vendors/${encodeURIComponent(vendorName)}`);
  return response.data;
};

export const getFraudStats = async () => {
  const response = await api.get('/fraud-stats/');
  return response.data;
};

// Product Classification
export const classifyProduct = async (description, hsCode = null) => {
  const url = hsCode 
    ? `/classify/${encodeURIComponent(description)}?hs_code=${hsCode}`
    : `/classify/${encodeURIComponent(description)}`;
  const response = await api.get(url);
  return response.data;
};

export default api;
