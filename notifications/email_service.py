"""
Email notification service for booking confirmations and cancellations
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_booking_confirmation_email(booking):
    """
    Send confirmation email to guest when booking is confirmed by staff
    
    Args:
        booking: RoomBooking instance
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        # Email subject
        subject = f"✅ Booking Confirmed - {booking.hotel.name} - {booking.confirmation_number}"
        
        # Email content
        guest_name = booking.guest_name
        hotel_name = booking.hotel.name
        check_in = booking.check_in.strftime('%B %d, %Y')
        check_out = booking.check_out.strftime('%B %d, %Y')
        nights = booking.nights
        room_type = booking.room_type.name if booking.room_type else 'Room'
        total_amount = f"{booking.currency} {booking.total_amount:.2f}"
        
        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .booking-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
                .detail-row:last-child {{ border-bottom: none; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; }}
                .total {{ background: #e8f5e8; padding: 15px; border-radius: 8px; text-align: center; font-size: 18px; font-weight: bold; }}
                .footer {{ text-align: center; color: #666; margin-top: 30px; font-size: 14px; }}
                .success-icon {{ font-size: 48px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="success-icon">✅</div>
                    <h1>Booking Confirmed!</h1>
                    <p>Your reservation has been confirmed by our staff</p>
                </div>
                
                <div class="content">
                    <p>Dear {guest_name},</p>
                    
                    <p>Great news! Your booking at <strong>{hotel_name}</strong> has been confirmed by our staff. Here are your reservation details:</p>
                    
                    <div class="booking-details">
                        <div class="detail-row">
                            <span class="label">Confirmation Number:</span>
                            <span class="value"><strong>{booking.confirmation_number}</strong></span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Hotel:</span>
                            <span class="value">{hotel_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Room Type:</span>
                            <span class="value">{room_type}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Check-in:</span>
                            <span class="value">{check_in}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Check-out:</span>
                            <span class="value">{check_out}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Duration:</span>
                            <span class="value">{nights} night(s)</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Guests:</span>
                            <span class="value">{booking.adults} adult(s){f", {booking.children} child(ren)" if booking.children > 0 else ""}</span>
                        </div>
                    </div>
                    
                    <div class="total">
                        Total Amount: {total_amount}
                    </div>
                    
                    <p><strong>Important Notes:</strong></p>
                    <ul>
                        <li>Please arrive at the hotel on your check-in date</li>
                        <li>Bring a valid ID and this confirmation email</li>
                        <li>Standard check-in time is 3:00 PM, check-out is 11:00 AM</li>
                        <li>Contact the hotel directly for any special requests</li>
                    </ul>
                    
                    <p>We look forward to welcoming you to {hotel_name}!</p>
                    
                    <div class="footer">
                        <p>This is an automated confirmation email from {hotel_name}</p>
                        <p>If you have any questions, please contact the hotel directly</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_content = f"""
        BOOKING CONFIRMED - {hotel_name}
        
        Dear {guest_name},
        
        Your booking has been confirmed! Here are your reservation details:
        
        Confirmation Number: {booking.confirmation_number}
        Hotel: {hotel_name}
        Room Type: {room_type}
        Check-in: {check_in}
        Check-out: {check_out}
        Duration: {nights} night(s)
        Guests: {booking.adults} adult(s){f", {booking.children} child(ren)" if booking.children > 0 else ""}
        Total Amount: {total_amount}
        
        Please bring a valid ID and this confirmation email when you arrive.
        
        We look forward to welcoming you!
        
        {hotel_name}
        """
        
        # Send email
        result = send_mail(
            subject=subject,
            message=plain_content,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[booking.guest_email],
            html_message=html_content,
            fail_silently=False
        )
        
        logger.info(f"📧 Confirmation email sent to {booking.guest_email} for booking {booking.booking_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send confirmation email for booking {booking.booking_id}: {e}")
        return False


def send_booking_cancellation_email(booking, reason=None, cancelled_by=None):
    """
    Send cancellation email to guest when booking is cancelled
    
    Args:
        booking: RoomBooking instance
        reason: Cancellation reason
        cancelled_by: Who cancelled the booking
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        # Email subject
        subject = f"❌ Booking Cancelled - {booking.hotel.name} - {booking.confirmation_number}"
        
        # Email content
        guest_name = booking.guest_name
        hotel_name = booking.hotel.name
        check_in = booking.check_in.strftime('%B %d, %Y')
        check_out = booking.check_out.strftime('%B %d, %Y')
        room_type = booking.room_type.name if booking.room_type else 'Room'
        total_amount = f"{booking.currency} {booking.total_amount:.2f}"
        cancellation_reason = reason or 'No specific reason provided'
        cancelled_by_text = cancelled_by or 'Hotel Staff'
        
        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .booking-details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
                .detail-row:last-child {{ border-bottom: none; }}
                .label {{ font-weight: bold; color: #555; }}
                .value {{ color: #333; }}
                .cancellation-box {{ background: #ffe6e6; padding: 15px; border-radius: 8px; border-left: 4px solid #ff4757; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; margin-top: 30px; font-size: 14px; }}
                .cancel-icon {{ font-size: 48px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="cancel-icon">❌</div>
                    <h1>Booking Cancelled</h1>
                    <p>Your reservation has been cancelled</p>
                </div>
                
                <div class="content">
                    <p>Dear {guest_name},</p>
                    
                    <p>We regret to inform you that your booking at <strong>{hotel_name}</strong> has been cancelled.</p>
                    
                    <div class="cancellation-box">
                        <p><strong>Cancellation Details:</strong></p>
                        <p><strong>Reason:</strong> {cancellation_reason}</p>
                        <p><strong>Cancelled by:</strong> {cancelled_by_text}</p>
                    </div>
                    
                    <div class="booking-details">
                        <h3>Cancelled Booking Details:</h3>
                        <div class="detail-row">
                            <span class="label">Confirmation Number:</span>
                            <span class="value">{booking.confirmation_number}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Hotel:</span>
                            <span class="value">{hotel_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Room Type:</span>
                            <span class="value">{room_type}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Check-in:</span>
                            <span class="value">{check_in}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Check-out:</span>
                            <span class="value">{check_out}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">Amount:</span>
                            <span class="value">{total_amount}</span>
                        </div>
                    </div>
                    
                    <p><strong>What happens next:</strong></p>
                    <ul>
                        <li>If you made a payment, refunds will be processed according to our policy</li>
                        <li>You may contact the hotel directly for rebooking options</li>
                        <li>We apologize for any inconvenience caused</li>
                    </ul>
                    
                    <p>If you have any questions about this cancellation, please contact {hotel_name} directly.</p>
                    
                    <div class="footer">
                        <p>This is an automated cancellation email from {hotel_name}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_content = f"""
        BOOKING CANCELLED - {hotel_name}
        
        Dear {guest_name},
        
        Your booking has been cancelled.
        
        Cancellation Reason: {cancellation_reason}
        Cancelled by: {cancelled_by_text}
        
        Cancelled Booking Details:
        Confirmation Number: {booking.confirmation_number}
        Hotel: {hotel_name}
        Room Type: {room_type}
        Check-in: {check_in}
        Check-out: {check_out}
        Amount: {total_amount}
        
        If you made a payment, refunds will be processed according to our policy.
        
        For questions, please contact the hotel directly.
        
        {hotel_name}
        """
        
        # Send email
        result = send_mail(
            subject=subject,
            message=plain_content,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[booking.guest_email],
            html_message=html_content,
            fail_silently=False
        )
        
        logger.info(f"📧 Cancellation email sent to {booking.guest_email} for booking {booking.booking_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send cancellation email for booking {booking.booking_id}: {e}")
        return False