import React from 'react';
import './index.css';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <h1 className="text-3xl font-bold text-gray-900">Invoice AI</h1>
            <div className="text-sm text-gray-500">
              Intelligent Invoice Processing System
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-gray-600 mb-4">
                Welcome to Invoice AI
              </h2>
              <p className="text-gray-500 mb-6">
                Upload invoices for automated processing and validation
              </p>
              <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                Upload Invoice
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
