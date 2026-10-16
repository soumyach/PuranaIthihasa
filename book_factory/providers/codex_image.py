"""Host-injected adapter for the Codex built-in image-generation tool.

The desktop host owns the native tool.  A repository process can execute this
adapter only when that host injects a callable runner; otherwise it fails closed
and the file-handoff bridge in illustration_production is used.
"""

from ..errors import ProviderUnavailableError
from .base import ImageProvider


class CodexNativeImageProvider(ImageProvider):
    kind = "image"
    name = "codex-built-in-image-gen"

    def __init__(self, executor=None, recovery=None):
        self.executor = executor
        self.recovery = recovery

    def capabilities(self):
        available = callable(self.executor)
        return {
            "kind": self.kind,
            "name": self.name,
            "model": "NOT_SURFACED_BY_BUILTIN_TOOL",
            "available": available,
            "operations": ["generate", "edit", "reference_conditioning"],
            "reference_conditioning": True,
            "network_calls": True,
            "credential_required": False,
            "estimated_cost_minor_units": 0,
            "billable_repository_call": False,
            "integration": "HOST_INJECTED_CODEX_NATIVE_IMAGE_TOOL",
            "reason": None if available else "Codex native image executor is not injected into this process",
            "setup_hint": "Run through the Codex session handoff or inject the authorized host runner",
        }

    def estimate_minor_units(self, request):
        if request.get("paid_operation"):
            raise ProviderUnavailableError("the Codex native adapter does not authorize paid operations")
        return 0

    def _execute(self, request, operation_key):
        if not callable(self.executor):
            capability = self.capabilities()
            raise ProviderUnavailableError(capability["reason"], capability)
        return self.executor(request, operation_key)

    def generate(self, request, operation_key):
        return self._execute(dict(request, operation="generate"), operation_key)

    def edit(self, request, operation_key):
        return self._execute(dict(request, operation="edit"), operation_key)

    def recover(self, provider_request_id):
        if not callable(self.recovery):
            raise ProviderUnavailableError("Codex native image recovery is not injected")
        return self.recovery(provider_request_id)
