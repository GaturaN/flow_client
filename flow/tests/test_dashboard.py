# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import json

import frappe
from frappe.desk.desktop import get_desktop_page
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get as chart_data
from frappe.desk.doctype.number_card.number_card import get_result
from frappe.tests import IntegrationTestCase

from flow.tests.usage_records import make_chat, make_user

MANAGER = "flow-dashboard-manager@example.com"
CLERK = "flow-dashboard-clerk@example.com"
CARDS = ("Flow Chats This Week", "Flow Failed Runs", "Flow Thumbs Down", "Flow Enabled Agents")
CHART = "Flow Runs Per Day"


class TestFlowDashboard(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		self.addCleanup(frappe.set_user, "Administrator")
		self.site_chats_before = _card("Flow Chats This Week")
		self.site_runs_before = _runs_on_chart()
		make_user(MANAGER, role="System Manager")
		make_user(CLERK, role="Desk User")
		make_chat(MANAGER)
		make_chat(CLERK, status="Failed")
		make_chat(CLERK, feedback="Down")
		make_chat(CLERK, status="Failed", days_ago=10)
		make_chat(CLERK, feedback="Down", days_ago=40)
		make_chat(CLERK, status="Failed", feedback="Down", source="Trigger")

	def test_a_desk_user_counts_only_their_own_chats(self):
		frappe.set_user(CLERK)

		self.assertEqual(_card("Flow Chats This Week"), 2)

	def test_a_system_manager_counts_the_whole_site(self):
		frappe.set_user(MANAGER)

		self.assertEqual(_card("Flow Chats This Week"), self.site_chats_before + 3)

	def test_failed_runs_count_the_last_seven_days(self):
		frappe.set_user(CLERK)

		self.assertEqual(_card("Flow Failed Runs"), 1)

	def test_thumbs_down_count_the_last_thirty_days(self):
		frappe.set_user(CLERK)

		self.assertEqual(_card("Flow Thumbs Down"), 1)

	def test_enabled_agents_leave_out_disabled_ones(self):
		model = _make_model()
		enabled_before = _card("Flow Enabled Agents")
		_make_agent("Dashboard On Agent", model, enabled=1)
		_make_agent("Dashboard Off Agent", model, enabled=0)

		self.assertEqual(_card("Flow Enabled Agents"), enabled_before + 1)

	def test_runs_per_day_follow_each_persons_access(self):
		frappe.set_user(CLERK)
		clerk_runs = _runs_on_chart()
		frappe.set_user(MANAGER)

		self.assertEqual((clerk_runs, _runs_on_chart()), (3, self.site_runs_before + 4))

	def test_the_flow_workspace_shows_the_cards_the_chart_and_the_report(self):
		workspace = frappe.get_doc("Workspace", "Flow")

		self.assertEqual(tuple(card.number_card_name for card in workspace.number_cards), CARDS)
		self.assertEqual([chart.chart_name for chart in workspace.charts], [CHART])
		self.assertIn("Flow Usage", [link.link_to for link in workspace.links if link.link_type == "Report"])

	def test_every_usage_block_names_a_widget_by_the_label_desk_matches_on(self):
		workspace = frappe.get_doc("Workspace", "Flow")
		blocks = json.loads(workspace.content)

		self.assertEqual(
			(
				[block["data"]["number_card_name"] for block in blocks if block["type"] == "number_card"],
				[block["data"]["chart_name"] for block in blocks if block["type"] == "chart"],
			),
			([card.label for card in workspace.number_cards], [chart.label for chart in workspace.charts]),
		)

	def test_a_desk_user_sees_the_usage_section_without_the_report_link(self):
		frappe.set_user(CLERK)

		page = get_desktop_page(json.dumps({"name": "Flow", "title": "Flow", "public": 1}))
		cards = tuple(card.get("number_card_name") for card in page["number_cards"]["items"])
		charts = [chart.get("chart_name") for chart in page["charts"]["items"]]
		links = [link.get("link_to") for card in page["cards"]["items"] for link in card.get("links")]

		self.assertEqual(
			(cards, charts, "Flow Session" in links, "Flow Usage" in links), (CARDS, [CHART], True, False)
		)


def _card(name: str) -> int:
	card = frappe.get_doc("Number Card", name)
	return int(get_result(card.as_dict(), card.filters_json))


def _runs_on_chart() -> int:
	return sum(chart_data(chart_name=CHART, refresh=1)["datasets"][0]["values"])


def _make_model() -> str:
	return (
		frappe.get_doc(
			{
				"doctype": "Flow Model",
				"title": "Dashboard Test Model",
				"model_id": "openai/gpt-4o-mini",
				"enabled": 1,
			}
		)
		.insert()
		.name
	)


def _make_agent(title: str, model: str, enabled: int) -> None:
	frappe.get_doc(
		{
			"doctype": "Flow Agent",
			"title": title,
			"model": model,
			"instructions": "Made-up agent for the dashboard test.",
			"enabled": enabled,
		}
	).insert()
