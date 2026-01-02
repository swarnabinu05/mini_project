import React, { useState } from 'react';
import { Search, Tag, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { classifyProduct } from '../services/api';

function ProductClassifier() {
  const [description, setDescription] = useState('');
  const [hsCode, setHsCode] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleClassify = async (e) => {
    e.preventDefault();
    if (!description.trim()) {
      alert('Please enter a product description');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await classifyProduct(description, hsCode || null);
      setResult(response);
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const exampleProducts = [
    { desc: 'Hyundai Exter', hs: '' },
    { desc: 'Mazda 6 Sedan', hs: '' },
    { desc: 'Toyota Camry 2024', hs: '870323' },
    { desc: 'Dell Laptop XPS 15', hs: '' },
    { desc: 'Iron Ore Fines', hs: '260111' },
    { desc: 'Steel Coils Hot Rolled', hs: '720851' },
    { desc: 'Pfizer Medicine', hs: '' },
    { desc: 'Unknown Product XYZ', hs: '' },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Product Classifier</h1>
        <p className="text-gray-500 mt-1">Test the smart product classification system</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Classify a Product</h2>
          
          <form onSubmit={handleClassify}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Product Description *
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., Hyundai Exter, Mazda 6, Dell Laptop"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                HS Code (Optional)
              </label>
              <input
                type="text"
                value={hsCode}
                onChange={(e) => setHsCode(e.target.value)}
                placeholder="e.g., 870323, 260111"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                6-digit Harmonized System code for more accurate classification
              </p>
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Classifying...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Classify Product
                </>
              )}
            </button>
          </form>

          {/* Example Products */}
          <div className="mt-6 pt-6 border-t">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Try these examples:</h3>
            <div className="flex flex-wrap gap-2">
              {exampleProducts.map((example, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setDescription(example.desc);
                    setHsCode(example.hs);
                  }}
                  className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-700"
                >
                  {example.desc}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Result Panel */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Classification Result</h2>
          
          {!result && !loading && (
            <div className="text-center py-12 text-gray-400">
              <Tag className="w-16 h-16 mx-auto mb-4" />
              <p>Enter a product description to see classification</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-12">
              <Loader2 className="w-16 h-16 mx-auto mb-4 text-blue-500 animate-spin" />
              <p className="text-gray-600">Analyzing product...</p>
            </div>
          )}

          {result && !result.error && (
            <div>
              {/* Classification Status */}
              <div className={`flex items-center gap-3 p-4 rounded-lg mb-4 ${
                result.classification?.classified 
                  ? 'bg-green-50 text-green-800'
                  : 'bg-yellow-50 text-yellow-800'
              }`}>
                {result.classification?.classified ? (
                  <CheckCircle className="w-6 h-6" />
                ) : (
                  <XCircle className="w-6 h-6" />
                )}
                <span className="font-semibold">
                  {result.classification?.classified ? 'Product Classified' : 'Could Not Classify'}
                </span>
              </div>

              {/* Input */}
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-medium text-gray-500 mb-2">Input</h4>
                <p className="font-medium">{result.input?.description}</p>
                {result.input?.hs_code && (
                  <p className="text-sm text-gray-600">HS Code: {result.input.hs_code}</p>
                )}
              </div>

              {/* Classification Details */}
              {result.classification?.classified && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                    <span className="text-sm text-gray-600">Category</span>
                    <span className="font-semibold text-blue-800 capitalize">
                      {result.classification.category?.replace(/_/g, ' ')}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Confidence</span>
                    <span className={`font-semibold capitalize ${
                      result.classification.confidence === 'high' ? 'text-green-600' :
                      result.classification.confidence === 'medium' ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {result.classification.confidence}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Method</span>
                    <span className="font-medium text-gray-800">
                      {result.classification.classification_method?.replace(/_/g, ' ')}
                    </span>
                  </div>

                  {result.classification.suggested_hs_code && (
                    <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                      <span className="text-sm text-gray-600">Suggested HS Code</span>
                      <span className="font-semibold text-purple-800">
                        {result.classification.suggested_hs_code}
                      </span>
                    </div>
                  )}

                  {/* Details */}
                  {result.classification.details && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-500 mb-2">Details</h4>
                      <pre className="text-xs text-gray-600 overflow-auto">
                        {JSON.stringify(result.classification.details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {!result.classification?.classified && (
                <div className="p-4 bg-yellow-50 rounded-lg">
                  <p className="text-yellow-800">
                    This product could not be automatically classified. 
                    Consider providing an HS code or adding the brand to the system.
                  </p>
                </div>
              )}
            </div>
          )}

          {result?.error && (
            <div className="p-4 bg-red-50 rounded-lg">
              <p className="text-red-800">Error: {result.error}</p>
            </div>
          )}
        </div>
      </div>

      {/* Supported Categories */}
      <div className="mt-8 bg-white rounded-xl shadow-sm p-6">
        <h2 className="text-lg font-semibold mb-4">Supported Categories & Brands</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="font-medium text-blue-800 mb-2">Cars (10% tax in Russia)</h3>
            <p className="text-sm text-gray-600">
              Toyota, Honda, Hyundai, Mazda, Ford, BMW, Mercedes, Audi, VW, Nissan, Kia, 
              Suzuki, Tata, Mahindra, Maruti, Tesla, and more...
            </p>
          </div>
          <div>
            <h3 className="font-medium text-purple-800 mb-2">Electronics (18% tax)</h3>
            <p className="text-sm text-gray-600">
              Dell, HP, Lenovo, Asus, Acer, Apple, MacBook, ThinkPad, Intel, AMD, Nvidia
            </p>
          </div>
          <div>
            <h3 className="font-medium text-green-800 mb-2">Medicines (50% tax)</h3>
            <p className="text-sm text-gray-600">
              Pfizer, Novartis, Roche, Johnson, Merck, Sanofi, Cipla, Sun Pharma
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductClassifier;
