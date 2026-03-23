import { useEffect, useState } from 'react'
import api from '../utils/api'
import toast from 'react-hot-toast'
const EMPTY = {name:'',gstin:'',phone:'',city:'',address:'',contact_person:'',notes:''}
export default function Mills() {
  const [mills, setMills] = useState([]); const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false); const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY); const [saving, setSaving] = useState(false); const [search, setSearch] = useState('')
  const load = () => { setLoading(true); api.get('/mills').then(r=>setMills(r.data)).finally(()=>setLoading(false)) }
  useEffect(load, [])
  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true) }
  const openEdit = m => { setEditing(m); setForm({...EMPTY,...m}); setShowModal(true) }
  const save = async e => {
    e.preventDefault(); setSaving(true)
    try {
      if(editing){await api.patch(`/mills/${editing.id}`,form);toast.success('Mill updated')}
      else{await api.post('/mills',form);toast.success('Mill created')}
      setShowModal(false); load()
    } catch(err){toast.error(err.response?.data?.detail||'Error')} finally{setSaving(false)}
  }
  const f = k => e => setForm(p=>({...p,[k]:e.target.value}))
  const filtered = mills.filter(m=>m.name.toLowerCase().includes(search.toLowerCase()))
  return (
    <div className="page">
      <div className="page-header page-header-row"><div><h2>Mills</h2><p>Paper mills and recycling facilities</p></div><button className="btn btn-primary" onClick={openCreate}>+ Add Mill</button></div>
      <div className="card">
        <div className="card-body" style={{paddingBottom:0}}><div className="filters-bar"><input placeholder="Search mills..." value={search} onChange={e=>setSearch(e.target.value)} style={{width:240}}/></div></div>
        <div className="table-wrap">
          {loading?<div className="loading-center"><div className="spinner"/></div>:filtered.length===0?<div className="empty-state"><p>No mills found</p></div>:
            <table><thead><tr><th>Name</th><th>GSTIN</th><th>Phone</th><th>City</th><th>Contact</th><th>Status</th><th></th></tr></thead><tbody>
              {filtered.map(m=><tr key={m.id}><td><strong>{m.name}</strong></td><td><code style={{fontSize:'0.8rem'}}>{m.gstin||'—'}</code></td><td>{m.phone||'—'}</td><td>{m.city||'—'}</td><td>{m.contact_person||'—'}</td><td><span className={`badge ${m.is_active?'badge-green':'badge-gray'}`}>{m.is_active?'Active':'Inactive'}</span></td><td><button className="btn btn-ghost btn-sm" onClick={()=>openEdit(m)}>Edit</button></td></tr>)}
            </tbody></table>}
        </div>
      </div>
      {showModal&&<div className="modal-overlay" onClick={e=>e.target===e.currentTarget&&setShowModal(false)}>
        <div className="modal"><div className="modal-header"><h3>{editing?'Edit Mill':'New Mill'}</h3><button className="btn btn-ghost btn-sm" onClick={()=>setShowModal(false)}>✕</button></div>
          <form onSubmit={save}><div className="modal-body"><div className="form-grid">
            <div className="form-group full"><label>Name *</label><input value={form.name} onChange={f('name')} required/></div>
            <div className="form-group"><label>GSTIN</label><input value={form.gstin} onChange={f('gstin')}/></div>
            <div className="form-group"><label>Phone</label><input value={form.phone} onChange={f('phone')}/></div>
            <div className="form-group"><label>City</label><input value={form.city} onChange={f('city')}/></div>
            <div className="form-group"><label>Contact Person</label><input value={form.contact_person} onChange={f('contact_person')}/></div>
            <div className="form-group full"><label>Address</label><textarea value={form.address} onChange={f('address')} rows={2}/></div>
            <div className="form-group full"><label>Notes</label><textarea value={form.notes} onChange={f('notes')} rows={2}/></div>
          </div></div>
          <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={()=>setShowModal(false)}>Cancel</button><button type="submit" className="btn btn-primary" disabled={saving}>{saving?'Saving…':'Save Mill'}</button></div>
          </form>
        </div>
      </div>}
    </div>
  )
}
