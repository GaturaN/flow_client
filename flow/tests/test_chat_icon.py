# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import os
import re
from unittest.mock import patch

import frappe
from frappe.core.doctype.navbar_settings.navbar_settings import sync_standard_items
from frappe.installer import _delete_linked_documents
from frappe.model.document import Document
from frappe.tests import IntegrationTestCase

from flow.assistant.assistant import ASSISTANT_AGENT_TITLE
from flow.boot import boot_session
from flow.chat_icon import USER_SWITCH, add_user_switch, chat_icon_state_for

CLERK = "chat-icon-clerk@example.com"
ALLOWED_AND_WANTED = {"allowed": True, "wanted": True}
NOT_ALLOWED = {"allowed": False, "wanted": False}
WAY_BACK_LABEL = "Show Flow chat icon"
PANEL_METHOD_CALL = re.compile(r"frappe\.flow\??\.panel\??\.(\w+)(?:\?\.)?\(")


class TestChatIconRule(IntegrationTestCase):
	def setUp(self):
		_make_desk_user(CLERK)
		_set_up_flow()
		frappe.db.set_single_value("Flow Settings", "show_chat_icon", 1)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_shows_when_both_switches_are_on_and_flow_is_ready(self):
		self.assertEqual(chat_icon_state_for(CLERK), ALLOWED_AND_WANTED)

	def test_shows_on_a_site_that_never_saved_flow_settings(self):
		frappe.db.delete("Singles", {"doctype": "Flow Settings"})

		self.assertEqual(chat_icon_state_for(CLERK), ALLOWED_AND_WANTED)

	def test_user_who_switched_it_off_keeps_the_panel_toggle(self):
		frappe.db.set_value("User", CLERK, USER_SWITCH, 0)
		frappe.set_user(CLERK)

		self.assertEqual(chat_icon_state_for(CLERK), {"allowed": True, "wanted": False})

	def test_hides_when_flow_settings_switches_it_off(self):
		frappe.db.set_single_value("Flow Settings", "show_chat_icon", 0)

		self.assertEqual(chat_icon_state_for(CLERK), NOT_ALLOWED)

	def test_hides_until_flow_is_set_up(self):
		frappe.db.delete("Flow Agent", {"name": ASSISTANT_AGENT_TITLE})

		self.assertEqual(chat_icon_state_for(CLERK), NOT_ALLOWED)

	def test_hides_when_the_flow_agent_is_disabled(self):
		frappe.db.set_value("Flow Agent", ASSISTANT_AGENT_TITLE, "enabled", 0)

		self.assertEqual(chat_icon_state_for(CLERK), NOT_ALLOWED)

	def test_hides_when_the_flow_agents_model_is_disabled(self):
		model = frappe.db.get_value("Flow Agent", ASSISTANT_AGENT_TITLE, "model")
		frappe.db.set_value("Flow Model", model, "enabled", 0)

		self.assertEqual(chat_icon_state_for(CLERK), NOT_ALLOWED)

	def test_hides_instead_of_failing_before_the_site_is_migrated(self):
		with patch("flow.chat_icon.USER_SWITCH", "flow_column_added_by_a_later_migrate"):
			self.assertEqual(chat_icon_state_for(CLERK), NOT_ALLOWED)

	def test_boot_tells_the_desk_whether_to_show_the_icon(self):
		frappe.set_user(CLERK)
		bootinfo = frappe._dict()

		boot_session(bootinfo)

		self.assertEqual(bootinfo.flow_chat_icon, ALLOWED_AND_WANTED)


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

	def test_install_and_every_migrate_add_the_switch(self):
		self.assertIn("flow.chat_icon.add_user_switch", frappe.get_hooks("after_install", app_name="flow"))
		self.assertIn("flow.chat_icon.add_user_switch", frappe.get_hooks("after_migrate", app_name="flow"))

	def test_every_migrate_keeps_a_single_switch(self):
		add_user_switch()

		self.assertEqual(frappe.db.count("Custom Field", {"dt": "User", "fieldname": USER_SWITCH}), 1)

	def test_uninstalling_flow_removes_the_switch(self):
		_delete_linked_documents("Flow", {"Custom Field": "module"}, dry_run=False)

		self.assertFalse(frappe.db.exists("Custom Field", {"dt": "User", "fieldname": USER_SWITCH}))


class TestWayBackMenuItem(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Navbar Item", {"parent": "Navbar Settings", "item_label": WAY_BACK_LABEL})

	def tearDown(self):
		frappe.db.rollback()

	def test_every_migrate_puts_the_way_back_in_the_sidebar_menu(self):
		sync_standard_items()

		row = _way_back_row()
		self.assertEqual((row.item_type, row.is_standard, row.icon), ("Action", 1, "message-circle"))

	def test_every_migrate_keeps_a_single_way_back_row(self):
		sync_standard_items()
		sync_standard_items()

		labels = [row.item_label for row in frappe.get_doc("Navbar Settings").settings_dropdown]
		self.assertEqual(labels.count(WAY_BACK_LABEL), 1)

	def test_install_puts_the_way_back_in_the_sidebar_menu(self):
		self.assertIn(
			"frappe.core.doctype.navbar_settings.navbar_settings.sync_standard_items",
			frappe.get_hooks("after_install", app_name="flow"),
		)

	def test_an_older_flow_bundle_cannot_break_the_menu(self):
		sync_standard_items()

		self.assertNotRegex(_way_back_row().condition, r"\w\(")

	def test_the_way_back_calls_only_what_the_panel_has(self):
		sync_standard_items()
		row = _way_back_row()
		called = PANEL_METHOD_CALL.findall(row.condition + row.action)

		self.assertEqual(called, ["isChatIconOff", "turnChatIconOn"])
		for method in called:
			self.assertIn(f"\n\t{method}() {{", _panel_source())


def _way_back_row() -> Document:
	rows = frappe.get_doc("Navbar Settings").settings_dropdown
	return next(row for row in rows if row.item_label == WAY_BACK_LABEL)


def _panel_source() -> str:
	path = os.path.join(frappe.get_app_path("flow"), "..", "frontend", "src", "main.js")
	with open(path) as source:
		return source.read()


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


def _set_up_flow() -> None:
	frappe.get_doc(
		{
			"doctype": "Flow Model",
			"title": "Chat Icon Test Model",
			"model_id": "openai/gpt-4o-mini",
			"enabled": 1,
		}
	).insert()
