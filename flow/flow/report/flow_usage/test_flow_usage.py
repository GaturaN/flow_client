# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import date_diff
from frappe.utils.data import get_timespan_date_range

from flow.flow.report.flow_usage.flow_usage import execute
from flow.tests.usage_records import make_chat, make_user

MANAGER = "flow-usage-manager@example.com"
CLERK = "flow-usage-clerk@example.com"


class TestFlowUsage(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		self.addCleanup(frappe.set_user, "Administrator")
		make_user(MANAGER, role="System Manager")
		make_user(CLERK, role="Desk User")
		make_chat(MANAGER)
		make_chat(CLERK, status="Failed")
		make_chat(CLERK, feedback="Down")
		make_chat(CLERK, days_ago=20)
		make_chat(CLERK, source="Trigger")

	def test_a_system_manager_sees_the_whole_site_by_default(self):
		frappe.set_user(MANAGER)

		usage = _usage_by_user({})

		self.assertEqual((usage[MANAGER], usage[CLERK]), ((1, 1, 0, 0), (2, 2, 1, 1)))

	def test_a_system_manager_can_narrow_to_just_themselves(self):
		frappe.set_user(MANAGER)

		self.assertEqual(set(_usage_by_user({"show": "Just me"})), {MANAGER})

	def test_a_system_manager_can_narrow_to_one_user(self):
		frappe.set_user(MANAGER)

		self.assertEqual(set(_usage_by_user({"user": CLERK})), {CLERK})

	def test_everyone_else_only_ever_sees_themselves(self):
		frappe.set_user(CLERK)

		self.assertEqual(set(_usage_by_user({"show": "Whole site", "user": MANAGER})), {CLERK})

	def test_the_period_leaves_out_older_chats(self):
		frappe.set_user(CLERK)

		self.assertEqual(_usage_by_user({"period": "Last 30 days"})[CLERK][0], 3)

	def test_the_summary_adds_up_the_rows(self):
		frappe.set_user(CLERK)

		*_, summary = execute({})

		self.assertEqual([item["value"] for item in summary], [2, 2, 1, 1])

	def test_the_chart_has_one_bar_per_day_of_the_period(self):
		frappe.set_user(CLERK)

		_, _, _, chart, _ = execute({"period": "Last 7 days"})

		self.assertEqual(len(chart["data"]["labels"]), _days_in("last 7 days"))
		self.assertEqual(sum(chart["data"]["datasets"][0]["values"]), 2)

	def test_last_seven_days_matches_the_dashboard_cards(self):
		make_chat(CLERK, days_ago=7)
		frappe.set_user(CLERK)

		self.assertEqual(_usage_by_user({"period": "Last 7 days"})[CLERK][0], 3)

	def test_runs_started_by_triggers_are_left_out(self):
		frappe.set_user(CLERK)

		self.assertEqual(_usage_by_user({})[CLERK], (2, 2, 1, 1))

	def test_only_a_system_manager_may_open_the_report(self):
		report = frappe.get_doc("Report", "Flow Usage")

		frappe.set_user(MANAGER)
		self.assertTrue(report.is_permitted())
		frappe.set_user(CLERK)
		self.assertFalse(report.is_permitted())


def _usage_by_user(filters: dict) -> dict[str, tuple[int, int, int, int]]:
	_, rows, *_ = execute(filters)
	return {row["user"]: (row["chats"], row["runs"], row["failed_runs"], row["thumbs_down"]) for row in rows}


def _days_in(timespan: str) -> int:
	start, end = get_timespan_date_range(timespan)
	return date_diff(end, start) + 1
