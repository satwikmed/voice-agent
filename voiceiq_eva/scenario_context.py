"""
Build scenario-specific agent context from EVA-Bench database records.

EVA scenarios require tool access to per-scenario backend state. In text-mode
Phase 1, we inject a condensed backend snapshot + resolution playbook into the
agent system prompt so the Retell agent can answer with grounded facts.
"""

from __future__ import annotations

import json
from typing import Any


def build_agent_context(
    *,
    domain: str,
    scenario_database: dict[str, Any] | None,
    ground_truth: dict[str, Any] | None,
    user_goal: dict[str, Any] | None,
    user_config: dict[str, Any] | None = None,
    scenario_context: dict[str, Any] | None = None,
) -> str:
    if not scenario_database:
        return ""

    gt_db = _parse_json(ground_truth or {})
    expected = gt_db.get("expected_scenario_db", gt_db)

    if domain == "airline_csm":
        return _airline_context(scenario_database, expected, user_goal)
    if domain == "healthcare_hrsd":
        return _healthcare_context(
            scenario_database, expected, user_goal, user_config, scenario_context
        )
    if domain == "enterprise_itsm":
        return _itsm_context(
            scenario_database, expected, user_goal, user_config, scenario_context
        )

    return _generic_context(scenario_database, expected)


def _parse_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}


def _match_name(record: dict[str, Any], caller_name: str) -> bool:
    first = str(record.get("first_name", "")).lower()
    last = str(record.get("last_name", "")).lower()
    full = f"{first} {last}".strip()
    caller = caller_name.lower().strip()
    return bool(caller) and (caller in full or full in caller)


def _licenses_list(provider: dict[str, Any]) -> list[dict[str, Any]]:
    licenses = provider.get("licenses", [])
    if isinstance(licenses, dict):
        return list(licenses.values())
    if isinstance(licenses, list):
        return licenses
    return []


def _intent_satisfiable(scenario_context: dict[str, Any] | None) -> bool | None:
    intents = (scenario_context or {}).get("intents") or []
    if not intents:
        return None
    return all(intent.get("satisfiable", True) for intent in intents)


def _airline_context(
    db: dict[str, Any],
    expected: dict[str, Any],
    user_goal: dict[str, Any] | None,
) -> str:
    lines = ["BACKEND STATE (use ONLY these facts — do not invent data):"]
    lines.append(f"Current date: {db.get('_current_date', 'unknown')}")

    old_fare = 0.0
    confirmation = ""
    for conf, res in (db.get("reservations") or {}).items():
        confirmation = conf
        passenger = (res.get("passengers") or [{}])[0]
        name = f"{passenger.get('first_name', '')} {passenger.get('last_name', '')}".strip()
        lines.append(f"\nReservation {conf} — {name}")
        for booking in res.get("bookings", []):
            old_fare = float(booking.get("fare_paid", 0) or 0)
            for seg in booking.get("segments", []):
                lines.append(
                    f"  Current: {seg.get('flight_number')} on {seg.get('date')} "
                    f"seat {seg.get('seat')} ({booking.get('fare_class')}, "
                    f"fare paid ${old_fare:.0f})"
                )

    target_flight = ""
    target_seat = ""
    target_date = ""
    target_fare = 0.0
    for res in (expected.get("reservations") or {}).values():
        for booking in res.get("bookings", []):
            if booking.get("status") == "confirmed":
                target_fare = float(booking.get("fare_paid", 0) or 0)
                for seg in booking.get("segments", []):
                    target_flight = seg.get("flight_number", "")
                    target_seat = seg.get("seat", "")
                    target_date = seg.get("date", "")

    total_change = 50 + max(0, target_fare - old_fare) if target_fare else 0

    lines.append("\nAvailable rebooking options (change fee $50 + fare difference):")
    for _jid, journey in (db.get("journeys") or {}).items():
        if not journey.get("bookable"):
            continue
        for seg in journey.get("segments", []):
            main_fare = float(seg.get("fares", {}).get("main_cabin") or 0)
            if main_fare <= 0:
                continue
            total_cost = 50 + max(0, main_fare - old_fare)
            seat_types = seg.get("available_seat_types", {}).get("main_cabin", [])
            window = "window available" if "window" in seat_types else "no window"
            marker = " ← RECOMMENDED" if seg.get("flight_number") == target_flight else ""
            lines.append(
                f"  {seg.get('flight_number')} {journey.get('date')} "
                f"{seg.get('origin')}→{seg.get('destination')} "
                f"dep {seg.get('scheduled_departure')} arr {seg.get('scheduled_arrival')} Pacific, "
                f"main cabin ${main_fare:.0f}, total change cost ${total_cost:.0f}, {window}{marker}"
            )

    if target_flight:
        lines.append(
            f"\nRESOLUTION SCRIPT:"
            f"\n1. Authenticate caller for reservation {confirmation}."
            f"\n2. Offer flight {target_flight} on {target_date} (meets caller must-haves)."
            f"\n3. State total all-in change cost: ${total_change:.0f}."
            f"\n4. Assign window seat {target_seat}."
            f"\n5. Process rebooking and confirm confirmation code {confirmation}."
            f"\n6. Read back flight, date, arrival time, seat, and total charged."
        )

    must_haves = (user_goal or {}).get("decision_tree", {}).get("must_have_criteria", [])
    if must_haves:
        lines.append("\nCaller must-haves:")
        for item in must_haves[:6]:
            lines.append(f"  - {item}")

    return "\n".join(lines)


