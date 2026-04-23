class GoalseekError(Exception):
    """Base class for package errors."""

    exit_code = 1


class ManifestValidationError(GoalseekError):
    exit_code = 2


class ConfigError(GoalseekError):
    exit_code = 2


class ProjectStateError(GoalseekError):
    exit_code = 2


class ProviderExecutionError(GoalseekError):
    exit_code = 4


class VerificationError(GoalseekError):
    exit_code = 5


class MetricExtractionError(VerificationError):
    pass


class GitOperationError(GoalseekError):
    exit_code = 3


class ScopeViolationError(GoalseekError):
    exit_code = 2
