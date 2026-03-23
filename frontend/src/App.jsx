import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Invoices from './pages/Invoices'; 
import Vendors from './pages/Vendors';
import Mills from './pages/Mills';
import Payments from './pages/Payments';
import Ledger from './pages/Ledger';
import Rates from './pages/Rates';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="invoices" element={<Invoices />} />
          <Route path="vendors" element={<Vendors />} />
          <Route path="mills" element={<Mills />} />
          <Route path="rates" element={<Rates />} />
          <Route path="payments" element={<Payments />} />
          <Route path="ledger" element={<Ledger />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </>
  );
}