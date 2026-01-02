import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { uploadInvoice } from '../services/api';

const COUNTRIES = [
  { value: 'russia', label: 'Russia' },
  { value: 'china', label: 'China' },
  { value: 'india', label: 'India' },
  { value: 'usa', label: 'United States' },
  { value: 'germany', label: 'Germany' },
];

function UploadInvoice() {
  const [invoiceFile, setInvoiceFile] = useState(null);
  const [certificateFile, setCertificateFile] = useState(null);
  const [country, setCountry] = useState('russia');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleInvoiceChange = (e) => {
    if (e.target.files[0]) {
      setInvoiceFile(e.target.files[0]);
    }
  };

  const handleCertificateChange = (e) => {
    if (e.target.files[0]) {
      setCertificateFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!invoiceFile) {
      alert('Please select an invoice file');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await uploadInvoice(invoiceFile, certificateFile, country);
      setResult(response);
    } catch (error) {
      setResult({
        status: 'error',
        message: error.response?.data?.detail || error.message || 'Upload failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setInvoiceFile(null);
    setCertificateFile(null);
    setResult(null);
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Upload Invoice</h1>
        <p className="text-gray-500 mt-1">Upload invoices for validation and processing</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload Form */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <form onSubmit={handleSubmit}>
            {/* Country Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Destination Country
              </label>
              <select
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {COUNTRIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>

            {/* Invoice Upload */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Invoice File (PDF or Image) *
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={handleInvoiceChange}
                  className="hidden"
                  id="invoice-upload"
                />
                <label htmlFor="invoice-upload" className="cursor-pointer">
                  {invoiceFile ? (
                    <div className="flex items-center justify-center gap-2 text-green-600">
                      <FileText className="w-8 h-8" />
                      <span className="font-medium">{invoiceFile.name}</span>
                    </div>
                  ) : (
                    <div>
                      <Upload className="w-12 h-12 mx-auto text-gray-400 mb-2" />
                      <p className="text-gray-600">Click to upload invoice</p>
                      <p className="text-sm text-gray-400">PDF, PNG, JPG up to 10MB</p>
                    </div>
                  )}
                </label>
              </div>
            </div>

            {/* Certificate Upload (Optional) */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quality Certificate (Optional)
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={handleCertificateChange}
                  className="hidden"
                  id="certificate-upload"
                />
                <label htmlFor="certificate-upload" className="cursor-pointer">
                  {certificateFile ? (
                    <div className="flex items-center justify-center gap-2 text-green-600">
                      <FileText className="w-8 h-8" />
                      <span className="font-medium">{certificateFile.name}</span>
                    </div>
                  ) : (
                    <div>
                      <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                      <p className="text-gray-600 text-sm">Click to upload certificate</p>
                      <p className="text-xs text-gray-400">Required for restricted items (Iron Ore, Steel)</p>
                    </div>
                  )}
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !invoiceFile}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Upload & Validate
                </>
              )}
            </button>
          </form>
        </div>

        {/* Result Panel */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Processing Result</h2>
          
          {!result && !loading && (
            <div className="text-center py-12 text-gray-400">
              <FileText className="w-16 h-16 mx-auto mb-4" />
              <p>Upload an invoice to see results</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-12">
              <Loader2 className="w-16 h-16 mx-auto mb-4 text-blue-500 animate-spin" />
              <p className="text-gray-600">Processing invoice...</p>
            </div>
          )}

          {result && (
            <div>
              {/* Status Badge */}
              <div className={`flex items-center gap-2 p-4 rounded-lg mb-4 ${
                result.status === 'processed_and_saved' 
                  ? 'bg-green-50 text-green-800'
                  : result.status === 'validation_failed'
                  ? 'bg-yellow-50 text-yellow-800'
                  : 'bg-red-50 text-red-800'
              }`}>
                {result.status === 'processed_and_saved' ? (
                  <CheckCircle className="w-6 h-6" />
                ) : result.status === 'validation_failed' ? (
                  <AlertTriangle className="w-6 h-6" />
                ) : (
                  <XCircle className="w-6 h-6" />
                )}
                <span className="font-semibold capitalize">
                  {result.status?.replace(/_/g, ' ')}
                </span>
              </div>

              {/* Errors */}
              {result.errors && result.errors.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-medium text-red-800 mb-2">Validation Errors:</h3>
                  <ul className="space-y-2">
                    {result.errors.map((error, index) => (
                      <li key={index} className="text-sm text-red-600 bg-red-50 p-2 rounded">
                        {error}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Success Info */}
              {result.status === 'processed_and_saved' && (
                <div className="space-y-3">
                  {result.download_url && (
                    <a
                      href={result.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block w-full bg-green-600 hover:bg-green-700 text-white text-center font-bold py-2 px-4 rounded-lg"
                    >
                      Download Signed Invoice
                    </a>
                  )}
                  
                  {result.approval && (
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="font-medium text-blue-800 mb-2">Approval Status</h4>
                      <p className="text-sm text-blue-600">
                        Status: {result.approval.status}<br />
                        Level: {result.approval.level}<br />
                        Approver: {result.approval.current_approver}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Fraud Analysis */}
              {result.fraud_analysis && (
                <div className={`mt-4 p-4 rounded-lg ${
                  result.fraud_analysis.risk_level === 'HIGH' 
                    ? 'bg-red-50' 
                    : result.fraud_analysis.risk_level === 'MEDIUM'
                    ? 'bg-yellow-50'
                    : 'bg-green-50'
                }`}>
                  <h4 className="font-medium mb-2">Fraud Analysis</h4>
                  <p className="text-sm">
                    Risk Level: <span className="font-bold">{result.fraud_analysis.risk_level}</span><br />
                    Score: {result.fraud_analysis.fraud_score}
                  </p>
                  {result.fraud_analysis.flags?.length > 0 && (
                    <ul className="mt-2 text-sm">
                      {result.fraud_analysis.flags.map((flag, i) => (
                        <li key={i} className="text-red-600">• {flag}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {/* Reset Button */}
              <button
                onClick={resetForm}
                className="w-full mt-4 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded-lg"
              >
                Upload Another Invoice
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default UploadInvoice;
