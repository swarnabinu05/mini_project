import React, { useState, useEffect } from 'react';
import { FileText, Download, RefreshCw, Trash2, ExternalLink } from 'lucide-react';
import { getSignedInvoices, downloadSignedInvoice, getAllInvoices, exportInvoices, deleteAllInvoices } from '../services/api';

function SignedInvoices() {
  const [signedFiles, setSignedFiles] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [signedData, invoicesData] = await Promise.all([
        getSignedInvoices(),
        getAllInvoices()
      ]);
      setSignedFiles(signedData.files || []);
      setInvoices(invoicesData || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleExport = async () => {
    try {
      const blob = await exportInvoices();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'invoices_export.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (err) {
      alert('Failed to export: ' + err.message);
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm('Are you sure you want to delete ALL invoices? This cannot be undone.')) {
      return;
    }
    
    setDeleting(true);
    try {
      await deleteAllInvoices();
      alert('All invoices deleted successfully');
      fetchData();
    } catch (err) {
      alert('Failed to delete: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Signed Invoices</h1>
          <p className="text-gray-500 mt-1">Download signed PDFs and manage invoice data</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Download className="w-4 h-4" />
            Export Excel
          </button>
          <button
            onClick={handleDeleteAll}
            disabled={deleting}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            {deleting ? 'Deleting...' : 'Delete All'}
          </button>
        </div>
      </div>

      {/* Signed PDFs */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-500" />
          Signed PDF Files ({signedFiles.length})
        </h2>
        
        {signedFiles.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {signedFiles.map((file, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 transition-colors">
                <div className="flex items-start gap-3">
                  <FileText className="w-10 h-10 text-red-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate" title={file.filename}>
                      {file.filename}
                    </p>
                    <p className="text-sm text-gray-500">
                      {file.size ? `${(file.size / 1024).toFixed(1)} KB` : 'PDF Document'}
                    </p>
                  </div>
                </div>
                <div className="mt-3 flex gap-2">
                  <a
                    href={downloadSignedInvoice(file.filename)}
                    download
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </a>
                  <a
                    href={downloadSignedInvoice(file.filename)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center px-3 py-2 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <FileText className="w-16 h-16 mx-auto mb-4" />
            <p>No signed invoices yet</p>
            <p className="text-sm">Upload and process invoices to generate signed PDFs</p>
          </div>
        )}
      </div>

      {/* All Invoices Table */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">All Processed Invoices ({invoices.length})</h2>
        
        {invoices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left py-3 px-4">ID</th>
                  <th className="text-left py-3 px-4">Invoice ID</th>
                  <th className="text-left py-3 px-4">Date</th>
                  <th className="text-left py-3 px-4">Customer</th>
                  <th className="text-right py-3 px-4">Total Amount</th>
                  <th className="text-right py-3 px-4">Tax</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">{invoice.id}</td>
                    <td className="py-3 px-4 font-medium">{invoice.invoice_id || '-'}</td>
                    <td className="py-3 px-4">{invoice.invoice_date || '-'}</td>
                    <td className="py-3 px-4">{invoice.customer_name || '-'}</td>
                    <td className="py-3 px-4 text-right">
                      ${invoice.total_amount?.toLocaleString() || 0}
                    </td>
                    <td className="py-3 px-4 text-right">
                      ${invoice.tax_amount?.toLocaleString() || 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <p>No invoices in database</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default SignedInvoices;
