# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

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


def add_user_switch() -> None:
	create_custom_fields(USER_SWITCH_FIELD)
