class AITutorException(Exception):
    """Base exception for AI Tutor domain errors."""
    default_code = "AI_TUTOR_ERROR"
    default_message = "An error occurred while processing the AI Tutor request."

    def __init__(self, message=None, code=None, retryable=False):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.retryable = retryable
        super().__init__(self.message)


class MissingCredentialsError(AITutorException):
    default_code = "MISSING_CREDENTIALS"
    default_message = "AI service credentials are not configured on this server. Please contact your platform administrator."


class ProviderAuthenticationError(AITutorException):
    default_code = "PROVIDER_AUTH_ERROR"
    default_message = "AI provider authentication failed. The configured API key is invalid or revoked."


class ProviderQuotaExceededError(AITutorException):
    default_code = "QUOTA_EXCEEDED"
    default_message = "The platform AI service quota has been temporarily exhausted. Please try again later."


class RateLimitExceededError(AITutorException):
    default_code = "RATE_LIMIT_EXCEEDED"
    default_message = "You have exceeded your permitted AI Tutor request frequency. Please wait a moment before trying again."


class DailyLimitExceededError(AITutorException):
    default_code = "DAILY_LIMIT_EXCEEDED"
    default_message = "You have reached your daily AI Tutor request limit for today. It will reset tomorrow."


class ProviderTimeoutError(AITutorException):
    default_code = "PROVIDER_TIMEOUT"
    default_message = "The AI service took too long to respond. Please try again with a shorter code snippet or question."

    def __init__(self, message=None, code=None):
        super().__init__(message=message, code=code, retryable=True)


class InputTooLargeError(AITutorException):
    default_code = "INPUT_TOO_LARGE"
    default_message = "Submitted code or context exceeds maximum allowed size."


class PolicyViolationError(AITutorException):
    default_code = "POLICY_VIOLATION"
    default_message = "AI assistance for this feature is restricted under current assessment rules."
