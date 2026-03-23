import { useEffect, useState } from 'react'
import api from '../utils/api'
import toast from 'react-hot-toast'
const EMPTY = {name:'',gstin:'',phone:'',city:'',address:'',bank_name:'',bank_account:'',bank_ifsc:'',upi_id:'',notes:''}
export default function Vendors() {
  const [vendors, setVendors] = useState([]); const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false); const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY); const [saving, setSaving] = useState(false)
  const [search, setSearch] = useState(''); const [activeOnly, setActiveOnly] = useState(true)
  const load = () => { setLoading(true); api.get(`/vendors?active_only=${activeOnly}`).then(r=>setVendors(r.data)).finally(()=>setLoading(false)) }
  useEffect(load, [activeOnly])
  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true) }
  const openEdit = v => { setEditing(v); setForm({...EMPTY,...v}); setShowModal(true) }
  const save = async e => {
    e.preventDefault(); setSaving(true)
    try {
      if(editing){await api.patch(`/vendors/${editing.id}`,form);toast.success('Vendor updated')}
      else{await api.post('/vendors',form);toast.success('Vendor created')}
      setShowModal(false); load()
    } catch(err){toast.error(err.response?.data?.detail||'Error')} finally{setSaving(false)}
  }
  const f = k => e => setForm(p=>({...p,[k]:e.target.value}))
  const filtered = vendors.filter(v=>v.name.toLowerCase().includes(search.toLowerCase())||v.phone?.includes(search))
  return (
    <div className="page">
      <div className="page-header page-header-row"><div><h2>Vendors</h2><p>Manage material suppliers</p></div><button className="btn btn-primary" onClick={openCreate}>+ Add Vendor</button></div>
      <div className="card">
        <div className="card-body" style={{paddingBottom:0}}>
          <div className="filters-bar">
            <input placeholder="Search vendors..." value={search} onChange={e=>setSearch(e.target.value)} style={{width:240}}/>
            <label style={{display:'flex',alignItems:'center',gap:6,textTransform:'none',fontSize:'0.85rem',color:'var(--ink-2)'}}><input type="checkbox" checked={activeOnly} onChange={e=>setActiveOnly(e.target.checked)} style={{width:'auto'}}/>Active only</label>
          </div>
        </div>
        <div className="table-wrap">
          {loading?<div className="loading-center"><div className="spinner"/></div>:filtered.length===0?<div className="empty-state"><p>No vendors found</p></div>:
            <table><thead><tr><th>Name</th><th>GSTIN</th><th>Phone</th><th>City</th><th>Bank</th><th>Status</th><th></th></tr></thead><tbody>
              {filtered.map(v=><tr key={v.id}><td><strong>{v.name}</strong></td><td><code style={{fontSize:'0.8rem'}}>{v.gstin||'—'}</code></td><td>{v.phone||'—'}</td><td>{v.city||'—'}</td><td>{v.bank_name||'—'}</td><td><span className={`badge ${v.is_active?'badge-green':'badge-gray'}`}>{v.is_active?'Active':'Inactive'}</span></td><td><button className="btn btn-ghost btn-sm" onClick={()=>openEdit(v)}>Edit</button></td></tr>)}
            </tbody></table>}
        </div>
      </div>
      {showModal&&<div className="modal-overlay" onClick={e=>e.target===e.currentTarget&&setShowModal(false)}>
        <div className="modal modal-lg">
          <div className="modal-header"><h3>{editing?'Edit Vendor':'New Vendor'}</h3><button className="btn btn-ghost btn-sm" onClick={()=>setShowModal(false)}>✕</button></div>
          <form onSubmit={save}>
            <div className="modal-body"><div className="form-grid">
              <div className="form-group full"><label>Name *</label><input value={form.name} onChange={f('name')} required/></div>
              <div className="form-group"><label>GSTIN</label><input value={form.gstin} onChange={f('gstin')}/></div>
              <div className="form-group"><label>Phone</label><input value={form.phone} onChange={f('phone')}/></div>
              <div className="form-group"><label>City</label><input value={form.city} onChange={f('city')}/></div>
              <div className="form-group full"><label>Address</label><textarea value={form.address} onChange={f('address')} rows={2}/></div>
              <div className="form-group"><label>Bank Name</label><input value={form.bank_name} onChange={f('bank_name')}/></div>
              <div className="form-group"><label>Account No</label><input value={form.bank_account} onChange={f('bank_account')}/></div>
              <div className="form-group"><label>IFSC</label><input value={form.bank_ifsc} onChange={f('bank_ifsc')}/></div>
              <div className="form-group"><label>UPI ID</label><input value={form.upi_id} onChange={f('upi_id')}/></div>
              <div className="form-group full"><label>Notes</label><textarea value={form.notes} onChange={f('notes')} rows={2}/></div>
            </div></div>
            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={()=>setShowModal(false)}>Cancel</button><button type="submit" className="btn btn-primary" disabled={saving}>{saving?'Saving…':'Save Vendor'}</button></div>
          </form>
        </div>
      </div>}
    </div>
  )
}
