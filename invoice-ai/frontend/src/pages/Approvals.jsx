import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Clock, AlertTriangle, RefreshCw, User } from 'lucide-react';
import { getApprovalsDashboard, approveInvoice, rejectInvoice } from '../services/api';

function Approvals() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [approverName, setApproverName] = useState('');
  const [showModal, setShowModal] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [comments, setComments] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await getApprovalsDashboard();
      setData(response);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApprove = async (approvalId) => {
    if (!approverName.trim()) {
      alert('Please enter your name');
      return;
    }
    
    setActionLoading(approvalId);
    try {
      const result = await approveInvoice(approvalId, approverName, comments);
      alert(result.message || 'Approved successfully');
      setShowModal(null);
      setComments('');
      fetchData();
    } catch (err) {
      alert('Failed to approve: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (approvalId) => {
    if (!approverName.trim()) {
      alert('Please enter your name');
      return;
    }
    if (!rejectReason.trim()) {
      alert('Please enter a rejection reason');
      return;
    }
    
    setActionLoading(approvalId);
    try {
      const result = await rejectInvoice(approvalId, approverName, rejectReason);
      alert(result.message || 'Rejected successfully');
      setShowModal(null);
      setRejectReason('');
      fetchData();
    } catch (err) {
      alert('Failed to reject: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const summary = data?.summary || {};
  const pendingByLevel = data?.pending_by_level || {};
  const pendingApprovals = data?.pending_approvals || [];
  const overdueApprovals = data?.overdue_approvals || [];

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Approval Workflow</h1>
          <p className="text-gray-500 mt-1">Review and approve pending invoices</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Approver Name Input */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex items-center gap-4">
          <User className="w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Enter your name (required for approvals)"
            value={approverName}
            onChange={(e) => setApproverName(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <Clock className="w-8 h-8 text-yellow-600" />
            <div>
              <p className="text-sm text-yellow-700">Pending</p>
              <p className="text-3xl font-bold text-yellow-800">{summary.total_pending || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-green-600" />
            <div>
              <p className="text-sm text-green-700">Approved</p>
              <p className="text-3xl font-bold text-green-800">{summary.total_approved || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <XCircle className="w-8 h-8 text-red-600" />
            <div>
              <p className="text-sm text-red-700">Rejected</p>
              <p className="text-3xl font-bold text-red-800">{summary.total_rejected || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-orange-600" />
            <div>
              <p className="text-sm text-orange-700">Overdue</p>
              <p className="text-3xl font-bold text-orange-800">{summary.overdue_count || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Pending by Level */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Pending by Approval Level</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">{pendingByLevel.Manager || 0}</p>
            <p className="text-sm text-blue-800">Manager</p>
            <p className="text-xs text-gray-500">All invoices</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-2xl font-bold text-purple-600">{pendingByLevel.Finance || 0}</p>
            <p className="text-sm text-purple-800">Finance</p>
            <p className="text-xs text-gray-500">&gt; $50,000</p>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <p className="text-2xl font-bold text-red-600">{pendingByLevel.Compliance || 0}</p>
            <p className="text-sm text-red-800">Compliance</p>
            <p className="text-xs text-gray-500">&gt; $100,000 or High Risk</p>
          </div>
        </div>
      </div>

      {/* Overdue Approvals */}
      {overdueApprovals.length > 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-6 mb-8">
          <h2 className="text-lg font-semibold text-orange-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Overdue Approvals (Waiting &gt; 3 days)
          </h2>
          <div className="space-y-2">
            {overdueApprovals.map((approval) => (
              <div key={approval.id} className="flex items-center justify-between bg-white p-3 rounded-lg">
                <div>
                  <span className="font-medium">{approval.invoice_id}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    {approval.vendor_name} - ${approval.total_amount?.toLocaleString()}
                  </span>
                </div>
                <span className="text-orange-600 font-medium">
                  {approval.waiting_days} days waiting
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pending Approvals Table */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Pending Approvals</h2>
        {pendingApprovals.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4">Invoice ID</th>
                  <th className="text-left py-3 px-4">Vendor</th>
                  <th className="text-left py-3 px-4">Country</th>
                  <th className="text-right py-3 px-4">Amount</th>
                  <th className="text-center py-3 px-4">Level</th>
                  <th className="text-center py-3 px-4">Risk</th>
                  <th className="text-center py-3 px-4">Waiting</th>
                  <th className="text-center py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pendingApprovals.map((approval) => (
                  <tr key={approval.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{approval.invoice_id}</td>
                    <td className="py-3 px-4">{approval.vendor_name || '-'}</td>
                    <td className="py-3 px-4 capitalize">{approval.country || '-'}</td>
                    <td className="py-3 px-4 text-right">
                      ${approval.total_amount?.toLocaleString() || 0}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        approval.level === 3 ? 'bg-red-100 text-red-800' :
                        approval.level === 2 ? 'bg-purple-100 text-purple-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {approval.level_name}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      {approval.fraud_score !== null && (
                        <span className={`px-2 py-1 rounded text-xs ${
                          approval.fraud_score >= 70 ? 'bg-red-100 text-red-800' :
                          approval.fraud_score >= 40 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {approval.fraud_score?.toFixed(0)}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center text-gray-500">
                      {approval.waiting_days}d
                    </td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => setShowModal({ type: 'approve', approval })}
                          disabled={actionLoading === approval.id}
                          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-xs"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => setShowModal({ type: 'reject', approval })}
                          disabled={actionLoading === approval.id}
                          className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 text-xs"
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <CheckCircle className="w-16 h-16 mx-auto mb-4" />
            <p>No pending approvals</p>
          </div>
        )}
      </div>

      {/* Approval/Reject Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">
              {showModal.type === 'approve' ? 'Approve Invoice' : 'Reject Invoice'}
            </h3>
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                Invoice: <strong>{showModal.approval.invoice_id}</strong><br />
                Amount: <strong>${showModal.approval.total_amount?.toLocaleString()}</strong>
              </p>
            </div>
            
            {showModal.type === 'approve' ? (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Comments (optional)
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                  placeholder="Add any comments..."
                />
              </div>
            ) : (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rejection Reason *
                </label>
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                  placeholder="Enter reason for rejection..."
                  required
                />
              </div>
            )}
            
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowModal(null);
                  setComments('');
                  setRejectReason('');
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (showModal.type === 'approve') {
                    handleApprove(showModal.approval.id);
                  } else {
                    handleReject(showModal.approval.id);
                  }
                }}
                disabled={actionLoading}
                className={`flex-1 px-4 py-2 text-white rounded-lg ${
                  showModal.type === 'approve' 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-red-600 hover:bg-red-700'
                } disabled:opacity-50`}
              >
                {actionLoading ? 'Processing...' : showModal.type === 'approve' ? 'Approve' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Approvals;
