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


class ConflictError(OmniFlowError):
    """Raised when a resource conflict occurs (e.g. concurrent edits)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message=message, code="CONFLICT")


class ProviderUnavailableError(OmniFlowError):
    """Raised when an LLM provider is down or times out."""

    def __init__(self, message: str = "Provider unavailable"):
        super().__init__(message=message, code="PROVIDER_UNAVAILABLE")


class ToolExecutionError(OmniFlowError):
    """Raised when an agent tool fails."""

    def __init__(self, message: str = "Tool execution failed"):
        super().__init__(message=message, code="TOOL_ERROR")


class WorkflowExecutionError(OmniFlowError):
    """Raised when a bound workflow fails."""

    def __init__(self, message: str = "Workflow execution failed"):
        super().__init__(message=message, code="WORKFLOW_ERROR")


class PolicyViolationError(OmniFlowError):
    """Raised when an agent violates workspace policy."""

    def __init__(self, message: str = "Policy violation"):
        super().__init__(message=message, code="POLICY_VIOLATION")


class WorkspaceIsolationError(OmniFlowError):
    """Raised when cross-workspace access is attempted."""

    def __init__(self, message: str = "Workspace isolation violation"):
        super().__init__(message=message, code="WORKSPACE_ISOLATION")
