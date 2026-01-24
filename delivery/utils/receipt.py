from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime
from io import BytesIO
import json
from django.templatetags.static import static
import os



def build_modern_invoice(order):

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "HeiseiMin-W3"
    styles["Heading3"].fontName = "HeiseiMin-W3"

    center = ParagraphStyle(name="center", parent=styles["Normal"], alignment=1)
    heading = ParagraphStyle(name="heading", parent=styles["Heading3"], textColor=colors.HexColor("#111827"))

    def header(canvas, doc):
        from django.conf import settings
        logo_path = os.path.join(settings.BASE_DIR, 
                        "static",
                        "images",
                        "logo.png"
                    )

        canvas.saveState()

        # Dark header bar
        canvas.setFillColor(colors.HexColor("#1f2937"))
        canvas.rect(0, A4[1]-90, A4[0], 90, fill=1)

        # LOGO
        # ===== SIZE SETTINGS =====
        LOGO_HEIGHT = 28           # <-- match text visual height
        LOGO_WIDTH = 28            # <-- square look (adjust if needed)

        X_START = 40               # left padding
        Y_BASE = A4[1] - 65 
        canvas.drawImage(
            logo_path,
            X_START,
            Y_BASE - (LOGO_HEIGHT/2),      # position
            width=LOGO_WIDTH,
            height=LOGO_HEIGHT,       # adjust width
            preserveAspectRatio=True,
            mask="auto"        # transparent background support
        )

         # ===== BRAND TEXT NEXT TO LOGO =====
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 22)
        canvas.drawString(
            X_START + LOGO_WIDTH + 12,   # <-- 12px spacing
            Y_BASE - 8,                  # <-- aligns baseline visually
            "BuyZone"
        )

        # Subtitle text
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 11)
        canvas.drawString(
            X_START + LOGO_WIDTH + 12,
            Y_BASE - 28,
            "Modern Retail Invoice"
        )

        canvas.restoreState()



    story = []
    story.append(Spacer(1, 100))

    # -------- Invoice Meta ----------
    now = datetime.now()

    meta = [
        ["Invoice No", f"INV-{order.oid}"],
        ["Order ID", order.oid],
        ["Booking Date", str(order.BookDate.strftime("%d %b %Y • %I:%M %p"))],
        ["Generated At", now.strftime("%d %b %Y • %I:%M %p")],
        ["Payment", order.paymentstatus],
    ]

    meta_table = Table(meta, colWidths=[150, 300])
    meta_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
    ]))

    story.append(Paragraph("Invoice Details", heading))
    story.append(Spacer(1, 6))
    story.append(meta_table)
    story.append(Spacer(1, 18))

    # -------- Customer ----------
    story.append(Paragraph("Customer Details", heading))
    story.append(Spacer(1, 6))

    customer_table = [
        ["Billing Details", "Shipping Details"],
        [
            f"{order.name}\n{order.address1}\n{order.address2}, {order.city}\n"
            f"State: {order.state}\nPIN: {order.zip_code}\nEmail: {order.email}",
            "Same as Billing Address"
        ]
    ]

    cust = Table(customer_table, colWidths=[260, 260])
    cust.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('BOX', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))

    story.append(cust)
    story.append(Spacer(1, 18))

    # -------- Items ----------
    story.append(Paragraph("Order Summary", heading))
    story.append(Spacer(1, 6))

    data = [["Product Name","Size","Qty","Old Price","New Price","Discount","Total"]]

    items = json.loads(order.items_json)

    for pid, v in items.items():
        qty, name, price, mrp, discount, size = v
        total = int(price) * int(qty)

        data.append([
            name,
            size,
            qty,
            f"{mrp}",
            f"₹{price}",
            f"{discount}",
            f"₹{total}"
        ])

    item_table = Table(
        data,
        colWidths=[150, 45, 40, 75, 75, 70, 70]
    )
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'HeiseiMin-W3'),

        # nicer spacing
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))

    story.append(item_table)
    story.append(Spacer(1, 16))

    # -------- Totals ----------
    totals = [
        ["Subtotal", f"₹{order.amount}"],
        ["Delivery", "₹0"],
        ["Grand Total", f"₹{order.amount}"],
    ]

    total_table = Table(totals, colWidths=[350, 120])
    total_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,2), (-1,2), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,-1), 'HeiseiMin-W3'),
    ]))

    story.append(total_table)
    story.append(Spacer(1, 30))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Thank you for shopping with BuyZone", center))
    story.append(Paragraph("This invoice was generated electronically.", center))

    doc.build(story, onFirstPage=header, onLaterPages=header)

    buffer.seek(0)
    return buffer
