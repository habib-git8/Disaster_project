import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.conf import settings

def generate_donation_receipt(donation):
    """
    Generates a PDF receipt for a donation and returns the file path.
    
    Args:
        donation (Donation): The donation instance.
    
    Returns:
        str: Path to the generated PDF file.
    """
    # Define receipt directory inside media folder
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        static_base = settings.STATICFILES_DIRS[0]  # Get the first static directory
    else:
        static_base = settings.BASE_DIR  # Fallback to BASE_DIR

    # Define the receipts directory inside static
    receipt_dir = os.path.join(static_base, 'receipts')

    # Create the directory if it does not exist
    os.makedirs(receipt_dir, exist_ok=True)

    # Define receipt filename
    receipt_filename = f"receipt_{donation.id}.pdf"
    receipt_path = os.path.join(receipt_dir, receipt_filename)

    # Create a PDF canvas
    c = canvas.Canvas(receipt_path, pagesize=A4)
    c.setFont("Helvetica", 12)

    # Add receipt content
    c.drawString(100, 750, "Donation Receipt")
    c.drawString(100, 730, f"Receipt ID: {donation.id}")
    c.drawString(100, 710, f"Donor: {donation.user.username} ({donation.user.email})")
    c.drawString(100, 690, f"Amount Donated: ${donation.amount}")
    c.drawString(100, 670, f"Donation Date: {donation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(100, 650, f"Donated to: {donation.post.title}")

    # Sign-off
    c.drawString(100, 620, "Thank you for your generous donation!")
    c.drawString(100, 600, "Disaster Connect Team")

    # Save PDF
    c.save()

    return receipt_path
