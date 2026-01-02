"""
Workflow & Approval System

Features:
- Multi-level approval workflow (Manager → Finance → Compliance)
- Email notifications for pending approvals
- Dashboard showing approval status
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.database import models


# Approval levels configuration
APPROVAL_LEVELS = {
    1: {"name": "Manager", "threshold": 0},       # All invoices need manager approval
    2: {"name": "Finance", "threshold": 50000},   # Invoices > $50k need finance approval
    3: {"name": "Compliance", "threshold": 100000} # Invoices > $100k need compliance approval
}

# Email configuration (update these with your SMTP settings)
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",  # Set your email
    "sender_password": "",  # Set your app password
    "enabled": False  # Set to True when email is configured
}

# Approver email mapping
APPROVERS = {
    1: {"name": "Manager", "email": "manager@company.com"},
    2: {"name": "Finance Head", "email": "finance@company.com"},
    3: {"name": "Compliance Officer", "email": "compliance@company.com"}
}


def create_approval_request(
    db: Session,
    invoice_id: str,
    invoice_db_id: int = None,
    vendor_name: str = None,
    country: str = None,
    total_amount: float = None,
    fraud_score: float = None
) -> models.InvoiceApproval:
    """
    Create a new approval request for an invoice.
    Determines the required approval level based on amount and risk.
    """
    # Determine required approval level
    required_level = 1  # Default: Manager
    
    if total_amount:
        if total_amount > APPROVAL_LEVELS[3]["threshold"]:
            required_level = 3
        elif total_amount > APPROVAL_LEVELS[2]["threshold"]:
            required_level = 2
    
    # High fraud score requires compliance approval
    if fraud_score and fraud_score >= 70:
        required_level = max(required_level, 3)
    elif fraud_score and fraud_score >= 40:
        required_level = max(required_level, 2)
    
    # Create approval record
    approval = models.InvoiceApproval(
        invoice_id=invoice_id,
        invoice_db_id=invoice_db_id,
        status="pending",
        level=1,  # Start at level 1
        current_approver=APPROVERS[1]["name"],
        vendor_name=vendor_name,
        country=country,
        total_amount=total_amount,
        fraud_score=fraud_score
    )
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    # Send email notification
    send_approval_notification(approval, APPROVERS[1]["email"])
    
    return approval


def approve_invoice(
    db: Session,
    approval_id: int,
    approver_name: str,
    comments: str = None
) -> Dict[str, Any]:
    """
    Approve an invoice at the current level.
    May escalate to next level if required.
    """
    approval = db.query(models.InvoiceApproval).filter(
        models.InvoiceApproval.id == approval_id
    ).first()
    
    if not approval:
        return {"success": False, "error": "Approval request not found"}
    
    if approval.status != "pending":
        return {"success": False, "error": f"Invoice already {approval.status}"}
    
    current_level = approval.level
    
    # Check if higher approval is needed
    needs_higher = False
    if approval.total_amount:
        if current_level < 3 and approval.total_amount > APPROVAL_LEVELS[3]["threshold"]:
            needs_higher = True
        elif current_level < 2 and approval.total_amount > APPROVAL_LEVELS[2]["threshold"]:
            needs_higher = True
    
    if approval.fraud_score:
        if current_level < 3 and approval.fraud_score >= 70:
            needs_higher = True
        elif current_level < 2 and approval.fraud_score >= 40:
            needs_higher = True
    
    if needs_higher:
        # Escalate to next level
        next_level = current_level + 1
        approval.level = next_level
        approval.current_approver = APPROVERS[next_level]["name"]
        approval.comments = (approval.comments or "") + f"\n[{approver_name}] Approved at Level {current_level}. {comments or ''}"
        approval.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Send notification to next approver
        send_approval_notification(approval, APPROVERS[next_level]["email"])
        
        return {
            "success": True,
            "status": "escalated",
            "message": f"Approved at Level {current_level} ({APPROVAL_LEVELS[current_level]['name']}). "
                      f"Escalated to Level {next_level} ({APPROVAL_LEVELS[next_level]['name']}) for final approval.",
            "next_approver": APPROVERS[next_level]["name"]
        }
    else:
        # Final approval
        approval.status = "approved"
        approval.approved_by = approver_name
        approval.approved_at = datetime.utcnow()
        approval.comments = (approval.comments or "") + f"\n[{approver_name}] Final approval. {comments or ''}"
        approval.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "status": "approved",
            "message": f"Invoice fully approved by {approver_name}",
            "approved_at": approval.approved_at.isoformat()
        }


def reject_invoice(
    db: Session,
    approval_id: int,
    rejector_name: str,
    reason: str
) -> Dict[str, Any]:
    """Reject an invoice."""
    approval = db.query(models.InvoiceApproval).filter(
        models.InvoiceApproval.id == approval_id
    ).first()
    
    if not approval:
        return {"success": False, "error": "Approval request not found"}
    
    if approval.status != "pending":
        return {"success": False, "error": f"Invoice already {approval.status}"}
    
    approval.status = "rejected"
    approval.approved_by = rejector_name
    approval.rejection_reason = reason
    approval.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "status": "rejected",
        "message": f"Invoice rejected by {rejector_name}",
        "reason": reason
    }


def get_pending_approvals(db: Session, level: int = None) -> List[Dict]:
    """Get all pending approval requests, optionally filtered by level."""
    query = db.query(models.InvoiceApproval).filter(
        models.InvoiceApproval.status == "pending"
    )
    
    if level:
        query = query.filter(models.InvoiceApproval.level == level)
    
    approvals = query.order_by(models.InvoiceApproval.created_at.desc()).all()
    
    return [
        {
            "id": a.id,
            "invoice_id": a.invoice_id,
            "vendor_name": a.vendor_name,
            "country": a.country,
            "total_amount": a.total_amount,
            "fraud_score": a.fraud_score,
            "level": a.level,
            "level_name": APPROVAL_LEVELS[a.level]["name"],
            "current_approver": a.current_approver,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "waiting_days": (datetime.utcnow() - a.created_at).days if a.created_at else 0
        }
        for a in approvals
    ]


def get_approval_status(db: Session, invoice_id: str) -> Optional[Dict]:
    """Get approval status for a specific invoice."""
    approval = db.query(models.InvoiceApproval).filter(
        models.InvoiceApproval.invoice_id == invoice_id
    ).first()
    
    if not approval:
        return None
    
    return {
        "id": approval.id,
        "invoice_id": approval.invoice_id,
        "status": approval.status,
        "level": approval.level,
        "level_name": APPROVAL_LEVELS[approval.level]["name"],
        "current_approver": approval.current_approver,
        "approved_by": approval.approved_by,
        "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
        "rejection_reason": approval.rejection_reason,
        "comments": approval.comments,
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
        "updated_at": approval.updated_at.isoformat() if approval.updated_at else None
    }


def get_approval_dashboard(db: Session) -> Dict[str, Any]:
    """Get approval workflow dashboard statistics."""
    # Count by status
    pending = db.query(models.InvoiceApproval).filter(
        models.InvoiceApproval.status == "pending"
    ).count()
    
    approved = db.query(models.InvoiceApproval).filter(
        models.InvoiceApproval.status == "approved"
    ).count()
    
    rejected = db.query(models.InvoiceApproval).filter(
        models.InvoiceApproval.status == "rejected"
    ).count()
    
    # Pending by level
    pending_by_level = {}
    for level in [1, 2, 3]:
        count = db.query(models.InvoiceApproval).filter(
            models.InvoiceApproval.status == "pending",
            models.InvoiceApproval.level == level
        ).count()
        pending_by_level[APPROVAL_LEVELS[level]["name"]] = count
    
    # Get pending approvals list
    pending_list = get_pending_approvals(db)
    
    # Overdue approvals (pending > 3 days)
    overdue = [p for p in pending_list if p["waiting_days"] > 3]
    
    return {
        "summary": {
            "total_pending": pending,
            "total_approved": approved,
            "total_rejected": rejected,
            "overdue_count": len(overdue)
        },
        "pending_by_level": pending_by_level,
        "pending_approvals": pending_list[:20],  # Latest 20
        "overdue_approvals": overdue,
        "approval_levels": APPROVAL_LEVELS
    }


def send_approval_notification(approval: models.InvoiceApproval, to_email: str) -> bool:
    """
    Send email notification for pending approval.
    Returns True if email sent successfully.
    """
    if not EMAIL_CONFIG["enabled"]:
        print(f"EMAIL DISABLED: Would send approval notification to {to_email}")
        print(f"  Invoice: {approval.invoice_id}")
        print(f"  Amount: ${approval.total_amount}")
        print(f"  Vendor: {approval.vendor_name}")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = to_email
        msg['Subject'] = f"[ACTION REQUIRED] Invoice Approval Pending - {approval.invoice_id}"
        
        body = f"""
        <html>
        <body>
        <h2>Invoice Approval Required</h2>
        <p>A new invoice requires your approval:</p>
        
        <table border="1" cellpadding="10">
            <tr><td><strong>Invoice ID</strong></td><td>{approval.invoice_id}</td></tr>
            <tr><td><strong>Vendor</strong></td><td>{approval.vendor_name or 'N/A'}</td></tr>
            <tr><td><strong>Country</strong></td><td>{approval.country or 'N/A'}</td></tr>
            <tr><td><strong>Amount</strong></td><td>${approval.total_amount:,.2f}</td></tr>
            <tr><td><strong>Fraud Score</strong></td><td>{approval.fraud_score or 0:.1f}</td></tr>
            <tr><td><strong>Approval Level</strong></td><td>{APPROVAL_LEVELS[approval.level]['name']}</td></tr>
        </table>
        
        <p>Please review and approve/reject this invoice at:</p>
        <p><a href="http://127.0.0.1:8001/approvals/">Invoice Approval Dashboard</a></p>
        
        <p>Or use the API:</p>
        <ul>
            <li>Approve: POST /approvals/{approval.id}/approve</li>
            <li>Reject: POST /approvals/{approval.id}/reject</li>
        </ul>
        
        <p>Thank you,<br>Invoice Processing System</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
        server.send_message(msg)
        server.quit()
        
        print(f"EMAIL SENT: Approval notification to {to_email}")
        return True
        
    except Exception as e:
        print(f"EMAIL ERROR: Failed to send to {to_email}: {str(e)}")
        return False


def configure_email(smtp_server: str, smtp_port: int, sender_email: str, sender_password: str):
    """Configure email settings for notifications."""
    EMAIL_CONFIG["smtp_server"] = smtp_server
    EMAIL_CONFIG["smtp_port"] = smtp_port
    EMAIL_CONFIG["sender_email"] = sender_email
    EMAIL_CONFIG["sender_password"] = sender_password
    EMAIL_CONFIG["enabled"] = True
    print("Email notifications enabled")


def set_approver_email(level: int, name: str, email: str):
    """Set approver details for a specific level."""
    if level in APPROVERS:
        APPROVERS[level]["name"] = name
        APPROVERS[level]["email"] = email
        print(f"Approver Level {level} set to: {name} ({email})")
