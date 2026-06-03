"""Custom exception classes for OmniFlow."""


class OmniFlowError(Exception):
    """Base exception for all OmniFlow errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AuthenticationError(OmniFlowError):
    """Raised when authentication fails (invalid credentials, expired token)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR")


class AuthorizationError(OmniFlowError):
    """Raised when a user lacks permission for the requested action."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class ValidationError(OmniFlowError):
    """Raised when request data fails validation."""

    def __init__(self, message: str = "Invalid request"):
        super().__init__(message=message, code="VALIDATION_ERROR")


class BusinessRuleError(OmniFlowError):
    """Raised when a business rule is violated."""

    def __init__(self, message: str = "Business rule violation"):
        super().__init__(message=message, code="BUSINESS_RULE_ERROR")


class NotFoundError(OmniFlowError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, code="NOT_FOUND")


class ExternalAPIError(OmniFlowError):
    """Raised when an external API call fails."""

    def __init__(self, message: str = "External API error"):
        super().__init__(message=message, code="EXTERNAL_API_ERROR")
