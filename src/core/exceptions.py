from .types import ErrorCategory


class EngineError(Exception):
    """Base class for errors raised by the engine."""

    category: ErrorCategory = ErrorCategory.UNKNOWN


class PreflightError(EngineError):
    """Report an environment or package preflight failure."""

    category = ErrorCategory.RUNTIME


class ParseError(EngineError):
    category = ErrorCategory.PARSE


class NoValidSelectionError(EngineError):
    category = ErrorCategory.POLICY


class BeliefInconsistentError(EngineError):
    category = ErrorCategory.POLICY


class SearchAPIError(EngineError):
    category = ErrorCategory.RUNTIME


class SearchBudgetExceededError(EngineError):
    category = ErrorCategory.TIMEOUT


class InvalidOutputError(EngineError):
    category = ErrorCategory.POLICY


class LegalityViolationError(EngineError):
    category = ErrorCategory.LEGALITY
