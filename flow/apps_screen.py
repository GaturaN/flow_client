# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import frappe

DESK_USER_TYPE = "System User"


def is_desk_user() -> bool:
	return frappe.get_cached_value("User", frappe.session.user, "user_type") == DESK_USER_TYPE
