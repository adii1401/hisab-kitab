import { useEffect, useState } from 'react'
import api from '../utils/api'
import toast from 'react-hot-toast'
import { useAuth } from '../hooks/useAuth'

const SB = {draft:'badge-gray',pending_approval:'badge-gold',approved:'badge-blue',executed:'badge-orange',confirmed:'badge-green',rejected:'badge-red',manual:'badge-green'}
const fmt = n => n ? `₹${Number(n).toLocaleString('en-IN',{maximumFractionDigits:2})}` : '—'

export default function Payments() {
  const {user} = useAuth(); 
  const isAdmin = user?.role === 'admin'
  
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('all')
  const [showCreate, setShowCreate] = useState(false)
  const [saving, setSaving] = useState(false)
  
  // Renamed from 'trips' to 'invoiceList' to avoid confusion
  const [invoiceList, setInvoiceList] = useState([])
  
  // Notice 'trip_id' is kept here because your backend Database still links payments to the Trip table ID
  const [form, setForm] = useState({trip_id:'', direction:'outgoing', amount:'', mode:'neft', payment_date:'', reference_no:'', notes:''})

  const load = () => { 
    setLoading(true); 
    api.get(`/payments${tab === 'pending' ? '?pending_approval=true' : ''}`)
       .then(r => setPayments(r.data))
       .finally(() => setLoading(false)) 
  }

  // Fetch the Invoices for the Dropdown
  useEffect(() => {
    api.get('/invoices?limit=200')
       .then(r => setInvoiceList(r.data))
       .catch(err => console.error("Failed to load invoices:", err))
  }, [])

  useEffect(load, [tab])

  const action = async (id, act, body={}) => {
    try { 
      await api.post(`/payments/${id}/${act}`, body); 
      toast.success(`Payment ${act}d`); 
      load() 
    } catch(err) {
      toast.error(err.response?.data?.detail || 'Error')
    }
  }

  const save = async e => {
    e.preventDefault(); 
    setSaving(true)
    try { 
      await api.post('/payments', form); 
      toast.success('Payment recorded successfully!'); 
      setShowCreate(false); 
      setForm({...form, amount:'', reference_no:'', notes:''}); // Reset form partially
      load() 
    } catch(err) {
      toast.error(err.response?.data?.detail || 'Error saving payment')
    } finally {
      setSaving(false)
    }
  }

  const f = k => e => setForm(p => ({...p, [k]: e.target.value}))

  return (
    <div className="page">
      <div className="page-header page-header-row">
        <div>
          <h2>Payments</h2>
          <p>Manage vendor payouts and mill collections</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ Record Payment</button>
      </div>
      
      <div className="tabs">
        <button className={`tab-btn ${tab === 'all' ? 'active' : ''}`} onClick={() => setTab('all')}>All Payments</button>
        <button className={`tab-btn ${tab === 'pending' ? 'active' : ''}`} onClick={() => setTab('pending')}>Pending Approval</button>
      </div>

      <div className="card">
        <div className="table-wrap">
          {loading ? <div className="loading-center"><div className="spinner"/></div> : payments.length === 0 ? <div className="empty-state"><p>No payments found</p></div> :
            <table>
              <thead>
                <tr><th>Direction</th><th>Amount</th><th>Mode</th><th>Party</th><th>Date</th><th>Ref</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {payments.map(p => <tr key={p.id}>
                  <td><span className={`badge ${p.direction === 'outgoing' ? 'badge-red' : 'badge-green'}`}>{p.direction}</span></td>
                  <td><strong>{fmt(p.amount)}</strong></td>
                  <td>{p.mode?.replace('_',' ').toUpperCase()}</td>
                  <td>{p.vendor_name || p.mill_name || '—'}</td>
                  <td>{p.payment_date || '—'}</td>
                  <td><code style={{fontSize:'0.78rem'}}>{p.reference_no || '—'}</code></td>
                  <td><span className={`badge ${SB[p.status] || 'badge-gray'}`}>{p.status}</span></td>
                  <td>
                    <div style={{display:'flex', gap:4}}>
                      {p.status === 'draft' && <button className="btn btn-ghost btn-sm" onClick={() => action(p.id,'submit')}>Submit</button>}
                      {p.status === 'pending_approval' && isAdmin && <><button className="btn btn-primary btn-sm" onClick={() => action(p.id,'approve',{})}>Approve</button><button className="btn btn-danger btn-sm" onClick={() => {const r=prompt('Rejection reason?'); if(r) action(p.id,'approve',{rejection_reason:r})}}>Reject</button></>}
                      {p.status === 'approved' && <button className="btn btn-ghost btn-sm" onClick={() => action(p.id,'execute',{})}>Execute</button>}
                      {p.status === 'executed' && isAdmin && <button className="btn btn-primary btn-sm" onClick={() => action(p.id,'confirm',{})}>Confirm</button>}
                    </div>
                  </td>
                </tr>)}
              </tbody>
            </table>
          }
        </div>
      </div>

      {showCreate && <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setShowCreate(false)}>
        <div className="modal">
          <div className="modal-header">
            <h3>Record Payment</h3>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowCreate(false)}>✕</button>
          </div>
          <form onSubmit={save}>
            <div className="modal-body">
              <div className="form-grid">
                
                {/* UPDATED DROPDOWN */}
                <div className="form-group full">
                  <label>Link to Invoice *</label>
                  <select value={form.trip_id} onChange={f('trip_id')} required>
                    <option value="">-- Select Invoice --</option>
                    {invoiceList.map(inv => (
                      <option key={inv.id} value={inv.id}>
                        {inv.trip_date} | Inv #{inv.eway_bill_no || 'N/A'} | {inv.vehicle_no}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Direction *</label>
                  <select value={form.direction} onChange={f('direction')}>
                    <option value="outgoing">Outgoing (Pay Vendor)</option>
                    <option value="incoming">Incoming (Collect from Mill)</option>
                  </select>
                </div>
                
                <div className="form-group"><label>Amount (₹) *</label><input type="number" step="0.01" value={form.amount} onChange={f('amount')} required/></div>
                <div className="form-group"><label>Mode *</label><select value={form.mode} onChange={f('mode')}><option value="neft">NEFT</option><option value="rtgs">RTGS</option><option value="upi">UPI</option><option value="cash">Cash</option><option value="cheque">Cheque</option></select></div>
                <div className="form-group"><label>Payment Date</label><input type="date" value={form.payment_date} onChange={f('payment_date')}/></div>
                <div className="form-group"><label>Reference No</label><input value={form.reference_no} onChange={f('reference_no')}/></div>
                <div className="form-group full"><label>Notes</label><textarea value={form.notes} onChange={f('notes')} rows={2}/></div>
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Save Payment'}</button>
            </div>
          </form>
        </div>
      </div>}
    </div>
  )
}