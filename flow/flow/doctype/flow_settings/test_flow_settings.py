# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from flow.assistant.assistant import ASSISTANT_AGENT_TITLE

CLERK = "flow-settings-clerk@example.com"
MANAGER = "flow-settings-manager@example.com"


class TestFlowSettings(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_chat_icon_is_on_for_a_site_that_never_saved_flow_settings(self):
		frappe.db.delete("Singles", {"doctype": "Flow Settings"})

		self.assertEqual(frappe.get_doc("Flow Settings").show_chat_icon, 1)

	def test_only_a_system_manager_can_change_flow_settings(self):
		_make_user(MANAGER, role="System Manager")
		_make_user(CLERK, role="Desk User")

		self.assertTrue(frappe.has_permission("Flow Settings", "write", user=MANAGER))
		self.assertFalse(frappe.has_permission("Flow Settings", "write", user=CLERK))

	def test_form_knows_flow_is_not_set_up_without_an_enabled_flow_model(self):
		frappe.db.delete("Flow Agent", {"name": ASSISTANT_AGENT_TITLE})

		self.assertFalse(_flow_is_set_up_on_the_form())

	def test_form_knows_flow_is_set_up_once_an_enabled_flow_model_exists(self):
		frappe.db.delete("Flow Agent", {"name": ASSISTANT_AGENT_TITLE})

		frappe.get_doc(
			{
				"doctype": "Flow Model",
				"title": "Flow Settings Test Model",
				"model_id": "openai/gpt-4o-mini",
				"enabled": 1,
			}
		).insert()

		self.assertTrue(_flow_is_set_up_on_the_form())


def _flow_is_set_up_on_the_form() -> bool:
	settings = frappe.get_doc("Flow Settings")
	settings.run_method("onload")
	return settings.get_onload("flow_is_set_up")


def _make_user(email: str, role: str) -> None:
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
		}
	).insert(ignore_permissions=True)
	user.add_roles(role)
