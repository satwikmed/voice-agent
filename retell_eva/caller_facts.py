"""
Extract caller verification facts from EVA-Bench scenario databases.

EVA negotiation scripts reference ``information_required``, but the dataset
does not ship that field populated. We derive it from the per-scenario backend
state so simulated callers provide exact identifiers during authentication.
"""

from __future__ import annotations

import json
from typing import Any


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
    return caller in full or full in caller


def _licenses_list(provider: dict[str, Any]) -> list[dict[str, Any]]:
    licenses = provider.get("licenses", [])
    if isinstance(licenses, dict):
        return list(licenses.values())
    if isinstance(licenses, list):
        return licenses
    return []


def _find_provider(db: dict[str, Any], caller_name: str) -> dict[str, Any] | None:
    for provider in (db.get("providers") or {}).values():
        if _match_name(provider, caller_name):
            return provider
    return None


def _find_employee(db: dict[str, Any], caller_name: str) -> dict[str, Any] | None:
    for employee in (db.get("employees") or {}).values():
        if _match_name(employee, caller_name):
            return employee
    return None


def _find_reservation(db: dict[str, Any], caller_name: str) -> tuple[str, dict[str, Any]] | None:
    for conf, reservation in (db.get("reservations") or {}).items():
        for passenger in reservation.get("passengers", []):
            if _match_name(passenger, caller_name):
                return conf, reservation
    return None


def _facts_from_provider(provider: dict[str, Any], expected_provider: dict[str, Any] | None) -> dict[str, str]:
    facts: dict[str, str] = {
        "NPI": str(provider.get("npi", "")),
        "Facility code": str(provider.get("facility_code", "")),
        "4-digit PIN": str(provider.get("pin", "")),
        "Employee ID": str(provider.get("employee_id", "")),
        "Phone last four": str(provider.get("phone_last_four", "")),
        "OTP code": str(provider.get("otp_code", "")),
    }
    for lic in _licenses_list(provider):
        facts["State license number"] = str(lic.get("state_license_number", ""))
        facts["License state"] = str(lic.get("state_code", ""))
        facts["License expiration"] = str(lic.get("expiration_date", ""))

    exp_provider = expected_provider or {}
    for exp_lic in _licenses_list(exp_provider):
        if exp_lic.get("supervising_physician_npi"):
            facts["Supervising physician NPI"] = str(exp_lic["supervising_physician_npi"])
        if exp_lic.get("extension_days"):
            facts["Extension duration"] = f"{exp_lic['extension_days']} days"
        if exp_lic.get("extension_type"):
            facts["Extension type"] = str(exp_lic["extension_type"])
    return {k: v for k, v in facts.items() if v}


def _facts_from_employee(
    employee: dict[str, Any],
    expected_employee: dict[str, Any] | None,
) -> dict[str, str]:
    facts: dict[str, str] = {
        "Employee ID": str(employee.get("employee_id", "")),
        "Date of birth": str(employee.get("date_of_birth", "")),
        "Phone last four": str(employee.get("phone_last_four", "")),
        "OTP code": str(employee.get("otp_code", "")),
        "Full name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
    }

    exp_employee = expected_employee or {}
    exp_i9 = exp_employee.get("i9_record") or {}
    if exp_i9.get("verification_action"):
        facts["Verification action"] = str(exp_i9["verification_action"])
    if exp_i9.get("document_list_type"):
        facts["Document list type"] = str(exp_i9["document_list_type"])
    if exp_i9.get("document_type_code"):
        code = str(exp_i9["document_type_code"])
        facts["Document type code"] = code
        if code == "US_PASSPORT":
            facts["Document type"] = "US Passport"
    if exp_i9.get("document_number"):
        facts["Document number"] = str(exp_i9["document_number"])
    if exp_i9.get("document_expiration_date"):
        facts["Document expiration date"] = str(exp_i9["document_expiration_date"])
    if exp_i9.get("issuing_country_code"):
        facts["Issuing country code"] = str(exp_i9["issuing_country_code"])

    i9 = employee.get("i9_record") or {}
    if i9.get("verification_action") and "Verification action" not in facts:
        facts["Verification action"] = str(i9["verification_action"])

    visa = employee.get("visa_record") or {}
    exp_visa = exp_employee.get("visa_record") or {}
    if visa.get("petition_number"):
        facts["Visa petition number"] = str(visa["petition_number"])
    exp_dependents = exp_visa.get("dependents") or []
    if exp_dependents:
        spouse = exp_dependents[0]
        facts["Spouse first name"] = str(spouse.get("first_name", ""))
        facts["Spouse last name"] = str(spouse.get("last_name", ""))
        facts["Spouse date of birth"] = str(spouse.get("date_of_birth", ""))
        facts["Spouse country of birth"] = str(spouse.get("country_of_birth", ""))

    return {k: v for k, v in facts.items() if v}


def _facts_from_reservation(conf: str, reservation: dict[str, Any]) -> dict[str, str]:
    passenger = (reservation.get("passengers") or [{}])[0]
    return {
        "Confirmation code": conf,
        "Last name": str(passenger.get("last_name", "")),
        "First name": str(passenger.get("first_name", "")),
        "Phone": str(passenger.get("phone", "")),
    }


def _facts_from_itsm_employee(employee: dict[str, Any]) -> dict[str, str]:
    facts: dict[str, str] = {
        "Employee ID": str(employee.get("employee_id", "")),
        "Date of birth": str(employee.get("date_of_birth", "")),
        "Phone last four": str(employee.get("phone_last_four", "")),
        "OTP code": str(employee.get("otp_code", "")),
        "Full name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip(),
    }
    ad = (employee.get("account_status") or {}).get("active_directory") or {}
    if ad.get("locked"):
        facts["Active Directory status"] = f"locked ({ad.get('lock_reason', 'unknown')})"
    return {k: v for k, v in facts.items() if v}


def build_caller_facts(
    *,
    domain: str,
    scenario_database: dict[str, Any] | None,
    ground_truth: dict[str, Any] | None,
    user_config: dict[str, Any] | None,
) -> dict[str, str]:
    """Build the information_required map for a scenario caller persona."""
    if not scenario_database:
        return {}

    caller_name = (user_config or {}).get("name", "")
    gt = _parse_json(ground_truth or {})
    expected = gt.get("expected_scenario_db", gt)

    if domain == "airline_csm":
        match = _find_reservation(scenario_database, caller_name)
        if match:
            conf, reservation = match
            return _facts_from_reservation(conf, reservation)

    if domain == "healthcare_hrsd":
        provider = _find_provider(scenario_database, caller_name)
        exp_provider = _find_provider(expected, caller_name) if expected else None
        employee = _find_employee(scenario_database, caller_name)
        exp_employee = _find_employee(expected, caller_name) if expected else None

        if provider and _licenses_list(provider):
            return _facts_from_provider(provider, exp_provider)
        if employee:
            return _facts_from_employee(employee, exp_employee)

    if domain == "enterprise_itsm":
        employee = _find_employee(scenario_database, caller_name)
        if employee:
            return _facts_from_itsm_employee(employee)

    return {}


def format_caller_facts_block(facts: dict[str, str]) -> str:
    """Render facts for injection into a caller persona prompt."""
    if not facts:
        return ""
    lines = [
        "YOUR VERIFICATION & REQUEST DETAILS (information_required — use these EXACT values when the agent asks; never invent or guess):"
    ]
    for key, value in facts.items():
        lines.append(f"- {key}: {value}")
    lines.append(
        "When the agent asks for any identifier above, quote the exact value from this list."
    )
    return "\n".join(lines)
