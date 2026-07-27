from .types import ErrorCategory


class EngineError(Exception):
    category: ErrorCategory = ErrorCategory.UNKNOWN


class ParseError(EngineError):
    category = ErrorCategory.PARSE


class NoValidSelectionError(EngineError):
    category = ErrorCategory.POLICY


class BeliefInconsistentError(EngineError):
    category = ErrorCategory.POLICY


class SearchAPIError(EngineError):
    category = ErrorCategory.RUNTIME


class SearchBudgetExceeded(EngineError):
    category = ErrorCategory.TIMEOUT


class InvalidOutputError(EngineError):
    category = ErrorCategory.POLICY


class LegalityViolation(EngineError):
    category = ErrorCategory.LEGALITY
