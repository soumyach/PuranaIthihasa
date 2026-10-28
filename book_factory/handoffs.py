"""Auditable file handoffs for Codex specialist agents.

The repository cannot spawn a Codex subagent itself.  The Director therefore
prepares a locked request and imports the separate agent's exact response.  An
orchestrator attestation records the real session execution without pretending
that it is a cryptographic identity proof.
"""

from pathlib import Path

from .errors import ContractError
from .util import atomic_json_write, content_hash, load_json, stable_id, utc_now


HANDOFF_KINDS = {
    "MANUSCRIPT_GENERATION", "MANUSCRIPT_REVISION", "EDITORIAL_REVIEW",
    "VISUAL_PREPRODUCTION", "VISUAL_REVIEW", "DIRECTOR_DIAGNOSTIC",
    "DIRECTOR_DIAGNOSTIC_REVIEW",
}
MECHANISM = "CODEX_SPECIALIST_SUBAGENT_HANDOFF"
CAPABILITIES = {
    "MANUSCRIPT_GENERATION": "manuscript_generation",
    "MANUSCRIPT_REVISION": "manuscript_generation",
    "EDITORIAL_REVIEW": "editorial_review",
    "VISUAL_PREPRODUCTION": "visual_preproduction",
    "VISUAL_REVIEW": "visual_evaluation",
    "DIRECTOR_DIAGNOSTIC": "orchestration_diagnostic",
    "DIRECTOR_DIAGNOSTIC_REVIEW": "orchestration_diagnostic_review",
}


def finalize_handoff(payload):
    unsigned = {key: value for key, value in payload.items() if key not in {"handoff_hash", "id", "path"}}
    digest = content_hash(unsigned)
    result = dict(unsigned)
    result["handoff_hash"] = digest
    result["id"] = stable_id("agent-handoff", result["book_id"], result["kind"], digest)
    return result


def validate_execution(handoff, response, expected_capability, writer_id=None):
    if response.get("handoff_hash") != handoff.get("handoff_hash"):
        raise ContractError("agent response does not bind the prepared handoff")
    if response.get("request_hash") != handoff.get("request_hash"):
        raise ContractError("agent response does not bind the locked request")
    execution = response.get("execution", {})
    if execution.get("mechanism") != MECHANISM:
        raise ContractError("unsupported Codex handoff execution mechanism")
    if not execution.get("executed"):
        raise ContractError("agent response does not attest actual execution")
    if execution.get("capability") != expected_capability:
        raise ContractError("agent response capability does not match the handoff")
    if not execution.get("agent_id"):
        raise ContractError("agent response is missing an agent id")
    if execution.get("paid_api_calls") != 0 or execution.get("cost_minor_units") != 0:
        raise ContractError("this milestone permits only zero-cost Codex session handoffs")
    if execution.get("attestation_scope") != "ORCHESTRATOR_SESSION_RECORD_NOT_CRYPTOGRAPHIC_IDENTITY":
        raise ContractError("the execution attestation scope must be explicit")
    if writer_id and execution.get("agent_id") == writer_id:
        raise ContractError("the independent reviewer must differ from the creator")
    if not response.get("orchestrator_attested"):
        raise ContractError("the active Codex orchestrator did not attest this imported response")
    return execution


class SessionHandoffStore:
    def __init__(self, books_root):
        self.books_root = Path(books_root)

    def _root(self, book_id, kind):
        return self.books_root / book_id / "handoffs" / kind.lower().replace("_", "-")

    def prepare(self, book_id, kind, request, required_role, locked_input_hashes, writer_id=None):
        if kind not in HANDOFF_KINDS:
            raise ContractError("unknown agent handoff kind")
        request_hash = request.get("request_hash") or content_hash(request)
        payload = {
            "schema_version": "1.0",
            "book_id": book_id,
            "kind": kind,
            "status": "AWAITING_CODEX_SPECIALIST_AGENT",
            "request_hash": request_hash,
            "request": request,
            "required_role": required_role,
            "required_capability": CAPABILITIES[kind],
            "required_independence_from_writer_id": writer_id,
            "locked_input_hashes": sorted(set(locked_input_hashes)),
            "execution_boundary": {
                "mechanism": MECHANISM,
                "programmatic_spawn_available_inside_repository": False,
                "orchestrated_by_current_codex_session": True,
                "paid_api_calls_allowed": 0,
                "identity_assurance": "SESSION_ATTESTATION_ONLY_NOT_CRYPTOGRAPHIC",
            },
        }
        record = finalize_handoff(payload)
        path = self._root(book_id, kind) / (record["handoff_hash"] + ".request.json")
        if path.exists() and load_json(path) != record:
            raise ContractError("agent handoff hash collision")
        if not path.exists():
            atomic_json_write(path, record)
        return record, path

    def store_response(self, handoff, response):
        unsigned = {key: value for key, value in response.items() if key not in {"response_hash", "id", "stored_at"}}
        digest = content_hash(unsigned)
        record = dict(unsigned)
        record["response_hash"] = digest
        record["id"] = stable_id("agent-response", handoff["book_id"], handoff["kind"], digest)
        record["stored_at"] = utc_now()
        path = self._root(handoff["book_id"], handoff["kind"]) / (digest + ".response.json")
        if path.exists():
            existing = load_json(path)
            # stored_at is deliberately retained from the first successful import.
            if {k: v for k, v in existing.items() if k != "stored_at"} != {k: v for k, v in record.items() if k != "stored_at"}:
                raise ContractError("agent response hash collision")
            return existing, path
        atomic_json_write(path, record)
        return record, path

    def response_for(self, handoff):
        """Return the one response bound to a handoff, failing closed on conflict."""
        root = self._root(handoff["book_id"], handoff["kind"])
        matches = []
        for path in sorted(root.glob("*.response.json")):
            response = load_json(path)
            unsigned = {
                key: value for key, value in response.items()
                if key not in {"response_hash", "id", "stored_at"}
            }
            digest = content_hash(unsigned)
            expected_id = stable_id("agent-response", handoff["book_id"], handoff["kind"], digest)
            if (
                response.get("response_hash") != digest
                or response.get("id") != expected_id
                or path.name != digest + ".response.json"
            ):
                raise ContractError("stored specialist response failed hash revalidation")
            if (
                response.get("handoff_hash") == handoff.get("handoff_hash")
                and response.get("request_hash") == handoff.get("request_hash")
            ):
                matches.append((response, path))
        if len(matches) > 1:
            raise ContractError("multiple specialist responses bind the same handoff")
        return matches[0] if matches else (None, None)

    def resume_status(self, handoff):
        """Rehydrate the next host action without dispatching duplicate specialist work."""
        if finalize_handoff(handoff) != handoff:
            raise ContractError("stored handoff failed hash revalidation")
        response, path = self.response_for(handoff)
        if response is None:
            return {
                "status": "AWAITING_CODEX_SPECIALIST_AGENT",
                "handoff_hash": handoff["handoff_hash"],
                "request_hash": handoff["request_hash"],
                "required_role": handoff["required_role"],
                "required_capability": handoff["required_capability"],
                "dispatch_required": True,
            }
        return {
            "status": "SPECIALIST_RESPONSE_AVAILABLE",
            "handoff_hash": handoff["handoff_hash"],
            "request_hash": handoff["request_hash"],
            "response_hash": response["response_hash"],
            "response_path": str(path),
            "dispatch_required": False,
        }
