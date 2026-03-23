import { useEffect, useState } from 'react'
import api from '../utils/api'
import toast from 'react-hot-toast'
const today = () => new Date().toISOString().slice(0,10)
export default function Rates() {
  const [rates, setRates] = useState([]); const [vendors, setVendors] = useState([]); const [mills, setMills] = useState([])
  const [loading, setLoading] = useState(true); const [date, setDate] = useState(today())
  const [form, setForm] = useState({party_type:'vendor',party_id:'',rate_per_kg:'',rate_date:today(),material_type:'paper'})
  const [saving, setSaving] = useState(false)
  const load = () => { setLoading(true); api.get(`/rates?rate_date=${date}`).then(r=>setRates(r.data)).finally(()=>setLoading(false)) }
  useEffect(()=>{Promise.all([api.get('/vendors'),api.get('/mills')]).then(([v,m])=>{setVendors(v.data);setMills(m.data)})}, [])
  useEffect(load, [date])
  const save = async e => {
    e.preventDefault(); setSaving(true)
    try { await api.post('/rates/single',{...form,rate_date:form.rate_date||date}); toast.success('Rate saved'); setForm(p=>({...p,rate_per_kg:'',party_id:''})); load() }
    catch(err){toast.error(err.response?.data?.detail||'Error')} finally{setSaving(false)}
  }
  const f = k => e => setForm(p=>({...p,[k]:e.target.value}))
  const parties = form.party_type==='vendor'?vendors:mills
  return (
    <div className="page">
      <div className="page-header"><h2>Daily Rates</h2><p>Set buy/sell rates for vendors and mills</p></div>
      <div style={{display:'grid',gridTemplateColumns:'340px 1fr',gap:20,alignItems:'start'}}>
        <div className="card"><div className="card-header"><h3>Set Rate</h3></div>
          <form onSubmit={save}><div className="card-body"><div className="form-grid" style={{gridTemplateColumns:'1fr'}}>
            <div className="form-group"><label>Date</label><input type="date" value={form.rate_date} onChange={e=>{f('rate_date')(e);setDate(e.target.value)}}/></div>
            <div className="form-group"><label>Party Type</label><select value={form.party_type} onChange={f('party_type')}><option value="vendor">Vendor (Buy Rate)</option><option value="mill">Mill (Sell Rate)</option></select></div>
            <div className="form-group"><label>{form.party_type==='vendor'?'Vendor':'Mill'}</label><select value={form.party_id} onChange={f('party_id')} required><option value="">Select…</option>{parties.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></div>
            <div className="form-group"><label>Rate (?/kg)</label><input type="number" step="0.01" value={form.rate_per_kg} onChange={f('rate_per_kg')} required placeholder="0.00"/></div>
            <button type="submit" className="btn btn-primary" disabled={saving} style={{justifyContent:'center'}}>{saving?'Saving…':'Save Rate'}</button>
          </div></div></form>
        </div>
        <div className="card">
          <div className="card-header"><h3>Rates for {date}</h3><input type="date" value={date} onChange={e=>setDate(e.target.value)} style={{width:'auto'}}/></div>
          <div className="table-wrap">
            {loading?<div className="loading-center"><div className="spinner"/></div>:rates.length===0?<div className="empty-state"><p>No rates set for this date</p></div>:
              <table><thead><tr><th>Type</th><th>Party</th><th>Rate (?/kg)</th><th>Material</th></tr></thead><tbody>
                {rates.map(r=><tr key={r.id}><td><span className={`badge ${r.party_type==='vendor'?'badge-orange':'badge-blue'}`}>{r.party_type==='vendor'?'Buy':'Sell'}</span></td><td><strong>{r.party_name||r.party_id}</strong></td><td><strong>?{Number(r.rate_per_kg).toFixed(2)}</strong></td><td>{r.material_type}</td></tr>)}
              </tbody></table>}
          </div>
        </div>
      </div>
    </div>
  )
}
