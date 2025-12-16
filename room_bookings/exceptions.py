class RoomAssignmentError(Exception):
    """Structured exception for room assignment validation failures"""
    
    def __init__(self, code, message, details=None):
        self.code = code
        self.message = message 
        self.details = details or {}
        super().__init__(self.message)