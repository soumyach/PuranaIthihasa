"""Provider-neutral contracts. Foundation PR2 ships no successful backend."""

from abc import ABC, abstractmethod

from ..errors import ProviderUnavailableError


PROVIDER_KINDS = ("language_model", "image", "pdf", "visual_evaluation")


class Provider(ABC):
    kind = None
    name = None

    @abstractmethod
    def capabilities(self):
        raise NotImplementedError

    @abstractmethod
    def estimate_minor_units(self, request):
        raise NotImplementedError

    @abstractmethod
    def execute(self, request, operation_key):
        raise NotImplementedError


class LanguageModelProvider(Provider):
    kind = "language_model"

    @abstractmethod
    def generate_manuscript(self, request, operation_key):
        raise NotImplementedError

    def execute(self, request, operation_key):
        return self.generate_manuscript(request, operation_key)


class ImageProvider(Provider):
    kind = "image"

    @abstractmethod
    def generate(self, request, operation_key):
        raise NotImplementedError

    @abstractmethod
    def edit(self, request, operation_key):
        raise NotImplementedError

    @abstractmethod
    def recover(self, provider_request_id):
        raise NotImplementedError

    def execute(self, request, operation_key):
        operation = request.get("operation", "generate")
        if operation == "generate":
            return self.generate(request, operation_key)
        if operation == "edit":
            return self.edit(request, operation_key)
        raise ValueError("unknown image operation %s" % operation)


class PdfProvider(Provider):
    kind = "pdf"

    @abstractmethod
    def compose(self, request, operation_key):
        raise NotImplementedError

    def execute(self, request, operation_key):
        return self.compose(request, operation_key)


class VisualEvaluationProvider(Provider):
    kind = "visual_evaluation"

    @abstractmethod
    def evaluate(self, request, operation_key):
        raise NotImplementedError

    def execute(self, request, operation_key):
        return self.evaluate(request, operation_key)


class UnavailableProvider(Provider):
    def __init__(self, kind, reason, setup_hint):
        if kind not in PROVIDER_KINDS:
            raise ValueError("unknown provider kind")
        self.kind = kind
        self.name = "unavailable-%s" % kind
        self.reason = reason
        self.setup_hint = setup_hint

    def capabilities(self):
        return {
            "kind": self.kind,
            "name": self.name,
            "available": False,
            "reason": self.reason,
            "setup_hint": self.setup_hint,
            "network_calls": False,
        }

    def estimate_minor_units(self, request):
        raise ProviderUnavailableError(self.reason, self.capabilities())

    def execute(self, request, operation_key):
        raise ProviderUnavailableError(self.reason, self.capabilities())


class FixtureImageProviderContract(UnavailableProvider):
    """Reserved offline test seam; it deliberately cannot report production success."""

    def __init__(self):
        super().__init__(
            "image",
            "the Foundation fixture image provider has no production execution backend",
            "implement an explicitly test-only deterministic fixture in a later milestone",
        )


class ProviderRegistry:
    def __init__(self, providers=None):
        self.providers = dict(providers or {})
        for kind in PROVIDER_KINDS:
            self.providers.setdefault(
                kind,
                UnavailableProvider(kind, "%s backend is not configured" % kind, "register an approved adapter and credentials"),
            )

    def capabilities(self):
        return {kind: self.providers[kind].capabilities() for kind in PROVIDER_KINDS}

    def require(self, kind):
        provider = self.providers[kind]
        capability = provider.capabilities()
        if not capability.get("available"):
            raise ProviderUnavailableError(capability["reason"], capability)
        return provider


def guarded_provider_call(provider, request, operation_key, budget_guard, page_id=None):
    capability = provider.capabilities()
    if not capability.get("available"):
        raise ProviderUnavailableError(capability.get("reason", "provider unavailable"), capability)
    estimate = provider.estimate_minor_units(request)
    budget_guard.reserve(operation_key, estimate, page_id=page_id)
    return provider.execute(request, operation_key)
