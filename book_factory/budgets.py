"""Hard cost and retry guards. Currency values use integer minor units."""

from .errors import BudgetExceededError, ContractError


class BudgetGuard:
    def __init__(self, policy):
        required = {"book_max_minor_units", "page_max_minor_units", "job_max_minor_units", "max_retries"}
        if required - set(policy):
            raise ContractError("budget policy is incomplete")
        if any(not isinstance(policy[key], int) or policy[key] < 0 for key in required):
            raise ContractError("budget limits must be non-negative integers")
        self.policy = policy
        self.book_spend = 0
        self.page_spend = {}
        self.reservations = {}

    def reserve(self, operation_key, estimated_minor_units, page_id=None):
        if operation_key in self.reservations:
            return self.reservations[operation_key]
        if not isinstance(estimated_minor_units, int) or estimated_minor_units < 0:
            raise ContractError("estimated cost must be a non-negative integer")
        if estimated_minor_units > self.policy["job_max_minor_units"]:
            raise BudgetExceededError("job estimate exceeds the configured cap")
        if self.book_spend + estimated_minor_units > self.policy["book_max_minor_units"]:
            raise BudgetExceededError("book estimate exceeds the remaining cap")
        current_page = self.page_spend.get(page_id, 0) if page_id else 0
        if page_id and current_page + estimated_minor_units > self.policy["page_max_minor_units"]:
            raise BudgetExceededError("page estimate exceeds the remaining cap")
        record = {"operation_key": operation_key, "reserved_minor_units": estimated_minor_units, "page_id": page_id}
        self.reservations[operation_key] = record
        self.book_spend += estimated_minor_units
        if page_id:
            self.page_spend[page_id] = current_page + estimated_minor_units
        return record
