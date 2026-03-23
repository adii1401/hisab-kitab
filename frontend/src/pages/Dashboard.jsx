import { useEffect, useState } from 'react'
import api from '../utils/api'
import { Link } from 'react-router-dom' // Use Link for faster navigation

export default function Dashboard() {
  const [invoices, setInvoices] = useState([]) // Changed name from trips to invoices
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
  // Use /invoices instead of /trips to match your new backend
  Promise.all([
    api.get('/invoices?limit=10'), 
    api.get('/payments?pending_approval=true')
  ])
  .then(([inv, pay]) => { 
    setInvoices(inv.data); // Use the data from /invoices
    setPayments(pay.data); 
  })
  .catch(err => console.error("Dashboard Load Error:", err))
  .finally(() => setLoading(false));
}, []);

  // Helper for GST/Invoice Status badges (if you have them)
  const renderStatus = s => {
    const m = { pending: 'badge-orange', completed: 'badge-green', draft: 'badge-gray' };
    return <span className={`badge ${m[s] || 'badge-blue'}`}>{s?.toUpperCase() || 'PROCESSED'}</span>
  }

  return (
    <div className="page">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Overview of your trading operations (HSN 47079000)</p>
      </div>

      <div className="stats-grid">
        {/* Updated Stats to reflect Invoice data */}
        <div className="stat-card accent">
          <div className="stat-label">Total Invoices</div>
          <div className="stat-value">{invoices?.length || 0}</div>
        </div>
        <div className="stat-card blue">
          <div className="stat-label">Total Weight (KG)</div>
          <div className="stat-value">
            {invoices?.reduce((acc, curr) => acc + (Number(curr.net_weight_kg) || 0), 0).toLocaleString('en-IN')}
          </div>
        </div>
        <div className="stat-card green">
          <div className="stat-label">Mill Receivables</div>
          <div className="stat-value">
             ₹{invoices?.reduce((acc, curr) => acc + (Number(curr.mill_total_amount) || 0), 0).toLocaleString('en-IN')}
          </div>
        </div>
        <div className="stat-card gold">
          <div className="stat-label">Pending Approval</div>
          <div className="stat-value">{payments?.length || 0}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Recent Invoices Table */}
        <div className="card">
          <div className="card-header">
            <h3>Recent Invoices</h3>
            <Link to="/invoices" className="btn btn-ghost btn-sm">View all</Link>
          </div>
          {loading ? (
            <div className="loading-center"><div className="spinner" /></div>
          ) : !invoices || invoices.length === 0 ? (
            <div className="empty-state"><p>No invoices processed yet</p></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Inv #</th>
                    <th>Mill</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map(inv => (
                    <tr key={inv.id}>
                      <td>{inv.invoice_date || inv.trip_date}</td>
                      <td><strong>#{inv.invoice_no || inv.eway_bill_no}</strong></td>
                      <td>{inv.mill_name}</td>
                      <td className="amt-positive">₹{Number(inv.mill_total_amount).toLocaleString('en-IN')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Payments Table */}
        <div className="card">
          <div className="card-header">
            <h3>Payments Pending Approval</h3>
            <Link to="/payments" className="btn btn-ghost btn-sm">View all</Link>
          </div>
          {loading ? (
            <div className="loading-center"><div className="spinner" /></div>
          ) : !payments || payments.length === 0 ? (
            <div className="empty-state"><p>No pending payments</p></div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Direction</th>
                    <th>Amount</th>
                    <th>Party</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map(p => (
                    <tr key={p.id}>
                      <td>
                        <span className={`badge ${p.direction === 'outgoing' ? 'badge-red' : 'badge-green'}`}>
                          {p.direction}
                        </span>
                      </td>
                      <td><strong>₹{Number(p.amount).toLocaleString('en-IN')}</strong></td>
                      <td>{p.vendor_name || p.mill_name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}