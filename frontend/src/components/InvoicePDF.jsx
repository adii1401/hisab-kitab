import React from 'react';

const InvoicePDF = React.forwardRef(({ invoiceData }, ref) => {
  if (!invoiceData) return null;

  // 1. FIX: Calculate the exact math on the frontend to avoid the 0.00 error
  const docDate = new Date(invoiceData.trip_date).toLocaleDateString('en-GB').replace(/\//g, '-');
  const qty = Number(invoiceData.loaded_weight_kg) || 0;
  const rate = Number(invoiceData.mill_default_rate_per_kg) || 0;
  const totalAmt = Number(invoiceData.mill_total_amount) || 0;
  
  const taxableAmt = qty * rate;
  const gstAmt = totalAmt - taxableAmt;

  // 2. FIX: Bulletproof inline styles so browsers cannot strip the borders
  const b = "1px solid black";
  const th = { border: b, padding: '4px', backgroundColor: '#e5e7eb', fontWeight: 'bold', textAlign: 'center' };
  const td = { border: b, padding: '4px', textAlign: 'center' };

  return (
    <div ref={ref} style={{ padding: '40px', fontFamily: 'sans-serif', fontSize: '11px', color: 'black', width: '210mm', boxSizing: 'border-box' }}>
      
      {/* HEADER ROW */}
      <table style={{ width: '100%', marginBottom: '10px' }}>
        <tbody>
          <tr>
            <td style={{ width: '120px' }}>
              <div style={{ width: '100px', height: '100px', border: b, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f9fafb' }}>
                <span style={{ fontSize: '9px', color: '#6b7280', textAlign: 'center' }}>QR CODE<br/>(IRN Generated)</span>
              </div>
            </td>
            <td style={{ textAlign: 'right', verticalAlign: 'top' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 'bold', margin: '0 0 5px 0', textTransform: 'uppercase' }}>
                {invoiceData.vendor?.name || 'GUPTA TRADING COMPANY'}
              </h2>
              <p style={{ margin: 0, fontWeight: 'bold' }}>GSTIN: {invoiceData.vendor?.gstin || '10AIHPG2379K1ZD'}</p>
            </td>
          </tr>
        </tbody>
      </table>

      {/* SECTION 1 & 2: E-INVOICE & TRANSACTION DETAILS */}
      <table style={{ width: '100%', borderCollapse: 'collapse', border: b, marginBottom: '10px' }}>
        <tbody>
          <tr>
            <td style={{ width: '50%', borderRight: b, verticalAlign: 'top' }}>
              <div style={{ borderBottom: b, padding: '4px', backgroundColor: '#e5e7eb', fontWeight: 'bold' }}>1. e-Invoice Details</div>
              <div style={{ padding: '4px', lineHeight: '1.6' }}>
                <strong>IRN:</strong> {invoiceData.irn || 'Not Generated Yet'}<br/>
                <strong>Ack. No:</strong> {invoiceData.ack_no || '-'}<br/>
                <strong>Ack. Date:</strong> {invoiceData.ack_date || '-'}
              </div>
            </td>
            <td style={{ width: '50%', verticalAlign: 'top' }}>
              <div style={{ borderBottom: b, padding: '4px', backgroundColor: '#e5e7eb', fontWeight: 'bold' }}>2. Transaction Details</div>
              <div style={{ padding: '4px', lineHeight: '1.6' }}>
                <table style={{ width: '100%' }}>
                  <tbody>
                    <tr>
                      <td style={{ width: '50%' }}>
                        <strong>Supply Type:</strong> B2B<br/>
                        <strong>Document Type:</strong> Tax Invoice<br/>
                        <strong>Document No:</strong> {invoiceData.eway_bill_no || invoiceData.invoice_no}<br/>
                        <strong>Document Date:</strong> {docDate}
                      </td>
                      <td style={{ width: '50%', verticalAlign: 'top' }}>
                        <strong>IGST Applicable:</strong> {invoiceData.gst_percent > 0 ? 'Yes' : 'No'}<br/>
                        <strong>Place of Supply:</strong> {invoiceData.ship_to_pincode ? `${invoiceData.ship_to_pincode}` : 'Standard'}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      {/* SECTION 3: PARTY DETAILS */}
      <table style={{ width: '100%', borderCollapse: 'collapse', border: b, marginBottom: '10px' }}>
        <tbody>
          <tr>
            <td colSpan="2" style={{ borderBottom: b, padding: '4px', backgroundColor: '#e5e7eb', fontWeight: 'bold' }}>3. Party Details</td>
          </tr>
          <tr>
            <td style={{ width: '50%', borderRight: b, padding: '6px', verticalAlign: 'top' }}>
              <div style={{ fontWeight: 'bold', textDecoration: 'underline', marginBottom: '4px' }}>Supplier</div>
              <strong>GSTIN:</strong> {invoiceData.vendor?.gstin || '10AIHPG2379K1ZD'}<br/>
              <strong style={{ fontSize: '12px' }}>{invoiceData.vendor?.name || 'GUPTA TRADING COMPANY'}</strong><br/>
              <div style={{ whiteSpace: 'pre-wrap', marginTop: '2px' }}>{invoiceData.vendor?.address || 'rama bhawan ramna road\ngaya\n823001 BIHAR'}</div>
            </td>
            <td style={{ width: '50%', padding: '6px', verticalAlign: 'top' }}>
              <div style={{ fontWeight: 'bold', textDecoration: 'underline', marginBottom: '4px' }}>Recipient</div>
              <strong>GSTIN:</strong> {invoiceData.mill?.gstin || 'URD'}<br/>
              <strong style={{ fontSize: '12px' }}>{invoiceData.mill?.name || 'Unknown Buyer'}</strong><br/>
              <div style={{ whiteSpace: 'pre-wrap', marginTop: '2px' }}>{invoiceData.mill?.address || '-'}</div>
              <div style={{ marginTop: '4px' }}><strong>Place of Supply:</strong> {invoiceData.mill?.city || 'Uttar Pradesh'}</div>
            </td>
          </tr>
        </tbody>
      </table>

      {/* SECTION 4: GOODS TABLE */}
      <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>4. Details of Goods / Services</div>
      <table style={{ width: '100%', borderCollapse: 'collapse', border: b, marginBottom: '10px' }}>
        <thead>
          <tr>
            <th style={th}>SlNo</th>
            <th style={{...th, textAlign: 'left'}}>Item Description</th>
            <th style={th}>HSN Code</th>
            <th style={th}>Quantity</th>
            <th style={th}>Unit</th>
            <th style={th}>Unit Price(Rs)</th>
            <th style={th}>Discount</th>
            <th style={th}>Taxable Amount</th>
            <th style={th}>Tax Rate</th>
            <th style={th}>Other</th>
            <th style={th}>Total</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={td}>1</td>
            <td style={{...td, textAlign: 'left', fontWeight: 'bold'}}>Scrap old waste kraft paper</td>
            <td style={td}>{invoiceData.hsn_code || '47079000'}</td>
            <td style={td}>{qty}</td>
            <td style={td}>KGS</td>
            <td style={td}>{rate.toFixed(2)}</td>
            <td style={td}>0.00</td>
            <td style={{...td, fontWeight: 'bold'}}>{taxableAmt.toFixed(2)}</td>
            <td style={td}>{Number(invoiceData.gst_percent).toFixed(2)}%</td>
            <td style={td}>0.00</td>
            <td style={{...td, fontWeight: 'bold'}}>{totalAmt.toFixed(2)}</td>
          </tr>
        </tbody>
      </table>

      {/* SECTION 5: TAX TOTALS TABLE */}
      <table style={{ width: '100%', borderCollapse: 'collapse', border: b, marginBottom: '30px' }}>
        <thead>
          <tr>
            <th style={th}>Tax'ble Amt</th>
            <th style={th}>CGST Amt</th>
            <th style={th}>SGST Amt</th>
            <th style={th}>IGST Amt</th>
            <th style={th}>CESS Amt</th>
            <th style={th}>State CESS</th>
            <th style={th}>Discount</th>
            <th style={th}>Other</th>
            <th style={th}>Round off</th>
            <th style={th}>Total Inv. Amt</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{...td, fontWeight: 'bold'}}>{taxableAmt.toFixed(2)}</td>
            <td style={td}>0.00</td>
            <td style={td}>0.00</td>
            <td style={td}>{gstAmt.toFixed(2)}</td>
            <td style={td}>0.00</td>
            <td style={td}>0.00</td>
            <td style={td}>0.00</td>
            <td style={td}>0.00</td>
            <td style={td}>0.00</td>
            <td style={{...td, fontWeight: 'bold', fontSize: '13px'}}>{totalAmt.toFixed(2)}</td>
          </tr>
        </tbody>
      </table>

      {/* FOOTER */}
      <table style={{ width: '100%', marginTop: '40px' }}>
        <tbody>
          <tr>
            <td style={{ width: '50%', verticalAlign: 'bottom' }}>
              <div style={{ marginBottom: '4px' }}><strong>Generated By:</strong> {invoiceData.vendor?.gstin || '10AIHPG2379K1ZD'}</div>
              <div><strong>Print Date:</strong> {new Date().toLocaleString('en-GB')}</div>
            </td>
            <td style={{ width: '50%', textAlign: 'right' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '50px' }}>For {invoiceData.vendor?.name || 'GUPTA TRADING COMPANY'}</div>
              <div style={{ borderTop: b, width: '200px', float: 'right', paddingTop: '4px' }}>Authorized Signatory</div>
            </td>
          </tr>
        </tbody>
      </table>

    </div>
  );
});

export default InvoicePDF;