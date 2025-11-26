from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os

class InvoiceGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center alignment
        )
        
    def generate_pdf_invoice(self, invoice_data, filename=None):
        """Generate PDF invoice"""
        if not filename:
            filename = f"invoice_{invoice_data['invoice_number']}.pdf"
        
        # Create the PDF document
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph("CAR PRICE PREDICTOR", self.title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Invoice header
        invoice_header = Paragraph(f"<b>Invoice #{invoice_data['invoice_number']}</b>", self.styles['Heading2'])
        story.append(invoice_header)
        story.append(Spacer(1, 10))
        
        # Date
        date_para = Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal'])
        story.append(date_para)
        story.append(Spacer(1, 20))
        
        # Customer details
        customer_header = Paragraph("<b>Bill To:</b>", self.styles['Heading3'])
        story.append(customer_header)
        
        customer_details = f"""
        {invoice_data['customer_name']}<br/>
        Email: {invoice_data['customer_email']}<br/>
        Phone: {invoice_data.get('customer_phone', 'N/A')}
        """
        customer_para = Paragraph(customer_details, self.styles['Normal'])
        story.append(customer_para)
        story.append(Spacer(1, 20))
        
        # Service details
        service_header = Paragraph("<b>Service Details:</b>", self.styles['Heading3'])
        story.append(service_header)
        
        # Create table for service details
        service_data = [
            ['Description', 'Details'],
            ['Car', f"{invoice_data['car_brand']} {invoice_data['car_model']} ({invoice_data['car_year']})"],
            ['Condition', invoice_data['car_condition'].title()],
            ['Kilometers Driven', f"{invoice_data['kilometers_driven']:,} km"],
            ['City', invoice_data['city'].title()],
            ['Predicted Price', f"₹{invoice_data['predicted_price']:,}"],
        ]
        
        service_table = Table(service_data, colWidths=[2*inch, 3*inch])
        service_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(service_table)
        story.append(Spacer(1, 30))
        
        # Billing details
        billing_header = Paragraph("<b>Billing Summary:</b>", self.styles['Heading3'])
        story.append(billing_header)
        
        billing_data = [
            ['Item', 'Amount'],
            ['Car Price Prediction Service', f"₹{invoice_data['service_charge']:,}"],
            ['Total Amount', f"₹{invoice_data['total_amount']:,}"],
        ]
        
        billing_table = Table(billing_data, colWidths=[3*inch, 2*inch])
        billing_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f39c12')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(billing_table)
        story.append(Spacer(1, 40))
        
        # Footer
        footer_text = """
        <b>Thank you for using Car Price Predictor!</b><br/>
        This invoice is for price prediction services only.<br/>
        For any queries, please contact us at support@carpredictor.com
        """
        footer_para = Paragraph(footer_text, self.styles['Normal'])
        story.append(footer_para)
        
        # Build PDF
        doc.build(story)
        return filename
    
    def prepare_invoice_data(self, invoice_row):
        """Prepare invoice data from database row"""
        return {
            'invoice_number': invoice_row['invoice_number'],
            'customer_name': invoice_row['full_name'],
            'customer_email': invoice_row['email'],
            'customer_phone': invoice_row.get('phone', 'N/A'),
            'car_brand': invoice_row['brand'],
            'car_model': invoice_row['model'],
            'car_year': invoice_row['year'],
            'car_condition': invoice_row['car_condition'],
            'kilometers_driven': invoice_row['kilometers_driven'],
            'city': invoice_row['city'],
            'predicted_price': invoice_row['predicted_price'],
            'service_charge': invoice_row['service_charge'],
            'total_amount': invoice_row['total_amount']
        }
