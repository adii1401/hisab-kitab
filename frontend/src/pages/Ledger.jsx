import { useEffect, useState } from 'react'
import api from '../utils/api'
export default function Ledger() {
  const [vendors,setVendors]=useState([]); const [mills,setMills]=useState([])
  const [selected,setSelected]=useState({type:'vendor',id:''}); const [ledger,setLedger]=useState(null); const [loading,setLoading]=useState(false)
  useEffect(()=>{Promise.all([api.get('/vendors'),api.get('/mills')]).then(([v,m])=>{setVendors(v.data);setMills(m.data)})}, [])
  const load = async () => {
    if(!selected.id) return; setLoading(true)
    try { const r=await api.get(`/ledger/summary?party_type=${selected.type}&party_id=${selected.id}`); setLedger(r.data) }
    catch { setLedger(null) } finally { setLoading(false) }
  }
  const parties = selected.type==='vendor'?vendors:mills
  const fmt = n => n!==undefined&&n!==null?`?${Number(n).toLocaleString('en-IN',{maximumFractionDigits:2})}`:'—'
  return (
    <div className="page">
      <div className="page-header"><h2>Ledger</h2><p>Vendor and mill account statements</p></div>
      <div className="card" style={{marginBottom:20}}><div className="card-body"><div className="filters-bar">
        <select value={selected.type} onChange={e=>setSelected({type:e.target.value,id:''})}><option value="vendor">Vendor</option><option value="mill">Mill</option></select>
        <select value={selected.id} onChange={e=>setSelected(p=>({...p,id:e.target.value}))}><option value="">Select {selected.type}…</option>{parties.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select>
        <button className="btn btn-primary" onClick={load} disabled={!selected.id||loading}>{loading?'Loading…':'View Ledger'}</button>
      </div></div></div>
      {ledger&&<>
        <div className="stats-grid" style={{marginBottom:20}}>
          <div className="stat-card accent"><div className="stat-label">Total Trips</div><div className="stat-value">{ledger.total_trips||0}</div></div>
          <div className="stat-card"><div className="stat-label">Total Amount</div><div className="stat-value" style={{fontSize:'1.4rem'}}>{fmt(ledger.total_amount)}</div></div>
          <div className="stat-card green"><div className="stat-label">Total Paid</div><div className="stat-value" style={{fontSize:'1.4rem'}}>{fmt(ledger.total_paid)}</div></div>
          <div className="stat-card gold"><div className="stat-label">Balance Due</div><div className="stat-value" style={{fontSize:'1.4rem'}}>{fmt(ledger.balance_due)}</div></div>
        </div>
        <div className="card"><div className="card-header"><h3>Transactions</h3></div><div className="table-wrap">
          {!ledger.entries||ledger.entries.length===0?<div className="empty-state"><p>No transactions found</p></div>:
            <table><thead><tr><th>Date</th><th>Description</th><th>Debit</th><th>Credit</th><th>Balance</th></tr></thead><tbody>
              {ledger.entries.map((e,i)=><tr key={i}><td>{e.date}</td><td>{e.description}</td><td className="amt-negative">{e.debit?fmt(e.debit):'—'}</td><td className="amt-positive">{e.credit?fmt(e.credit):'—'}</td><td>{fmt(e.balance)}</td></tr>)}
            </tbody></table>}
        </div></div>
      </>}
      {!ledger&&!loading&&<div className="card"><div className="empty-state" style={{padding:'80px 20px'}}><p>Select a vendor or mill to view their ledger</p></div></div>}
    </div>
  )
}
