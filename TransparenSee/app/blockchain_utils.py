import json
import hashlib
from decimal import Decimal


def build_report_snapshot(financial_report):
    entries = financial_report.entries.all().order_by("date", "id")

    return {
        "report_id": financial_report.id,
        "title": financial_report.title,
        "org": financial_report.organization.name,
        "academic_year": str(financial_report.academic_year),
        "entries": [
            {
                "date": str(e.date),
                "type": e.entry_type,
                "category": e.category,
                "description": e.description,
                "amount": str(e.amount),
            }
            for e in entries
        ]
    }


def generate_report_hash(snapshot: dict) -> str:
    normalized = json.dumps(snapshot, sort_keys=True).encode()
    return hashlib.sha256(normalized).hexdigest()