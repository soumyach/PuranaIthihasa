"""Append-only, replayable book production state."""

import json
from copy import deepcopy
from pathlib import Path

from .errors import ContractError, TransitionError
from .util import append_jsonl, atomic_json_write, stable_id, utc_now


STAGES = (
    "QUEUED",
    "SOURCE_CHECK",
    "MANUSCRIPT",
    "EDITORIAL_QA",
    "STORYBOARD",
    "CHARACTER_BIBLE",
    "ART_PROOFS",
    "AWAITING_STYLE_APPROVAL",
    "ILLUSTRATION",
    "LETTERING",
    "PDF_LAYOUT",
    "VISUAL_QA",
    "READY_FOR_PUBLICATION",
)
RECOVERY_STATES = ("BLOCKED", "FAILED")
ALL_STATES = set(STAGES + RECOVERY_STATES)


def next_stage(stage):
    if stage not in STAGES or stage == STAGES[-1]:
        return None
    return STAGES[STAGES.index(stage) + 1]


def validate_state(state):
    required = {"book_id", "current_stage", "version", "last_event_id", "completed_stages", "attempts"}
    missing = required - set(state)
    if missing:
        raise ContractError("state missing fields: %s" % ", ".join(sorted(missing)))
    if state["current_stage"] not in ALL_STATES:
        raise ContractError("unknown state %s" % state["current_stage"])
    if not isinstance(state["version"], int) or state["version"] < 1:
        raise ContractError("state version must be a positive integer")
    if state["current_stage"] in RECOVERY_STATES:
        recovery = state.get("recovery")
        if not isinstance(recovery, dict) or recovery.get("resume_stage") not in STAGES or not recovery.get("reason"):
            raise ContractError("blocked and failed states require reason and resume_stage")
    return state


