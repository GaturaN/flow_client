# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import frappe
from frappe.utils import add_days, now_datetime


def make_chat(
	owner: str,
	days_ago: int = 0,
	status: str = "Completed",
	feedback: str | None = None,
	source: str = "Manual",
) -> None:
	session = frappe.get_doc({"doctype": "Flow Session", "title": "Usage test", "source": source}).insert(
		ignore_permissions=True
	)
	run = frappe.get_doc(
		{
			"doctype": "Flow Run",
			"session": session.name,
			"source": source,
			"status": status,
			"error": "Made-up failure" if status == "Failed" else None,
			"feedback_rating": feedback,
		}
	).insert(ignore_permissions=True)
	started = add_days(now_datetime(), -days_ago)
	for doctype, name in (("Flow Session", session.name), ("Flow Run", run.name)):
		frappe.db.set_value(doctype, name, {"owner": owner, "creation": started}, update_modified=False)


def make_user(email: str, role: str) -> None:
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": email.split("@")[0],
			"send_welcome_email": 0,
		}
	).insert(ignore_permissions=True)
	user.add_roles(role)
