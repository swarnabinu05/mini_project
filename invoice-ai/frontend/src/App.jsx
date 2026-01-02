import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  Upload, 
  BarChart3, 
  CheckCircle, 
  Users, 
  FileText, 
  Shield,
  Home,
  Search
} from 'lucide-react';
import './index.css';

// Import pages
import Dashboard from './pages/Dashboard';
import UploadInvoice from './pages/UploadInvoice';
import Analytics from './pages/Analytics';
import Approvals from './pages/Approvals';
import Vendors from './pages/Vendors';
import SignedInvoices from './pages/SignedInvoices';
import ProductClassifier from './pages/ProductClassifier';

const navItems = [
  { path: '/', name: 'Dashboard', icon: Home },
  { path: '/upload', name: 'Upload Invoice', icon: Upload },
  { path: '/analytics', name: 'Analytics', icon: BarChart3 },
  { path: '/approvals', name: 'Approvals', icon: CheckCircle },
  { path: '/vendors', name: 'Vendors & Fraud', icon: Shield },
  { path: '/signed', name: 'Signed Invoices', icon: FileText },
  { path: '/classify', name: 'Product Classifier', icon: Search },
];

function Sidebar() {
  const location = useLocation();
  
  return (
    <div className="w-64 bg-gray-900 min-h-screen fixed left-0 top-0">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <FileText className="w-8 h-8 text-blue-400" />
          Invoice AI
        </h1>
        <p className="text-gray-400 text-sm mt-1">Processing System</p>
      </div>
      
      <nav className="mt-6">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-6 py-3 text-sm font-medium transition-colors ${
                isActive 
                  ? 'bg-blue-600 text-white border-r-4 border-blue-400' 
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
        <div className="text-xs text-gray-500">
          Backend: http://127.0.0.1:8001
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Sidebar />
        
        <main className="ml-64 p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<UploadInvoice />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/vendors" element={<Vendors />} />
            <Route path="/signed" element={<SignedInvoices />} />
            <Route path="/classify" element={<ProductClassifier />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
