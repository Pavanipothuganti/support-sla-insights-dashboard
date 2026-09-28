import unittest

import pandas as pd

from src.shift_analysis import _merge_shift
from src.sla_calculator import calculate_sla


class DateHandlingTests(unittest.TestCase):
    def test_shift_uses_roster_assignment_active_on_ist_ticket_date(self):
        tickets = pd.DataFrame(
            {
                "agent_id": ["A1", "A1"],
                "created_at_normalized": pd.to_datetime(
                    ["2025-06-29 18:29:00+00:00", "2025-06-29 18:30:00+00:00"], utc=True
                ),
            }
        )
        roster = pd.DataFrame(
            {
                "agent_id": ["A1", "A1"],
                "shift": ["Night", "Day"],
                "from_date": ["2025-01-01", "2025-06-30"],
                "to_date": ["2025-06-29", pd.NA],
            }
        )

        result = _merge_shift(tickets, roster)

        self.assertEqual(result["shift"].tolist(), ["Night", "Day"])

    def test_overlapping_roster_assignments_are_unknown(self):
        tickets = pd.DataFrame(
            {"agent_id": ["A1"], "created_at_normalized": pd.to_datetime(["2025-06-30"], utc=True)}
        )
        roster = pd.DataFrame(
            {
                "agent_id": ["A1", "A1"],
                "shift": ["Night", "Day"],
                "from_date": ["2025-01-01", "2025-06-01"],
                "to_date": [pd.NA, pd.NA],
            }
        )

        result = _merge_shift(tickets, roster)

        self.assertEqual(result.loc[0, "shift"], "Unknown")

    def test_week_uses_ist_calendar_date(self):
        tickets = pd.DataFrame(
            {
                "created_at": ["2025-01-05 19:00"],
                "first_response_at": ["2025-01-05 20:00"],
                "channel": ["email"],
            }
        )

        result = calculate_sla(tickets, {"email": 8.0})

        self.assertEqual(result.loc[0, "week"], "2025-01-06/2025-01-12")


if __name__ == "__main__":
    unittest.main()