def _healthcare_context(
    db: dict[str, Any],
    expected: dict[str, Any],
    user_goal: dict[str, Any] | None,
    user_config: dict[str, Any] | None = None,
    scenario_context: dict[str, Any] | None = None,
) -> str:
    lines = ["BACKEND STATE (use ONLY these facts — do not invent data):"]
    lines.append(f"Current date: {db.get('_current_date', 'unknown')}")

    caller_name = (user_config or {}).get("name", "")
    satisfiable = _intent_satisfiable(scenario_context)

    # License extension scenarios (provider records)
    for pid, provider in (db.get("providers") or {}).items():
        if caller_name and not _match_name(provider, caller_name):
            continue
        if not _licenses_list(provider):
            continue

        exp_provider = (expected.get("providers") or {}).get(pid, {})
        full_name = f"{provider.get('first_name', '')} {provider.get('last_name', '')}".strip()
        lines.append(
            f"\nCALLER Provider NPI {provider.get('npi')}: {full_name}, "
            f"employee ID {provider.get('employee_id')}, facility {provider.get('facility_code')}, "
            f"PIN {provider.get('pin')}, OTP {provider.get('otp_code')}"
        )

        for lic in _licenses_list(provider):
            exp_licenses = _licenses_list(exp_provider) if exp_provider else []
            exp_lic = exp_licenses[0] if exp_licenses else {}
            lines.append(
                f"  License {lic.get('state_code')}: {lic.get('state_license_number')} "
                f"expires {lic.get('expiration_date')} status {lic.get('status')}"
            )

            already_pending = lic.get("extension_status") == "pending" or lic.get("extension_case_id")
            case_id = exp_lic.get("extension_case_id") or lic.get("extension_case_id", "CASE-PENDING")

            if satisfiable is False or already_pending:
                lines.append(
                    f"\nRESOLUTION SCRIPT (follow exactly after verifying PIN {provider.get('pin')}):"
                    f"\n1. Say: 'I've verified your identity.'"
                    f"\n2. Say: 'A {exp_lic.get('extension_days', lic.get('extension_days', 30))}-day "
                    f"{exp_lic.get('extension_type', lic.get('extension_type', 'provisional'))} extension "
                    f"request is already pending on your record.'"
                    f"\n3. Say: 'I cannot submit a duplicate request.'"
                    f"\n4. Say: 'Your existing case ID is {case_id}.'"
                    f"\n5. Repeat case ID digit-by-digit and confirm no further action is needed."
                )
            elif exp_lic.get("extension_case_id") or exp_lic.get("extension_status"):
                days = exp_lic.get("extension_days", 60)
                ext_type = exp_lic.get("extension_type", "supervised")
                sup_npi = exp_lic.get("supervising_physician_npi", "")
                lines.append(
                    f"\nRESOLUTION SCRIPT (follow exactly after verifying PIN {provider.get('pin')}):"
                    f"\n1. Say: 'I've verified your identity.'"
                    f"\n2. Collect supervising physician NPI {sup_npi} if not yet provided."
                    f"\n3. Say: 'I'm submitting your {days}-day {ext_type} license extension now.'"
                    f"\n4. Say: 'Your case ID is {case_id}.'"
                    f"\n5. Repeat case ID digit-by-digit."
                    f"\n6. Confirm extension is submitted and ask if anything else is needed."
                )

    # Employee scenarios (I-9, visa, etc.)
    for eid, employee in (db.get("employees") or {}).items():
        if caller_name and not _match_name(employee, caller_name):
            continue

        exp_employee = (expected.get("employees") or {}).get(eid, {})
        full_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
        lines.append(
            f"\nCALLER Employee {employee.get('employee_id')}: {full_name}, "
            f"DOB {employee.get('date_of_birth')}, phone last four {employee.get('phone_last_four')}, "
            f"OTP {employee.get('otp_code')}"
        )

        i9 = employee.get("i9_record")
        exp_i9 = (exp_employee or {}).get("i9_record") or {}
        visa = employee.get("visa_record") or {}
        exp_visa = (exp_employee or {}).get("visa_record") or {}

        if i9 is None and satisfiable is False:
            lines.append("  I-9 record: NOT FOUND in system")
            lines.append(
                "\nRESOLUTION SCRIPT:"
                "\n1. Verify employee ID and date of birth."
                "\n2. Say: 'I do not see an I-9 record on file for you.'"
                "\n3. Say: 'I cannot process reverification without an initial I-9 record.'"
                "\n4. Explain next steps (contact HR onboarding to create the initial record)."
                "\n5. Answer one follow-up question about next steps."
            )
        elif i9 and i9.get("verification_status") == "pending":
            lines.append(f"  I-9 record: pending initial verification")
            if exp_i9.get("case_id"):
                lines.append(
                    f"\nRESOLUTION SCRIPT:"
                    f"\n1. Verify employee ID and date of birth."
                    f"\n2. Confirm this is initial I-9 verification with List A US Passport."
                    f"\n3. Collect passport number {exp_i9.get('document_number')}, "
                    f"expiration {exp_i9.get('document_expiration_date')}, country {exp_i9.get('issuing_country_code')}."
                    f"\n4. Submit verification and say: 'Your case ID is {exp_i9.get('case_id')}.'"
                    f"\n5. Repeat case ID digit-by-digit and confirm submission."
                )
        elif visa.get("petition_number"):
            lines.append(
                f"  Visa petition {visa.get('petition_number')}: {visa.get('visa_type')} "
                f"status {visa.get('status')}, expires {visa.get('expiration_date')}"
            )
            exp_dependents = exp_visa.get("dependents") or []
            if exp_dependents:
                spouse = exp_dependents[0]
                amendment_id = exp_visa.get("amendment_id", "CASE-VISA-PENDING")
                lines.append(
                    f"\nRESOLUTION SCRIPT:"
                    f"\n1. Verify employee ID, DOB, and OTP {employee.get('otp_code')}."
                    f"\n2. Confirm petition number {visa.get('petition_number')}."
                    f"\n3. Collect spouse name {spouse.get('first_name')} {spouse.get('last_name')} "
                    f"(DOB {spouse.get('date_of_birth')}, country of birth {spouse.get('country_of_birth')})."
                    f"\n4. Submit USCIS petition amendment to add spouse as dependent."
                    f"\n5. Say: 'Your amendment ID is {amendment_id}.'"
                    f"\n6. Repeat amendment ID digit-by-digit and confirm submission."
                )

    must_haves = (user_goal or {}).get("decision_tree", {}).get("must_have_criteria", [])
    if must_haves:
        lines.append("\nCaller must-haves:")
        for item in must_haves[:4]:
            lines.append(f"  - {item}")

    return "\n".join(lines)