class StateStore:
    """The event log is authoritative; state.json is a repairable materialized view."""

    def __init__(self, books_root, book_id, max_retries=3):
        self.book_id = book_id
        self.book_root = Path(books_root) / book_id
        self.run_root = self.book_root / "run"
        self.state_path = self.run_root / "state.json"
        self.events_path = self.run_root / "events.jsonl"
        self.max_retries = max_retries

    def _events(self):
        if not self.events_path.exists():
            return []
        events = []
        with self.events_path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError as exc:
                        raise ContractError("invalid event log line %d: %s" % (number, exc))
        for index, event in enumerate(events, 1):
            if event.get("sequence") != index:
                raise ContractError("event sequence is not contiguous")
        return events

    def initialize(self):
        if self.events_path.exists() and self._events():
            return self.load()
        now = utc_now()
        state = {
            "schema_version": "1.0",
            "book_id": self.book_id,
            "current_stage": "QUEUED",
            "version": 1,
            "last_event_id": stable_id("event", self.book_id, 1, "INITIALIZED"),
            "completed_stages": [],
            "attempts": {},
            "blocked": None,
            "recovery": None,
            "artifacts": [],
            "outstanding_jobs": [],
            "updated_at": now,
        }
        event = self._event("INITIALIZED", None, "QUEUED", state, None, "system", now, [], [], [])
        append_jsonl(self.events_path, event)
        atomic_json_write(self.state_path, state)
        return state

    def _event(self, action, previous, target, state, operation_key, actor, timestamp,
               input_hashes, output_hashes, policy_hashes):
        sequence = state["version"]
        return {
            "schema_version": "1.0",
            "id": state["last_event_id"],
            "sequence": sequence,
            "book_id": self.book_id,
            "action": action,
            "from": previous,
            "to": target,
            "actor": actor,
            "operation_key": operation_key,
            "input_hashes": sorted(input_hashes),
            "output_hashes": sorted(output_hashes),
            "policy_hashes": sorted(policy_hashes),
            "timestamp": timestamp,
            "state_snapshot": deepcopy(state),
        }

    def replay(self):
        events = self._events()
        if not events:
            raise ContractError("book %s has no event history" % self.book_id)
        state = None
        previous_target = None
        for event in events:
            if event.get("book_id") != self.book_id or event.get("from") != previous_target:
                raise ContractError("event chain is inconsistent")
            state = event.get("state_snapshot")
            validate_state(state)
            if (state["last_event_id"] != event["id"] or state["version"] != event["sequence"]
                    or state["current_stage"] != event.get("to")):
                raise ContractError("event snapshot does not match its envelope")
            previous_target = event["to"]
        return state

    def load(self):
        replayed = self.replay()
        materialized = None
        if self.state_path.exists():
            try:
                with self.state_path.open("r", encoding="utf-8") as handle:
                    materialized = json.load(handle)
            except (json.JSONDecodeError, OSError):
                materialized = None
        if materialized != replayed:
            atomic_json_write(self.state_path, replayed)
        return replayed

    def transition(self, target, operation_key, actor="director", recovery=None,
                   input_hashes=None, output_hashes=None, policy_hashes=None):
        if not operation_key:
            raise ContractError("an operation key is required")
        events = self._events()
        for event in events:
            if event.get("operation_key") == operation_key:
                return event["state_snapshot"]
        state = self.load() if events else self.initialize()
        current = state["current_stage"]
        if target not in ALL_STATES:
            raise TransitionError("unknown target %s" % target)
        if current == "READY_FOR_PUBLICATION":
            raise TransitionError("READY_FOR_PUBLICATION is terminal inside the factory")
        if current in RECOVERY_STATES:
            allowed = state["recovery"]["resume_stage"]
            if target != allowed:
                raise TransitionError("%s may resume only at %s" % (current, allowed))
            action = "RESUMED"
        elif target in RECOVERY_STATES:
            if not isinstance(recovery, dict) or recovery.get("resume_stage") != current or not recovery.get("reason"):
                raise TransitionError("recovery state requires a reason and the current resume_stage")
            action = "BLOCKED" if target == "BLOCKED" else "FAILED"
        elif target != next_stage(current):
            raise TransitionError("illegal transition %s -> %s" % (current, target))
        else:
            action = "ADVANCED"

        new_state = deepcopy(state)
        attempts = new_state.setdefault("attempts", {})
        attempts[current] = attempts.get(current, 0) + 1
        if attempts[current] > self.max_retries:
            raise TransitionError("retry limit exceeded for %s" % current)
        if action == "ADVANCED" and current not in new_state["completed_stages"]:
            new_state["completed_stages"].append(current)
        new_state["current_stage"] = target
        new_state["blocked"] = recovery.get("reason") if recovery and target == "BLOCKED" else None
        new_state["recovery"] = deepcopy(recovery) if target in RECOVERY_STATES else None
        new_state["version"] += 1
        new_state["updated_at"] = utc_now()
        new_state["last_event_id"] = stable_id("event", self.book_id, new_state["version"], operation_key)
        validate_state(new_state)
        event = self._event(
            action,
            current,
            target,
            new_state,
            operation_key,
            actor,
            new_state["updated_at"],
            input_hashes or [],
            output_hashes or [],
            policy_hashes or [],
        )
        append_jsonl(self.events_path, event)
        atomic_json_write(self.state_path, new_state)
        return new_state


def job_key(book_id, stage, page_id, input_hashes, policy_hashes, worker_version, provider_config_hash):
    from .util import content_hash

    return content_hash({
        "book_id": book_id,
        "stage": stage,
        "page_id": page_id,
        "input_hashes": sorted(input_hashes),
        "policy_hashes": sorted(policy_hashes),
        "worker_version": worker_version,
        "provider_config_hash": provider_config_hash,
    })


def page_id(book_id, page_number):
    if not isinstance(page_number, int) or page_number < 1:
        raise ContractError("page number must be a positive integer")
    return stable_id("page", book_id, "%04d" % page_number)
