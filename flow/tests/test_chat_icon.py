# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import frappe
from frappe.installer import _delete_linked_documents
from frappe.tests import IntegrationTestCase

from flow.chat_icon import USER_SWITCH, add_user_switch

CLERK = "chat-icon-clerk@example.com"


class TestUserSwitch(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_switch_sits_after_notifications_in_navigation_settings(self):
		fieldnames = [df.fieldname for df in frappe.get_meta("User").fields]

		self.assertEqual(fieldnames[fieldnames.index(USER_SWITCH) - 1], "notifications")

	def test_users_who_existed_before_flow_have_the_icon_on(self):
		self.assertEqual(frappe.db.get_value("User", "Administrator", USER_SWITCH), 1)

	def test_a_new_user_starts_with_the_icon_on(self):
		_make_desk_user(CLERK)

		self.assertEqual(frappe.db.get_value("User", CLERK, USER_SWITCH), 1)

	def test_a_desk_user_can_switch_their_own_icon_off(self):
		_make_desk_user(CLERK)
		frappe.set_user(CLERK)

		user = frappe.get_doc("User", CLERK)
		user.set(USER_SWITCH, 0)
		user.save()

		self.assertEqual(frappe.db.get_value("User", CLERK, USER_SWITCH), 0)

	def test_every_migrate_keeps_a_single_switch(self):
		add_user_switch()

		self.assertEqual(frappe.db.count("Custom Field", {"dt": "User", "fieldname": USER_SWITCH}), 1)

	def test_uninstalling_flow_removes_the_switch(self):
		_delete_linked_documents("Flow", {"Custom Field": "module"}, dry_run=False)

		self.assertFalse(frappe.db.exists("Custom Field", {"dt": "User", "fieldname": USER_SWITCH}))


def _make_desk_user(email: str) -> None:
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
		}
	).insert(ignore_permissions=True)
	user.add_roles("Desk User")
