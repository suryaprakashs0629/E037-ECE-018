"""Framework-independent deterministic allocator for the official E037 contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

PRIORITY = {"SECURITY": 1, "MEDICAL": 2, "EVENTS": 3, "MAINTENANCE": 4}
OFFICIAL_REASONS = {
    "UNKNOWN_GROUP", "DURATION_LIMIT", "TOO_MANY_CHANNELS", "RESERVED_CHANNEL",
    "MERGED", "NO_CHANNEL", "PREEMPTED"
}

@dataclass(frozen=True)
class Channel:
    channel_no: int
    frequency_mhz: str
    spacing_khz: str = "12.5"
    is_emergency: bool = False

@dataclass(frozen=True)
class Group:
    group_id: str
    group_name: str
    category: str
    priority_rank: int
    contact_name: str = ""
    contact_mobile: str = ""

@dataclass
class Request:
    request_id: str
    group_id: str
    date: str
    start_slot: int
    end_slot: int
    channels_needed: int
    fixed_channels: Optional[Tuple[int, ...]] = None
    submitted_seq: int = 0
    category: str = ""
    priority_rank: int = 99
    purpose: str = ""
    source: str = "command"
    aliases: List[str] = field(default_factory=list)
    is_emergency: bool = False

    @property
    def slots(self) -> range:
        return range(self.start_slot, self.end_slot + 1)

@dataclass(frozen=True)
class Assignment:
    date: str
    slot: int
    channel_no: int
    group_id: str
    request_id: str

@dataclass(frozen=True)
class Conflict:
    date: str
    request_id: str
    group_id: str
    reason: str
    detail: str = "NONE"

@dataclass
class EngineResult:
    assignments: List[Assignment] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)
    statuses: Dict[str, str] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)

class AllocationEngine:
    """Allocation rules are pure Python and can be reused by CLI and Flask."""
    def __init__(self, channels: Sequence[Channel], groups: Sequence[Group]):
        self.channels = {c.channel_no: c for c in channels}
        self.groups = {g.group_id: g for g in groups}
        self.assignments: List[Assignment] = []
        self.conflicts: List[Conflict] = []
        self.statuses: Dict[str, str] = {}
        self.requests: Dict[str, Request] = {}
        self.messages: List[str] = []

    @staticmethod
    def fixed_tuple(value) -> Optional[Tuple[int, ...]]:
        if value is None or value == "" or str(value).upper() == "ANY":
            return None
        if isinstance(value, (tuple, list)):
            return tuple(int(x) for x in value)
        return tuple(int(x.strip()) for x in str(value).split(";") if x.strip())

    def normalize_request(self, req: Request) -> Request:
        group = self.groups.get(req.group_id)
        if group:
            req.category = group.category
            req.priority_rank = 1 if req.is_emergency else (group.priority_rank or PRIORITY.get(group.category, 99))
        req.fixed_channels = self.fixed_tuple(req.fixed_channels)
        self.requests[req.request_id] = req
        return req

    def validate(self, req: Request) -> Optional[Conflict]:
        # Official first-failure order; malformed structural values are parser diagnostics.
        if req.group_id not in self.groups:
            return Conflict(req.date, req.request_id, req.group_id, "UNKNOWN_GROUP", "NONE")
        duration = req.end_slot - req.start_slot + 1
        if duration > 8:
            return Conflict(req.date, req.request_id, req.group_id, "DURATION_LIMIT", "NONE")
        if req.channels_needed > 3:
            return Conflict(req.date, req.request_id, req.group_id, "TOO_MANY_CHANNELS", "NONE")
        if req.fixed_channels and 16 in req.fixed_channels:
            return Conflict(req.date, req.request_id, req.group_id, "RESERVED_CHANNEL", "NONE")
        if not (1 <= req.start_slot <= req.end_slot <= 48):
            return ValueError("Slots must be inclusive integers from 1 to 48.")
        if req.channels_needed < 1:
            return ValueError("channels_needed must be at least 1.")
        if req.fixed_channels is not None:
            if len(set(req.fixed_channels)) != len(req.fixed_channels):
                return ValueError("fixed_channels contains duplicate channel numbers.")
            if any(ch not in range(1, 16) for ch in req.fixed_channels):
                return ValueError("fixed_channels must contain channels 1–15 only.")
            if len(req.fixed_channels) != req.channels_needed:
                return ValueError("fixed_channels count must equal channels_needed.")
        return None

    def _same_group_merge(self, requests: Sequence[Request]) -> Tuple[List[Request], List[Conflict]]:
        """Merge connected overlapping intervals per group; max demand, earliest ID."""
        merged: List[Request] = []
        logs: List[Conflict] = []
        by_group: Dict[str, List[Request]] = {}
        for req in sorted(requests, key=lambda r: r.submitted_seq):
            by_group.setdefault(req.group_id, []).append(req)
        for group_id, items in by_group.items():
            items = sorted(items, key=lambda r: (r.start_slot, r.submitted_seq))
            clusters: List[List[Request]] = []
            for req in items:
                if not clusters or req.start_slot > max(x.end_slot for x in clusters[-1]):
                    clusters.append([req])
                else:
                    clusters[-1].append(req)
            for cluster in clusters:
                first = min(cluster, key=lambda r: r.submitted_seq)
                if len(cluster) == 1:
                    merged.append(first)
                    continue
                max_demand = max(r.channels_needed for r in cluster)
                start = min(r.start_slot for r in cluster)
                end = max(r.end_slot for r in cluster)
                # A fixed set is a hard constraint. If several overlapping records carry
                # different fixed sets, retain a deterministic invalid marker for this cluster.
                fixed_sets = {r.fixed_channels for r in cluster if r.fixed_channels is not None}
                fixed = next(iter(fixed_sets)) if len(fixed_sets) == 1 else (tuple() if len(fixed_sets) > 1 else None)
                combined = Request(
                    request_id=first.request_id, group_id=group_id, date=first.date,
                    start_slot=start, end_slot=end, channels_needed=max_demand,
                    fixed_channels=fixed, submitted_seq=first.submitted_seq,
                    category=first.category, priority_rank=(1 if any(x.is_emergency for x in cluster) else first.priority_rank),
                    purpose=first.purpose, source=first.source,
                    aliases=[x.request_id for x in cluster if x.request_id != first.request_id],
                    is_emergency=any(x.is_emergency for x in cluster)
                )
                merged.append(combined)
                for later in sorted((x for x in cluster if x.request_id != first.request_id), key=lambda r:r.submitted_seq):
                    logs.append(Conflict(later.date, later.request_id, later.group_id, "MERGED", first.request_id))
        merged.sort(key=lambda r: r.submitted_seq)
        return merged, logs

    @staticmethod
    def _conflicts_with(channel_no: int, group_id: str, slot: int, date: str, assignments: Sequence[Assignment]) -> bool:
        for a in assignments:
            if a.date == date and a.slot == slot and a.group_id != group_id and abs(a.channel_no - channel_no) <= 1:
                return True
        return False

    def _plan_request(self, req: Request, base: Sequence[Assignment]) -> Tuple[Optional[List[Assignment]], Optional[int]]:
        tentative: List[Assignment] = []
        previous: List[int] = []
        for slot in req.slots:
            occupied = list(base) + tentative
            if req.fixed_channels is not None:
                chosen = list(req.fixed_channels)
                if any(self._conflicts_with(ch, req.group_id, slot, req.date, occupied) for ch in chosen):
                    return None, slot
            else:
                chosen = []
                # Retain as much of the previous slot's allocation as remains valid.
                for ch in previous:
                    if ch not in chosen and not self._conflicts_with(ch, req.group_id, slot, req.date, occupied):
                        chosen.append(ch)
                # Fill with the lowest valid channel numbers; adjacent channels inside
                # the same group are permitted by the official rule.
                for ch in range(1, 16):
                    if len(chosen) >= req.channels_needed:
                        break
                    if ch not in chosen and not self._conflicts_with(ch, req.group_id, slot, req.date, occupied):
                        chosen.append(ch)
                if len(chosen) != req.channels_needed:
                    return None, slot
                chosen.sort()
            if len(chosen) != req.channels_needed:
                return None, slot
            for ch in chosen:
                tentative.append(Assignment(req.date, slot, ch, req.group_id, req.request_id))
            previous = chosen
        return tentative, None

    def allocate_initial(self, requests: Sequence[Request]) -> EngineResult:
        accepted: List[Request] = []
        new_conflicts: List[Conflict] = []
        for raw in sorted(requests, key=lambda r:r.submitted_seq):
            req = self.normalize_request(raw)
            issue = self.validate(req)
            if isinstance(issue, ValueError):
                self.statuses[req.request_id] = "INVALID_INPUT"
                self.messages.append(f"{req.request_id}: {issue}")
                continue
            if issue:
                new_conflicts.append(issue)
                self.statuses[req.request_id] = issue.reason
            else:
                accepted.append(req)
        merged, merge_logs = self._same_group_merge(accepted)
        new_conflicts.extend(merge_logs)
        for log in merge_logs:
            self.statuses[log.request_id] = "MERGED"
        ordered = sorted(merged, key=lambda r:(r.priority_rank, r.submitted_seq, r.request_id))
        for req in ordered:
            # Merged constraints that conflict are not silently weakened.
            if req.fixed_channels == tuple():
                conflict = Conflict(req.date, req.request_id, req.group_id, "NO_CHANNEL", str(req.start_slot))
                new_conflicts.append(conflict); self.statuses[req.request_id] = "ALLOCATION_FAILED"
                continue
            planned, failed_slot = self._plan_request(req, self.assignments)
            if planned is None:
                conflict = Conflict(req.date, req.request_id, req.group_id, "NO_CHANNEL", str(failed_slot))
                new_conflicts.append(conflict); self.statuses[req.request_id] = "ALLOCATION_FAILED"
            else:
                self.assignments.extend(planned)
                self.statuses[req.request_id] = "ALLOCATED"
                for alias in req.aliases:
                    self.statuses[alias] = "MERGED"
        self.conflicts.extend(new_conflicts)
        return EngineResult(list(self.assignments), list(new_conflicts), dict(self.statuses), list(self.messages))

    def add_existing(self, requests: Sequence[Request], assignments: Sequence[Assignment]):
        for req in requests:
            self.normalize_request(req)
        self.assignments = list(assignments)

    def allocate_late(self, req: Request) -> EngineResult:
        req = self.normalize_request(req)
        issue = self.validate(req)
        if isinstance(issue, ValueError):
            self.messages.append(f"{req.request_id}: {issue}")
            self.statuses[req.request_id] = "INVALID_INPUT"
            return EngineResult(list(self.assignments), [], dict(self.statuses), list(self.messages))
        if issue:
            self.conflicts.append(issue); self.statuses[req.request_id] = issue.reason
            return EngineResult(list(self.assignments), [issue], dict(self.statuses), list(self.messages))
        planned, failed_slot = self._plan_request(req, self.assignments)
        if planned is not None:
            self.assignments.extend(planned); self.statuses[req.request_id] = "ALLOCATED"
            return EngineResult(list(self.assignments), [], dict(self.statuses), list(self.messages))
        # Only strictly lower-priority, overlapping requests are eligible.
        victim_ids = {a.request_id for a in self.assignments
                      if a.date == req.date and req.start_slot <= a.slot <= req.end_slot
                      and self.requests.get(a.request_id)
                      and self.requests[a.request_id].priority_rank > req.priority_rank}
        victims = sorted((self.requests[x] for x in victim_ids),
                         key=lambda v:(-v.priority_rank, -v.submitted_seq, v.request_id))
        for victim in victims:
            without_victim = [a for a in self.assignments if a.request_id != victim.request_id]
            replan, replan_failed = self._plan_request(req, without_victim)
            if replan is not None:
                self.assignments = without_victim + replan
                log = Conflict(victim.date, victim.request_id, victim.group_id, "PREEMPTED", req.request_id)
                self.conflicts.append(log)
                self.statuses[victim.request_id] = "PREEMPTED"
                self.statuses[req.request_id] = "ALLOCATED"
                return EngineResult(list(self.assignments), [log], dict(self.statuses), list(self.messages))
        log = Conflict(req.date, req.request_id, req.group_id, "NO_CHANNEL", str(failed_slot or req.start_slot))
        self.conflicts.append(log); self.statuses[req.request_id] = "ALLOCATION_FAILED"
        return EngineResult(list(self.assignments), [log], dict(self.statuses), list(self.messages))

    def result(self) -> EngineResult:
        return EngineResult(list(self.assignments), list(self.conflicts), dict(self.statuses), list(self.messages))


def slot_start(slot: int) -> str:
    minutes = (slot - 1) * 30
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def utilisation(assignments: Sequence[Assignment], date: str) -> Tuple[int, int, str]:
    used = sum(1 for a in assignments if a.date == date and 1 <= a.channel_no <= 15)
    return used, 720, f"{(used / 720 * 100):.2f}"
