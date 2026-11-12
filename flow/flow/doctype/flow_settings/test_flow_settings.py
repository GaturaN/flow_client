# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

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
