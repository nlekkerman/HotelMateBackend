# Single source of truth for room assignment business rules

# Booking statuses that can block room inventory (combine with timestamp checks)
# Only include PENDING_PAYMENT if business reserves inventory before payment
INVENTORY_BLOCKING_STATUSES = ["CONFIRMED"]  # CHECKED_IN status doesn't exist - use checked_in_at timestamp

# Booking statuses allowed for room assignment
ASSIGNABLE_BOOKING_STATUSES = ["CONFIRMED"]

# Non-blocking statuses (never block inventory)
NON_BLOCKING_STATUSES = ["CANCELLED", "COMPLETED", "NO_SHOW"]

# Room assignment operation types for audit logging
ASSIGNMENT_OPERATIONS = {
    'ASSIGNED': 'assigned',
    'REASSIGNED': 'reassigned', 
    'UNASSIGNED': 'unassigned'
}