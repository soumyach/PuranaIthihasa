class FactoryError(Exception):
    """Base error with a stable machine-readable code."""

    code = "FACTORY_ERROR"

    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}


class ContractError(FactoryError):
    code = "INVALID_CONTRACT"


class TransitionError(FactoryError):
    code = "ILLEGAL_TRANSITION"


class BlockedError(FactoryError):
    code = "BLOCKED"


class ProviderUnavailableError(FactoryError):
    code = "PROVIDER_UNAVAILABLE"


class BudgetExceededError(FactoryError):
    code = "BUDGET_EXCEEDED"


class LeaseError(FactoryError):
    code = "LEASE_UNAVAILABLE"


class NotImplementedStageError(FactoryError):
    code = "NOT_IMPLEMENTED"
