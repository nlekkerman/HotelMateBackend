"""
Create GitHub issues for Booking Phase Backend.
"""

import subprocess
import json

# Issue definitions for Booking Phase
issues = [
    {
        "title": "Availability Checker for Hotel Rooms",
        "body": """## Summary
Implement a backend API that checks if room types are available for a given hotel, date range and occupancy.

This will be used by the booking flow before creating any reservation.

## Scope
- New endpoint (example):
  - `GET /api/hotels/<slug>/availability/`
- Input (query params or JSON):
  - check_in_date
  - check_out_date
  - number_of_adults
  - number_of_children (optional)
  - optional room_type filter
- Output:
  - list of room types with:
    - room_type_code
    - room_type_name
    - is_available (bool)
    - available_units (optional)
    - notes/message (e.g. "Last rooms remaining")

## Requirements
- Use existing room inventory / allocation logic (or a simple placeholder if real PMS is not integrated yet).
- Validate that date range is:
  - in the future
  - check_out_date > check_in_date
- Return 400 for invalid input, 404 for invalid hotel slug.

## Acceptance Criteria
- [ ] Request with valid data returns availability status per room type.
- [ ] No booking is created at this stage.
- [ ] Endpoint is safe to call from frontend booking UI.
""",
        "labels": ["backend", "enhancement"]
    },
    {
        "title": "Real-Time Pricing Endpoint for Booking Flow",
        "body": """## Summary
Implement an API that calculates the **actual price** for a stay based on hotel, dates, room type and occupancy.

This should be called after availability is checked and before the booking is confirmed.

## Scope
- New endpoint (example):
  - `POST /api/hotels/<slug>/pricing/quote/`
- Input:
  - room_type_code
  - check_in_date
  - check_out_date
  - number_of_adults
  - number_of_children (optional)
  - optional promotional_code / offer_id
- Output:
  - currency
  - base_amount
  - taxes
  - fees (if any)
  - total_amount
  - breakdown (per night / per room if needed)
  - applied_offer / promo info (if any)

## Requirements
- Implement pricing logic that can be extended later:
  - for now simple per-night base rate is acceptable, but keep structure flexible.
- Pricing must be **recomputed on request**, not reused from the public "from price".
- Input validation and clear error messages (400) for invalid payload.

## Acceptance Criteria
- [ ] Valid request returns a precise total price and breakdown for the stay.
- [ ] Pricing respects dates / length of stay logic.
- [ ] API is ready to be consumed by booking confirmation screen.
""",
        "labels": ["backend", "enhancement"]
    },
    {
        "title": "Booking Creation Endpoint (Reservations)",
        "body": """## Summary
Implement an endpoint to **create a booking/reservation** once availability and pricing have been confirmed.

This is where the reservation is actually stored in our system.

## Scope
- New endpoint (example):
  - `POST /api/hotels/<slug>/bookings/`
- Input (JSON):
  - room_type_code
  - check_in_date
  - check_out_date
  - number_of_adults
  - number_of_children (optional)
  - guest details:
    - first_name
    - last_name
    - email
    - phone (optional)
  - pricing info (total_amount, currency, quote_id or similar)
  - optional:
    - special_requests
    - offer_id / promo_code
- Output:
  - booking_id
  - hotel_slug
  - room_type_code
  - dates
  - guest summary
  - status (e.g. "PENDING_PAYMENT", "CONFIRMED" depending on payment flow)

## Requirements
- Save booking record in DB with proper relations (hotel, room type, dates, guest).
- Basic guards to avoid double-booking if availability is exhausted.
- Status model:
  - at minimum: PENDING_PAYMENT, CONFIRMED, CANCELLED.
- This issue does **not** include payment processing; just assumes we can store a booking and update status later.

## Acceptance Criteria
- [ ] Valid payload creates a new booking and returns its ID + status.
- [ ] Invalid payload returns 400 with clear error messages.
- [ ] Booking is persisted and can be retrieved in later endpoints.
""",
        "labels": ["backend", "enhancement"]
    },
    {
        "title": "Payment Processing for Booking (Stripe/PayPal Integration)",
        "body": """## Summary
Integrate payment processing so bookings can be paid securely (Stripe or PayPal, depending on configuration).

This sits between **booking creation** and **final booking confirmation**.

## Scope
- Design payment flow around:
  - existing booking created with `PENDING_PAYMENT` status.
- Example endpoints:
  - `POST /api/bookings/<booking_id>/payment/session/` → create payment session (Stripe Checkout or PayPal link).
  - `POST /api/payment/webhook/` → handle payment provider webhooks.

## Requirements
- Support at least one provider (Stripe preferred if available).
- On successful payment:
  - mark booking as `CONFIRMED`.
  - store payment reference (transaction id, provider, amount).
- On failed/cancelled payment:
  - keep booking as `PENDING_PAYMENT` or move to `CANCELLED` (to be agreed).
- Handle basic security:
  - verify signatures/webhooks from payment provider.
  - never trust client for payment status.

## Acceptance Criteria
- [ ] Ability to create a payment session for a specific booking.
- [ ] Webhook or callback correctly updates booking status to CONFIRMED on success.
- [ ] Failed or cancelled payments do not incorrectly confirm bookings.
""",
        "labels": ["backend", "enhancement"]
    },
    {
        "title": "Email Confirmation for Bookings",
        "body": """## Summary
Send **email confirmations** to guests (and optionally hotel) when a booking is confirmed.

Triggered after payment success OR after booking is set to `CONFIRMED` status in our system.

## Scope
- Implement email sending for:
  - Guest booking confirmation
  - Optional: internal notification to hotel/reservations office
- Template should include:
  - hotel name
  - guest name
  - booking_id / reference
  - dates (check-in / check-out)
  - room type
  - total paid
  - contact info for changes/cancellations

## Requirements
- Hook into booking lifecycle:
  - On booking status change to `CONFIRMED`, trigger email.
- Use existing email infrastructure if present (SMTP, SendGrid, etc.).
- Ensure retries / error logging if email fails.
- Emails should be in a simple, clear format (HTML or text), ready to be improved later.

## Acceptance Criteria
- [ ] When a booking is confirmed, the guest receives an email with all key details.
- [ ] Hotel/internal mailbox receives a notification if configured.
- [ ] Email logic is idempotent or guarded so the same confirmation is not spammed multiple times by accident.
""",
        "labels": ["backend", "enhancement"]
    }
]