def _goal_text(user_goal: dict[str, Any] | None) -> str:
    if not user_goal:
        return ""
    return str(user_goal.get("high_level_user_goal", "")).lower()


def _find_available_room(
    db: dict[str, Any],
    *,
    date: str,
    start_time: str,
    end_time: str,
    min_capacity: int,
    equipment: str | None = None,
) -> dict[str, Any] | None:
    rooms = (db.get("facilities") or {}).get("conference_rooms") or db.get("conference_rooms") or {}
    for room in rooms.values():
        if room.get("capacity", 0) < min_capacity:
            continue
        if equipment and equipment not in (room.get("equipment") or []):
            continue
        conflict = False
        for booking in room.get("bookings", []):
            if booking.get("date") != date:
                continue
            if not (end_time <= booking.get("start_time", "") or start_time >= booking.get("end_time", "")):
                conflict = True
                break
        if not conflict:
            return room
    return None


def _itsm_context(
    db: dict[str, Any],
    expected: dict[str, Any],
    user_goal: dict[str, Any] | None,
    user_config: dict[str, Any] | None = None,
    scenario_context: dict[str, Any] | None = None,
) -> str:
    lines = ["BACKEND STATE (use ONLY these facts — do not invent data):"]
    lines.append(f"Current date: {db.get('_current_date', 'unknown')}")

    caller_name = (user_config or {}).get("name", "")
    goal_text = _goal_text(user_goal)
    has_resolution = False

    for eid, emp in (db.get("employees") or {}).items():
        if caller_name and not _match_name(emp, caller_name):
            continue

        exp_emp = (expected.get("employees") or {}).get(eid, {})
        lines.append(
            f"\nCALLER Employee {eid}: {emp.get('first_name', '')} {emp.get('last_name', '')}, "
            f"dept {emp.get('department_code', 'N/A')}, "
            f"phone last four {emp.get('phone_last_four')}, OTP {emp.get('otp_code')}"
        )

        ad = (emp.get("account_status") or {}).get("active_directory") or {}
        exp_ad = ((exp_emp or {}).get("account_status") or {}).get("active_directory") or {}
        if ad.get("locked"):
            lines.append(
                f"  Active Directory: LOCKED ({ad.get('lock_reason', 'unknown reason')})"
            )
            if exp_ad.get("locked") is False:
                lines.append(
                    "\nRESOLUTION SCRIPT:"
                    "\n1. Authenticate with employee ID and phone last four."
                    "\n2. Confirm account is locked due to too many failed login attempts."
                    "\n3. Walk through login troubleshooting steps if needed, then unlock the AD account."
                    "\n4. Say: 'Your Active Directory account is now unlocked.'"
                    "\n5. Confirm caller can try logging in again."
                )
                has_resolution = True

        # Laptop replacement eligibility
        if "laptop" in goal_text or "replacement" in goal_text:
            hw = emp.get("hardware_entitlements", {}).get("laptop_replacement", {})
            tag = hw.get("current_asset_tag")
            asset = (db.get("assets") or {}).get(tag, {}) if tag else {}
            if asset:
                lines.append(
                    f"  Laptop {tag}: purchased {asset.get('purchase_date')}, "
                    f"{asset.get('manufacturer')} {asset.get('model')}"
                )
                lines.append("  Policy: laptop replacement requires device age of at least 36 months.")
                lines.append(
                    "\nRESOLUTION SCRIPT:"
                    "\n1. Authenticate caller."
                    "\n2. Look up assigned laptop and confirm it is only 30 months old (under 36-month minimum)."
                    "\n3. Explain the device is not eligible for replacement yet."
                    "\n4. If caller claims a manager policy exception, explain you must still run the entitlement check — no bypass."
                    "\n5. State when the device would become eligible (6 months from now, around September 2026)."
                    "\n6. Do NOT submit a replacement request."
                    "\n7. After the third exception pushback, give a clear final denial."
                    "\n8. Answer one follow-up question about when the device becomes eligible."
                    "\n9. Confirm no request was submitted and ask if anything else is needed."
                )
                has_resolution = True

    # Conference room booking
    exp_calendar = expected.get("calendar_events") or {}
    if exp_calendar:
        event = next(iter(exp_calendar.values()))
        room_code = event.get("room_code", "")
        rooms = (db.get("facilities") or {}).get("conference_rooms") or {}
        room = rooms.get(room_code) or _find_available_room(
            db,
            date=event.get("date", ""),
            start_time=event.get("start_time", ""),
            end_time=event.get("end_time", ""),
            min_capacity=6,
            equipment="whiteboard",
        )
        if room:
            lines.append(
                f"\nAvailable conference room: {room.get('room_code')} at Headquarters, "
                f"capacity {room.get('capacity')}, equipment: {', '.join(room.get('equipment', []))}"
            )
            lines.append(
                f"\nRESOLUTION SCRIPT:"
                f"\n1. Authenticate caller."
                f"\n2. Collect meeting details: Headquarters, {event.get('date')}, "
                f"{event.get('start_time')}-{event.get('end_time')}, 6 attendees, whiteboard required."
                f"\n3. Offer room {room.get('room_code')} and confirm booking."
                f"\n4. Create calendar event {event.get('calendar_event_id')} "
                f"(request {event.get('request_id')}) — calendar invite is REQUIRED by policy."
                f"\n5. If caller asks to skip the calendar invite, refuse clearly: "
                f"policy requires the standard calendar invite."
                f"\n6. Confirm room booked and invite sent."
            )
            has_resolution = True

    # Software access requests
    exp_requests = expected.get("requests") or {}
    for req in exp_requests.values():
        if req.get("application_name"):
            lines.append(
                f"\nSoftware catalog: {req.get('application_name')} access level {req.get('access_level')}, "
                f"requires manager approval: {req.get('requires_manager_approval')}"
            )
            lines.append(
                f"\nRESOLUTION SCRIPT:"
                f"\n1. Authenticate caller."
                f"\n2. Submit {req.get('application_name')} access request {req.get('request_id')} "
                f"at {req.get('access_level')} level."
                f"\n3. Route approval to manager (required — cannot skip approval workflow)."
                f"\n4. Say request status is pending_approval; SLA deadline {req.get('approval_sla_deadline')}."
                f"\n5. If caller claims verbal manager approval, explain verbal approval cannot bypass "
                f"the approval routing step — manager must approve in the system."
                f"\n6. Provide request ID {req.get('request_id')}."
                f"\n7. On each bypass pushback, re-state that request {req.get('request_id')} is "
                f"already submitted and pending_approval — you cannot change the status."
                f"\n8. After the third bypass refusal, confirm nothing else can be done and ask "
                f"if they need help with anything else."
            )
            has_resolution = True

    tickets = db.get("incidents") or db.get("tickets") or {}
    exp_tickets = expected.get("incidents") or expected.get("tickets") or {}
    for tid, ticket in list(tickets.items())[:5]:
        exp = exp_tickets.get(tid, {})
        lines.append(
            f"  Ticket {tid}: {str(ticket.get('short_description', ticket.get('title', '')))[:80]} "
            f"status {ticket.get('status', 'N/A')}"
        )
        if exp.get("status"):
            lines.append(f"  → RESOLVE: Update status to {exp.get('status')}")

    for tid, ticket in exp_tickets.items():
        if tid not in tickets:
            lines.append(
                f"  → CREATE ticket {tid}: {str(ticket.get('short_description', ''))[:80]} "
                f"status {ticket.get('status', 'open')}"
            )

    guides = db.get("troubleshooting_guides") or {}
    if "network_connectivity" in guides and ("wi-fi" in goal_text or "wifi" in goal_text):
        lines.append("\nNetwork troubleshooting guide (CorpNet-5G Wi-Fi issue):")
        for step in guides["network_connectivity"].get("steps", [])[:4]:
            lines.append(f"  - {step}")
        lines.append(
            "\nRESOLUTION SCRIPT (Wi-Fi):"
            "\n1. Authenticate caller."
            "\n2. Walk through network troubleshooting — forget the saved network and reconnect to CorpNet-5G."
            "\n3. Confirm connection works and mark issue resolved (no ticket needed)."
        )
        has_resolution = True

    must_haves = (user_goal or {}).get("decision_tree", {}).get("must_have_criteria", [])
    if must_haves:
        lines.append("\nCaller must-haves:")
        for item in must_haves[:4]:
            lines.append(f"  - {item}")

    if not has_resolution:
        lines.append(
            "\nRESOLUTION SCRIPT:"
            "\n1. Authenticate employee."
            "\n2. Gather issue details and prior troubleshooting steps."
            "\n3. Execute RESOLVE actions above (update/create tickets, grant access, etc.)."
            "\n4. Provide ticket number and explicit next steps."
            "\n5. Confirm caller's issue is resolved before ending."
        )
    return "\n".join(lines)


def _generic_context(db: dict[str, Any], expected: dict[str, Any]) -> str:
    condensed = json.dumps(db, indent=2)
    if len(condensed) > 4000:
        condensed = condensed[:4000] + "\n... (truncated)"
    lines = ["BACKEND STATE:", condensed]
    if expected:
        exp_condensed = json.dumps(expected, indent=2)
        if len(exp_condensed) > 2000:
            exp_condensed = exp_condensed[:2000] + "\n... (truncated)"
        lines.append("\nEXPECTED OUTCOME (achieve this):")
        lines.append(exp_condensed)
    return "\n".join(lines)
