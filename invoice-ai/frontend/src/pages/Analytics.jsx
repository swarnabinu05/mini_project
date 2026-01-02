import React, { useState, useEffect } from 'react';
import { BarChart3, PieChart, TrendingUp, DollarSign, RefreshCw } from 'lucide-react';
import { getAnalyticsDashboard } from '../services/api';

function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await getAnalyticsDashboard();
      setData(response);
    } catch (err) {
      setError('Failed to load analytics data');
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

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  const summary = data?.summary?.summary || {};
  const charts = data?.charts || {};

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-500 mt-1">Visual insights into your invoice data</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Invoices</p>
              <p className="text-2xl font-bold">{summary.total_invoices || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-100 rounded-lg">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Amount</p>
              <p className="text-2xl font-bold">${(summary.total_amount_processed || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Tax Collected</p>
              <p className="text-2xl font-bold">${(summary.total_tax_collected || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <PieChart className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Countries</p>
              <p className="text-2xl font-bold">{summary.unique_countries || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* By Country */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            Invoices by Country
          </h3>
          {charts.by_country?.data?.length > 0 ? (
            <div className="space-y-3">
              {charts.by_country.data.map((item, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-24 text-sm font-medium text-gray-600 capitalize">
                    {item.country}
                  </div>
                  <div className="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                    <div
                      className="bg-blue-500 h-full rounded-full flex items-center justify-end pr-2"
                      style={{
                        width: `${Math.min(100, (item.total_amount / (charts.by_country.data[0]?.total_amount || 1)) * 100)}%`
                      }}
                    >
                      <span className="text-xs text-white font-medium">
                        ${item.total_amount.toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="w-16 text-sm text-gray-500 text-right">
                    {item.invoice_count} inv
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No data available</p>
          )}
        </div>

        {/* By Category */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <PieChart className="w-5 h-5 text-purple-500" />
            Invoices by Product Category
          </h3>
          {charts.by_category?.data?.length > 0 ? (
            <div className="space-y-3">
              {charts.by_category.data.map((item, index) => {
                const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-yellow-500', 'bg-red-500', 'bg-pink-500'];
                return (
                  <div key={index} className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${colors[index % colors.length]}`}></div>
                    <div className="flex-1 text-sm font-medium text-gray-600 capitalize">
                      {item.category?.replace(/_/g, ' ')}
                    </div>
                    <div className="text-sm text-gray-500">
                      {item.item_count} items
                    </div>
                    <div className="text-sm font-semibold">
                      ${item.total_amount?.toLocaleString()}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No data available</p>
          )}
        </div>

        {/* By Month */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-500" />
            Invoices by Month
          </h3>
          {charts.by_month?.data?.length > 0 ? (
            <div className="space-y-3">
              {charts.by_month.data.slice(-6).map((item, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-20 text-sm font-medium text-gray-600">
                    {item.month}
                  </div>
                  <div className="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                    <div
                      className="bg-green-500 h-full rounded-full flex items-center justify-end pr-2"
                      style={{
                        width: `${Math.min(100, (item.total_amount / (Math.max(...charts.by_month.data.map(d => d.total_amount)) || 1)) * 100)}%`
                      }}
                    >
                      <span className="text-xs text-white font-medium">
                        ${item.total_amount.toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="w-12 text-sm text-gray-500 text-right">
                    {item.invoice_count}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No data available</p>
          )}
        </div>

        {/* Tax by Product */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-yellow-500" />
            Tax Collected by Product
          </h3>
          {charts.tax_by_product?.data?.length > 0 ? (
            <div className="space-y-3">
              {charts.tax_by_product.data.slice(0, 6).map((item, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <span className="text-sm font-medium capitalize">
                      {item.category?.replace(/_/g, ' ')}
                    </span>
                    {item.hs_code && (
                      <span className="text-xs text-gray-400 ml-2">
                        HS: {item.hs_code}
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold text-green-600">
                      ${item.total_tax_collected?.toLocaleString()}
                    </span>
                    <span className="text-xs text-gray-400 ml-2">
                      ({item.avg_tax_rate}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No data available</p>
          )}
        </div>
      </div>

      {/* Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Vendors */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Top Vendors</h3>
          {charts.top_vendors?.data?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Vendor</th>
                    <th className="text-right py-2">Invoices</th>
                    <th className="text-right py-2">Amount</th>
                    <th className="text-right py-2">Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {charts.top_vendors.data.map((vendor, index) => (
                    <tr key={index} className="border-b">
                      <td className="py-2 font-medium">{vendor.vendor_name}</td>
                      <td className="py-2 text-right">{vendor.total_invoices}</td>
                      <td className="py-2 text-right">${vendor.total_amount?.toLocaleString()}</td>
                      <td className="py-2 text-right">
                        <span className={`px-2 py-1 rounded text-xs ${
                          vendor.risk_score >= 70 ? 'bg-red-100 text-red-800' :
                          vendor.risk_score >= 40 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {vendor.risk_score}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No vendors tracked yet</p>
          )}
        </div>

        {/* Top Importers */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">Top Importers</h3>
          {charts.top_importers?.data?.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Importer</th>
                    <th className="text-right py-2">Invoices</th>
                    <th className="text-right py-2">Total Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {charts.top_importers.data.map((importer, index) => (
                    <tr key={index} className="border-b">
                      <td className="py-2 font-medium">{importer.importer_name}</td>
                      <td className="py-2 text-right">{importer.invoice_count}</td>
                      <td className="py-2 text-right">${importer.total_amount?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No importers tracked yet</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Analytics;
