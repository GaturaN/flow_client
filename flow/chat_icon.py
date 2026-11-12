# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from flow.assistant.assistant import assistant_is_ready

USER_SWITCH = "flow_show_chat_icon"

USER_SWITCH_FIELD = {
	"User": [
		{
			"fieldname": USER_SWITCH,
			"fieldtype": "Check",
			"label": "Show Flow Chat Icon",
			"default": "1",
			"insert_after": "notifications",
			"module": "Flow",
			"description": "Shows the Flow chat icon in the bottom-right corner. Has no effect while Flow Settings → Show Chat Icon is off.",
		}
	]
}


def chat_icon_state_for(user: str) -> dict[str, bool]:
	allowed = _site_allows_chat_icon()
	return {"allowed": allowed, "wanted": allowed and _user_switch_is_on(user)}


def add_user_switch() -> None:
	create_custom_fields(USER_SWITCH_FIELD)


def _site_allows_chat_icon() -> bool:
	return _site_is_migrated_for_chat_icon() and _site_switch_is_on() and assistant_is_ready()


def _site_is_migrated_for_chat_icon() -> bool:
	return frappe.db.has_column("User", USER_SWITCH)


def _site_switch_is_on() -> bool:
	return bool(frappe.get_doc("Flow Settings").show_chat_icon)


def _user_switch_is_on(user: str) -> bool:
	return bool(frappe.db.get_value("User", user, USER_SWITCH))
