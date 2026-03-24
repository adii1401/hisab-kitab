import { useEffect, useState, useRef } from 'react';
import api from '../utils/api';
import toast from 'react-hot-toast';
import { useReactToPrint } from 'react-to-print';
import InvoicePDF from '../components/InvoicePDF'; // Assuming you saved the template here

const today = () => new Date().toISOString().slice(0, 10);

const EMPTY = {
  invoice_date: today(),
  invoice_no: '',
  vendor_id: '',
  mill_id: '',
  vehicle_no: '',
  driver_phone: '',
  net_weight_kg: '',
  negotiated_buy_rate: '',
  negotiated_sell_rate: '',
  hsn_code: '47079000',
  gst_percent: '5.00',
  advance_to_vendor: '0',
  freight_cost: '0',
  transaction_type: 'regular',
  dispatch_pincode: '',
  ship_to_pincode: ''
};

const GST_SLABS = ['0.00', '5.00', '12.00', '18.00', '28.00'];

const fmt = n => n ? `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 })}` : '—';

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [mills, setMills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  // --- PDF PRINTING LOGIC ---
  const printRef = useRef();
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  const handlePrint = useReactToPrint({
    content: () => printRef.current,
    documentTitle: selectedInvoice ? `Invoice_${selectedInvoice.eway_bill_no || 'Document'}` : 'Invoice',
    onAfterPrint: () => setSelectedInvoice(null), // Clear memory after printing
  });

  const triggerPrint = (invoice) => {
    setSelectedInvoice(invoice);
    // Give React 100ms to load the invoice data into the hidden PDF template before popping the print window
    setTimeout(() => {
      handlePrint();
    }, 100);
  };
  // -------------------------

  const load = () => {
    setLoading(true);
    api.get('/invoices')
       .then(r => setInvoices(r.data))
       .catch(err => {
         console.error(err);
         toast.error("Failed to load invoices");
       })
       .finally(() => setLoading(false));
  };

  useEffect(() => {
    Promise.all([api.get('/vendors'), api.get('/mills')])
      .then(([v, m]) => {
        setVendors(v.data); 
        setMills(m.data);
      })
      .catch(err => console.error(err));
    load();
  }, []);

  const save = async e => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/invoices/process-invoice', form);
      toast.success('Invoice Created Successfully');
      setShowModal(false);
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error creating invoice. Check data.');
    } finally { 
      setSaving(false); 
    }
  };

  const f = k => e => setForm(p => ({ ...p, [k]: e.target.value }));

  // Live calculation for the "Hisab Preview"
  const taxable = (Number(form.net_weight_kg) * Number(form.negotiated_sell_rate)).toFixed(2);
  const total = (Number(taxable) * (1 + Number(form.gst_percent) / 100)).toFixed(2);

  return (
    <div className="page">
      <div className="page-header page-header-row">
        <div>
          <h2>Invoices</h2>
          <p>Manage Mill Sales & Vendor Purchases</p>
        </div>
        <button className="btn btn-primary" onClick={() => { setForm(EMPTY); setShowModal(true); }}>
          + New Invoice
        </button>
      </div>

      <div className="card">
        <div className="table-wrap">
          {loading ? <div className="spinner" /> : (
            <table>
              <thead>
                <tr>
                  <th>Inv No.</th>
                  <th>Date</th>
                  <th>Vehicle</th>
                  <th>Mill / Vendor</th>
                  <th>Weight</th>
                  <th>Sell Rate</th>
                  <th>Buy Rate</th>
                  <th>Total Bill</th>
                  <th style={{textAlign: 'center'}}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map(inv => (
                  <tr key={inv.id}>
                    <td><strong>#{inv.eway_bill_no}</strong></td>
                    <td>{inv.trip_date}</td>
                    <td>{inv.vehicle_no}</td>
                    <td>
                        {/* FIXED: Added fallback for flat or nested backend response */}
                        <div style={{fontSize: '0.85rem'}}>{inv.mill?.name || inv.mill_name || 'Unknown Mill'}</div>
                        <div style={{fontSize: '0.75rem', color: 'var(--ink-3)'}}>{inv.vendor?.name || inv.vendor_name || 'Unknown Vendor'}</div>
                    </td>
                    <td>{inv.loaded_weight_kg} kg</td>
                    <td>₹{inv.mill_default_rate_per_kg}</td>
                    <td>₹{inv.vendor_rate_per_kg}</td>
                    <td style={{fontWeight: 600}}>{fmt(inv.mill_total_amount)}</td>
                    <td style={{textAlign: 'center'}}>
                       {/* PDF Print Button added here */}
                       <button 
                          onClick={() => triggerPrint(inv)}
                          style={{
                            background: '#1a1a1a', 
                            color: 'white', 
                            padding: '4px 8px', 
                            borderRadius: '4px', 
                            fontSize: '0.8rem',
                            cursor: 'pointer',
                            border: 'none'
                          }}
                        >
                          🖨️ PDF
                        </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal modal-lg">
            <div className="modal-header">
              <h3>Process New Invoice</h3>
              <button className="btn btn-ghost" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={save}>
              <div className="modal-body">
                <div className="form-grid">
                  
                  <div className="form-group"><label>Invoice No *</label><input value={form.invoice_no} onChange={f('invoice_no')} placeholder="e.g. 42" required /></div>
                  <div className="form-group"><label>Date *</label><input type="date" value={form.invoice_date} onChange={f('invoice_date')} required /></div>
                  
                  <div className="form-group"><label>Mill (Buyer) *</label>
                    <select value={form.mill_id} onChange={f('mill_id')} required>
                      <option value="">Select mill…</option>
                      {mills.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                    </select>
                  </div>
                  
                  <div className="form-group"><label>Vendor (Supplier) *</label>
                    <select value={form.vendor_id} onChange={f('vendor_id')} required>
                      <option value="">Select vendor…</option>
                      {vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                    </select>
                  </div>
                  
                  <div className="form-group"><label>Vehicle No *</label><input value={form.vehicle_no} onChange={f('vehicle_no')} placeholder="UP78DN..." required /></div>
                  <div className="form-group"><label>Driver Phone</label><input value={form.driver_phone} onChange={f('driver_phone')} placeholder="10 Digit Mobile" /></div>
                  
                  <div className="form-group"><label>HSN Code</label><input value={form.hsn_code} onChange={f('hsn_code')} /></div>
                  <div className="form-group"><label>Net Weight (KG) *</label><input type="number" value={form.net_weight_kg} onChange={f('net_weight_kg')} required /></div>
                  
                  <div className="form-group"><label>Sell Rate (Negotiated) *</label><input type="number" step="0.01" value={form.negotiated_sell_rate} onChange={f('negotiated_sell_rate')} required /></div>
                  <div className="form-group"><label>Buy Rate (Negotiated) *</label><input type="number" step="0.01" value={form.negotiated_buy_rate} onChange={f('negotiated_buy_rate')} required /></div>
                  
                  <div className="form-group"><label>GST Slab</label>
                    <select value={form.gst_percent} onChange={f('gst_percent')}>
                      {GST_SLABS.map(s => <option key={s} value={s}>{s}%</option>)}
                    </select>
                  </div>
                  <div className="form-group"><label>Advance to Vendor</label><input type="number" value={form.advance_to_vendor} onChange={f('advance_to_vendor')} /></div>

                  {/* --- NEW LOGISTICS SECTION FOR E-WAY BILLS --- */}
                  <div className="form-group full" style={{ marginTop: '15px', borderTop: '1px solid #eee', paddingTop: '15px' }}>
                    <label style={{ color: 'var(--primary)', fontWeight: 'bold' }}>E-Way Bill & Logistics Type *</label>
                    <select value={form.transaction_type} onChange={f('transaction_type')} required style={{ backgroundColor: '#f8f9fa' }}>
                      <option value="regular">1. Regular (Billing matches Shipping)</option>
                      <option value="bill_to_ship_to">2. Bill To - Ship To (Ship to different location)</option>
                      <option value="bill_from_dispatch_from">3. Bill From - Dispatch From (Dispatch from different location)</option>
                      <option value="combination">4. Combination of 2 and 3 (Both differ)</option>
                    </select>
                  </div>

                  {/* Conditionally render Dispatch Pincode */}
                  {(form.transaction_type === 'bill_from_dispatch_from' || form.transaction_type === 'combination') && (
                    <div className="form-group">
                      <label>Dispatch From Pincode *</label>
                      <input 
                        value={form.dispatch_pincode} 
                        onChange={f('dispatch_pincode')} 
                        placeholder="e.g. 733121" 
                        maxLength="6"
                        required 
                      />
                    </div>
                  )}

                  {/* Conditionally render Ship To Pincode */}
                  {(form.transaction_type === 'bill_to_ship_to' || form.transaction_type === 'combination') && (
                    <div className="form-group">
                      <label>Ship To Pincode *</label>
                      <input 
                        value={form.ship_to_pincode} 
                        onChange={f('ship_to_pincode')} 
                        placeholder="e.g. 209311" 
                        maxLength="6"
                        required 
                      />
                    </div>
                  )}
                  {/* --- END LOGISTICS SECTION --- */}

                </div>

                <div style={{ marginTop: 20, padding: 15, background: '#f8f9fa', borderRadius: 8 }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Taxable Amount: <strong>₹{taxable}</strong></span>
                      <span>GST Amount: <strong>₹{(total - taxable).toFixed(2)}</strong></span>
                      <span style={{color: 'var(--green)'}}>Total Mill Bill: <strong>₹{total}</strong></span>
                   </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Confirm & Save Invoice'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --- HIDDEN PRINT TEMPLATE --- */}
      <div style={{ display: 'none' }}>
        <InvoicePDF ref={printRef} invoiceData={selectedInvoice} />
      </div>

    </div>
  );
}