def create_issue(issue_data):
    """Create a GitHub issue using gh CLI"""
    title = issue_data["title"]
    body = issue_data["body"]
    labels = issue_data["labels"]
    
    # Build command
    cmd = [
        "gh", "issue", "create",
        "--repo", "nlekkerman/HotelMateBackend",
        "--title", title,
        "--body", body,
        "--assignee", "@me"
    ]
    
    # Add labels individually
    for label in labels:
        cmd.extend(["--label", label])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        print(f"✓ Created: {title}")
        print(f"  URL: {issue_url}\n")
        return {"title": title, "url": issue_url}
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create: {title}")
        print(f"  Error: {e.stderr}\n")
        return None


def main():
    print("Creating GitHub issues for Booking Phase Backend...\n")
    print("=" * 70)
    print()
    
    created_issues = []
    
    for issue in issues:
        result = create_issue(issue)
        if result:
            created_issues.append(result)
    
    print("=" * 70)
    print(f"\n✓ Created {len(created_issues)} issues\n")
    
    # Output Markdown list
    print("## Created Issues\n")
    for issue in created_issues:
        # Extract issue number from URL
        issue_num = issue["url"].split("/")[-1]
        print(f"- #{issue_num}: [{issue['title']}]({issue['url']})")


if __name__ == "__main__":
    main()
