import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

from app.core.config import settings

W, H = A4
TEAL = colors.HexColor("#0F6E56")
LIGHT_TEAL = colors.HexColor("#E1F5EE")
GRAY = colors.HexColor("#888780")
LIGHT_GRAY = colors.HexColor("#F1EFE8")
WHITE = colors.white


def _ensure_dir(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _styles():
    return {
        "title": ParagraphStyle("title", fontSize=16, fontName="Helvetica-Bold", textColor=TEAL, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontSize=11, fontName="Helvetica-Bold", spaceAfter=2),
        "normal": ParagraphStyle("normal", fontSize=9, fontName="Helvetica", leading=13),
        "small": ParagraphStyle("small", fontSize=8, fontName="Helvetica", textColor=GRAY, leading=11),
        "right": ParagraphStyle("right", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT),
        "bold": ParagraphStyle("bold", fontSize=9, fontName="Helvetica-Bold"),
        "center": ParagraphStyle("center", fontSize=9, fontName="Helvetica", alignment=TA_CENTER),
    }


def generate_gst_invoice(*, output_path, invoice_no, invoice_date, mill_name, mill_gstin,
                          mill_address, vehicle_no, eway_bill_no, hsn_code, gst_percent,
                          lines, trip_date):
    _ensure_dir(output_path)
    styles = _styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    header_data = [[
        [Paragraph(settings.COMPANY_NAME, styles["title"]),
         Paragraph(f"GSTIN: {settings.COMPANY_GSTIN}", styles["normal"]),
         Paragraph(settings.COMPANY_ADDRESS, styles["normal"]),
         Paragraph(f"Ph: {settings.COMPANY_PHONE}", styles["normal"])],
        [Paragraph("TAX INVOICE", ParagraphStyle("ti", fontSize=11, fontName="Helvetica-Bold",
                                                  textColor=TEAL, alignment=TA_RIGHT)),
         Paragraph(f"No: {invoice_no}", ParagraphStyle("r", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT)),
         Paragraph(f"Date: {invoice_date.strftime('%d %b %Y')}", ParagraphStyle("r2", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT))]
    ]]
    ht = Table(header_data[0], colWidths=[10*cm, 8*cm])
    ht.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0)]))
    story.append(ht)
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=8))

    bt = Table([[
        [Paragraph("<b>Bill To:</b>", styles["h2"]),
         Paragraph(mill_name, styles["normal"]),
         Paragraph(f"GSTIN: {mill_gstin or 'N/A'}", styles["normal"]),
         Paragraph(mill_address or "", styles["small"])],
        [Paragraph(f"<b>Trip date:</b> {trip_date.strftime('%d %b %Y')}", styles["normal"]),
         Paragraph(f"<b>Vehicle:</b> {vehicle_no}", styles["normal"]),
         Paragraph(f"<b>E-way bill:</b> {eway_bill_no or 'N/A'}", styles["normal"]),
         Paragraph(f"<b>HSN:</b> {hsn_code}", styles["normal"])]
    ]], colWidths=[10*cm, 8*cm])
    bt.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0)]))
    story.append(bt)
    story.append(Spacer(1, 0.4*cm))

    line_data = [["Material / Description", "HSN", "Qty (kg)", "Rate (Rs/kg)", "Amount (Rs)"]]
    base_total = Decimal("0")
    for line in lines:
        qty, rate = line["qty_kg"], line["rate"]
        amount = qty * rate
        base_total += amount
        line_data.append([line["material"], hsn_code, f"{qty:,.2f}", f"{rate:,.4f}", f"{amount:,.2f}"])

    gst_amount = base_total * gst_percent / 100
    grand_total = base_total + gst_amount
    half_gst = gst_percent / 2
    line_data.append(["", "", "", "Taxable amount", f"{base_total:,.2f}"])
    line_data.append(["", "", "", f"CGST @ {half_gst}%", f"{gst_amount/2:,.2f}"])
    line_data.append(["", "", "", f"SGST @ {half_gst}%", f"{gst_amount/2:,.2f}"])
    line_data.append(["", "", "", "TOTAL", f"{grand_total:,.2f}"])

    n = len(lines)
    it = Table(line_data, colWidths=[6*cm, 1.8*cm, 2.5*cm, 2.5*cm, 3.4*cm])
    it.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),TEAL), ("TEXTCOLOR",(0,0),(-1,0),WHITE),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),9),
        ("ALIGN",(2,0),(-1,-1),"RIGHT"), ("ALIGN",(0,0),(1,-1),"LEFT"),
        ("ROWBACKGROUNDS",(0,1),(-1,n),[LIGHT_GRAY, WHITE]),
        ("FONTNAME",(3,n+1),(-1,-1),"Helvetica-Bold"),
        ("LINEABOVE",(0,n+1),(-1,n+1),0.5,GRAY),
        ("BACKGROUND",(3,-1),(-1,-1),TEAL), ("TEXTCOLOR",(3,-1),(-1,-1),WHITE),
        ("FONTNAME",(3,-1),(-1,-1),"Helvetica-Bold"),
        ("GRID",(0,0),(-1,n),0.3,GRAY),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story.append(it)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"<b>Amount in words:</b> {_amount_words(grand_total)} only", styles["small"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"For <b>{settings.COMPANY_NAME}</b>", styles["normal"]))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("Authorised Signatory", styles["small"]))
    doc.build(story)
    return output_path


