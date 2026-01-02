// Main dashboard page - placeholder

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Upload, 
  FileText, 
  DollarSign, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  TrendingUp,
  Users
} from 'lucide-react';
import { getAnalyticsSummary, getApprovalsDashboard } from '../services/api';

function StatCard({ title, value, icon: Icon, color, link }) {
  const content = (
    <div className={`bg-white rounded-xl shadow-sm p-6 border-l-4 ${color}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-full bg-opacity-10 ${color.replace('border-', 'bg-')}`}>
          <Icon className={`w-6 h-6 ${color.replace('border-', 'text-')}`} />
        </div>
      </div>
    </div>
  );
  
  if (link) {
    return <Link to={link}>{content}</Link>;
  }
  return content;
}

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [approvals, setApprovals] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [summaryData, approvalsData] = await Promise.all([
          getAnalyticsSummary(),
          getApprovalsDashboard()
        ]);
        setSummary(summaryData.summary);
        setApprovals(approvalsData);
      } catch (err) {
        setError('Failed to load dashboard data. Make sure the backend is running.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-red-500" />
          <div>
            <h3 className="font-semibold text-red-800">Connection Error</h3>
            <p className="text-red-600">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of your invoice processing system</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Invoices"
          value={summary?.total_invoices || 0}
          icon={FileText}
          color="border-blue-500"
          link="/analytics"
        />
        <StatCard
          title="Amount Processed"
          value={`$${(summary?.total_amount_processed || 0).toLocaleString()}`}
          icon={DollarSign}
          color="border-green-500"
          link="/analytics"
        />
        <StatCard
          title="Pending Approvals"
          value={approvals?.summary?.total_pending || 0}
          icon={Clock}
          color="border-yellow-500"
          link="/approvals"
        />
        <StatCard
          title="High Risk Invoices"
          value={summary?.high_risk_invoices || 0}
          icon={AlertTriangle}
          color="border-red-500"
          link="/vendors"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Link
            to="/upload"
            className="flex flex-col items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <Upload className="w-8 h-8 text-blue-600 mb-2" />
            <span className="text-sm font-medium text-blue-900">Upload Invoice</span>
          </Link>
          <Link
            to="/approvals"
            className="flex flex-col items-center p-4 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors"
          >
            <CheckCircle className="w-8 h-8 text-yellow-600 mb-2" />
            <span className="text-sm font-medium text-yellow-900">Review Approvals</span>
          </Link>
          <Link
            to="/analytics"
            className="flex flex-col items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
          >
            <TrendingUp className="w-8 h-8 text-green-600 mb-2" />
            <span className="text-sm font-medium text-green-900">View Analytics</span>
          </Link>
          <Link
            to="/signed"
            className="flex flex-col items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
          >
            <FileText className="w-8 h-8 text-purple-600 mb-2" />
            <span className="text-sm font-medium text-purple-900">Download Signed</span>
          </Link>
        </div>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tax Collected</h3>
          <p className="text-3xl font-bold text-green-600">
            ${(summary?.total_tax_collected || 0).toLocaleString()}
          </p>
          <p className="text-sm text-gray-500 mt-1">Total tax from all invoices</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">This Month</h3>
          <p className="text-3xl font-bold text-blue-600">
            {summary?.invoices_this_month || 0}
          </p>
          <p className="text-sm text-gray-500 mt-1">Invoices processed this month</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Vendors Tracked</h3>
          <p className="text-3xl font-bold text-purple-600">
            {summary?.unique_vendors || 0}
          </p>
          <p className="text-sm text-gray-500 mt-1">Unique vendors in system</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
