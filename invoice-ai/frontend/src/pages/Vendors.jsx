import React, { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, TrendingUp, RefreshCw, Search } from 'lucide-react';
import { getVendors, getFraudStats } from '../services/api';

function Vendors() {
  const [vendors, setVendors] = useState(null);
  const [fraudStats, setFraudStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [vendorsData, fraudData] = await Promise.all([
        getVendors(),
        getFraudStats()
      ]);
      setVendors(vendorsData);
      setFraudStats(fraudData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const vendorList = vendors?.vendors || [];
  const filteredVendors = vendorList.filter(v => 
    v.vendor_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const summary = fraudStats?.summary || {};

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Vendors & Fraud Detection</h1>
          <p className="text-gray-500 mt-1">Monitor vendor risk scores and fraud detection</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Fraud Detection Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Invoices</p>
              <p className="text-2xl font-bold">{summary.total_invoices_processed || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Vendors Tracked</p>
              <p className="text-2xl font-bold">{summary.total_vendors_tracked || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-red-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">High Risk Vendors</p>
              <p className="text-2xl font-bold">{summary.high_risk_vendors || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Price Records</p>
              <p className="text-2xl font-bold">{summary.price_history_records || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Fraud Detection Features */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Fraud Detection Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-800 mb-2">Duplicate Detection</h3>
            <p className="text-sm text-blue-600">
              {fraudStats?.fraud_detection_features?.duplicate_detection || 
               'Flags invoices with same ID, amount+date, or similar patterns'}
            </p>
          </div>
          <div className="p-4 bg-yellow-50 rounded-lg">
            <h3 className="font-medium text-yellow-800 mb-2">Price Anomaly Detection</h3>
            <p className="text-sm text-yellow-600">
              {fraudStats?.fraud_detection_features?.price_anomaly_detection || 
               'Alerts when prices deviate >30% from historical average'}
            </p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <h3 className="font-medium text-purple-800 mb-2">Vendor Risk Scoring</h3>
            <p className="text-sm text-purple-600">
              {fraudStats?.fraud_detection_features?.vendor_risk_scoring || 
               'Tracks vendor reliability based on invoice success/failure rate'}
            </p>
          </div>
        </div>
      </div>

      {/* Vendor Search */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Vendor Risk Scores</h2>
          <div className="relative">
            <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search vendors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {filteredVendors.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4">Vendor Name</th>
                  <th className="text-center py-3 px-4">Total Invoices</th>
                  <th className="text-center py-3 px-4">Successful</th>
                  <th className="text-center py-3 px-4">Failed</th>
                  <th className="text-center py-3 px-4">Success Rate</th>
                  <th className="text-right py-3 px-4">Total Amount</th>
                  <th className="text-center py-3 px-4">Risk Score</th>
                  <th className="text-center py-3 px-4">Risk Level</th>
                </tr>
              </thead>
              <tbody>
                {filteredVendors.map((vendor, index) => (
                  <tr key={index} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">{vendor.vendor_name}</td>
                    <td className="py-3 px-4 text-center">{vendor.total_invoices}</td>
                    <td className="py-3 px-4 text-center text-green-600">{vendor.successful_invoices}</td>
                    <td className="py-3 px-4 text-center text-red-600">{vendor.failed_invoices}</td>
                    <td className="py-3 px-4 text-center">{vendor.success_rate}</td>
                    <td className="py-3 px-4 text-right">${vendor.total_amount_processed?.toLocaleString()}</td>
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className={`h-2 rounded-full ${
                              vendor.risk_score >= 70 ? 'bg-red-500' :
                              vendor.risk_score >= 40 ? 'bg-yellow-500' :
                              'bg-green-500'
                            }`}
                            style={{ width: `${vendor.risk_score}%` }}
                          ></div>
                        </div>
                        <span className="text-xs">{vendor.risk_score}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        vendor.risk_level === 'HIGH' ? 'bg-red-100 text-red-800' :
                        vendor.risk_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {vendor.risk_level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <Shield className="w-16 h-16 mx-auto mb-4" />
            <p>No vendors tracked yet</p>
            <p className="text-sm">Upload invoices to start tracking vendor performance</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Vendors;
