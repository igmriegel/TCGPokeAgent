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


class SearchBudgetExceededError(EngineError):
    category = ErrorCategory.TIMEOUT


class InvalidOutputError(EngineError):
    category = ErrorCategory.POLICY


class LegalityViolationError(EngineError):
    category = ErrorCategory.LEGALITY