def generate_vendor_receipt(*, output_path, receipt_no, receipt_date, vendor_name,
                             vendor_address, vehicle_no, trip_date, mill_name, lines,
                             vendor_rate_per_kg, advance_paid, balance_to_pay,
                             net_weight_kg, vendor_total):
    _ensure_dir(output_path)
    styles = _styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    ht = Table([[
        [Paragraph(settings.COMPANY_NAME, styles["title"]),
         Paragraph(f"GSTIN: {settings.COMPANY_GSTIN}", styles["normal"]),
         Paragraph(settings.COMPANY_ADDRESS, styles["normal"])],
        [Paragraph("PAYMENT RECEIPT", ParagraphStyle("pr", fontSize=11, fontName="Helvetica-Bold",
                                                      textColor=TEAL, alignment=TA_RIGHT)),
         Paragraph(f"No: {receipt_no}", ParagraphStyle("r", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT)),
         Paragraph(f"Date: {receipt_date.strftime('%d %b %Y')}", ParagraphStyle("r2", fontSize=9, fontName="Helvetica", alignment=TA_RIGHT))]
    ]], colWidths=[10*cm, 8*cm])
    ht.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0)]))
    story.append(ht)
    story.append(HRFlowable(width="100%", thickness=1.5, color=TEAL, spaceAfter=8))

    story.append(Paragraph(f"<b>Vendor:</b> {vendor_name}", styles["normal"]))
    story.append(Paragraph(f"<b>Vehicle:</b> {vehicle_no} | <b>Trip date:</b> {trip_date.strftime('%d %b %Y')} | <b>Mill:</b> {mill_name}", styles["normal"]))
    story.append(Spacer(1, 0.4*cm))

    receipt_data = [["Material", "Net Weight (kg)", "Mill Rate (Rs/kg)", "Amount (Rs)"]]
    for line in lines:
        amt = line["qty_kg"] * line["rate"]
        receipt_data.append([line["material"], f"{line['qty_kg']:,.2f}", f"{line['rate']:,.4f}", f"{amt:,.2f}"])
    rt = Table(receipt_data, colWidths=[7*cm, 3*cm, 3*cm, 3.2*cm])
    rt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),LIGHT_TEAL), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9), ("ALIGN",(1,0),(-1,-1),"RIGHT"),
        ("GRID",(0,0),(-1,-1),0.3,GRAY),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    story.append(rt)
    story.append(Spacer(1, 0.4*cm))

    calc_data = [
        [f"Net weight: {net_weight_kg:,.2f} kg x Rs {vendor_rate_per_kg}/kg", f"Rs {vendor_total:,.2f}"],
        ["Less: Advance paid at pickup", f"- Rs {advance_paid:,.2f}"],
        ["Balance payable to you", f"Rs {balance_to_pay:,.2f}"],
    ]
    ct = Table(calc_data, colWidths=[11*cm, 5.2*cm])
    ct.setStyle(TableStyle([
        ("FONTSIZE",(0,0),(-1,-1),9), ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
        ("BACKGROUND",(0,-1),(-1,-1),TEAL), ("TEXTCOLOR",(0,-1),(-1,-1),WHITE),
        ("LINEABOVE",(0,-1),(-1,-1),0.5,GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story.append(ct)
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"For <b>{settings.COMPANY_NAME}</b>", styles["normal"]))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("Authorised Signatory", styles["small"]))
    doc.build(story)
    return output_path


def _amount_words(amount: Decimal) -> str:
    ones = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine",
            "Ten","Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen",
            "Seventeen","Eighteen","Nineteen"]
    tens = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]
    def below100(n):
        return ones[n] if n < 20 else tens[n//10]+(" "+ones[n%10] if n%10 else "")
    def below1000(n):
        return ones[n//100]+" Hundred"+(" "+below100(n%100) if n%100 else "") if n>=100 else below100(n)
    n = int(amount)
    parts = []
    for div, label in [(10000000,"Crore"),(100000,"Lakh"),(1000,"Thousand")]:
        if n >= div:
            parts.append(below1000(n//div)+" "+label)
            n %= div
    if n: parts.append(below1000(n))
    return (" ".join(parts) if parts else "Zero") + " Rupees"
