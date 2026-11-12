# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

from datetime import date

import frappe
from frappe import _
from frappe.query_builder import Case
from frappe.query_builder.functions import Count, Date, Sum
from frappe.utils import add_days, date_diff, formatdate, getdate, nowdate

REPORT_MANAGER_ROLE = "System Manager"
JUST_ME = "Just me"
PERIOD_DAYS = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
DEFAULT_PERIOD = "Last 7 days"
CHAT_SOURCE = "Manual"
USER_COLUMN_WIDTH = 260
COUNT_COLUMN_WIDTH = 130


def execute(filters: dict | None = None):
	filters = frappe._dict(filters or {})
	owner = owner_in_scope(filters)
	since = _first_day_of(filters.period)
	rows = _usage_by_user(owner, since)
	return _columns(), rows, None, _runs_per_day_chart(owner, since), _summary(rows)


def owner_in_scope(filters: frappe._dict) -> str | None:
	if REPORT_MANAGER_ROLE not in frappe.get_roles():
		return frappe.session.user
	if filters.get("user"):
		return filters.user
	if filters.get("show") == JUST_ME:
		return frappe.session.user
	return None


def _first_day_of(period: str | None) -> date:
	days = PERIOD_DAYS.get(period, PERIOD_DAYS[DEFAULT_PERIOD])
	return getdate(add_days(nowdate(), 1 - days))


def _usage_by_user(owner: str | None, since: date) -> list[dict]:
	chats = _chats_by_user(owner, since)
	runs = _runs_by_user(owner, since)
	users = sorted(set(chats) | set(runs), key=lambda user: (-chats.get(user, 0), user))
	return [
		{
			"user": user,
			"chats": chats.get(user, 0),
			"runs": int(runs.get(user, {}).get("runs") or 0),
			"failed_runs": int(runs.get(user, {}).get("failed_runs") or 0),
			"thumbs_down": int(runs.get(user, {}).get("thumbs_down") or 0),
		}
		for user in users
	]


def _chats_by_user(owner: str | None, since: date) -> dict[str, int]:
	session = frappe.qb.DocType("Flow Session")
	query = (
		frappe.qb.from_(session)
		.select(session.owner, Count("*").as_("chats"))
		.where(_manual_rows_since(session, owner, since))
		.groupby(session.owner)
	)
	return {row.owner: row.chats for row in query.run(as_dict=True)}


def _runs_by_user(owner: str | None, since: date) -> dict[str, dict]:
	run = frappe.qb.DocType("Flow Run")
	failed_runs = Sum(Case().when(run.status == "Failed", 1).else_(0))
	thumbs_down = Sum(Case().when(run.feedback_rating == "Down", 1).else_(0))
	query = (
		frappe.qb.from_(run)
		.select(
			run.owner,
			Count("*").as_("runs"),
			failed_runs.as_("failed_runs"),
			thumbs_down.as_("thumbs_down"),
		)
		.where(_manual_rows_since(run, owner, since))
		.groupby(run.owner)
	)
	return {row.owner: row for row in query.run(as_dict=True)}


def _runs_per_day_chart(owner: str | None, since: date) -> dict:
	run = frappe.qb.DocType("Flow Run")
	day = Date(run.creation)
	query = (
		frappe.qb.from_(run).select(day, Count("*")).where(_manual_rows_since(run, owner, since)).groupby(day)
	)
	runs_on = {getdate(on): count for on, count in query.run()}
	days = [getdate(add_days(since, offset)) for offset in range(date_diff(nowdate(), since) + 1)]
	return {
		"data": {
			"labels": [formatdate(on) for on in days],
			"datasets": [{"name": _("Runs"), "values": [runs_on.get(on, 0) for on in days]}],
		},
		"type": "bar",
	}


def _manual_rows_since(table, owner: str | None, since: date):
	criterion = (table.source == CHAT_SOURCE) & (table.creation >= since)
	return criterion & (table.owner == owner) if owner else criterion


def _columns() -> list[dict]:
	return [
		{
			"fieldname": "user",
			"label": _("User"),
			"fieldtype": "Link",
			"options": "User",
			"width": USER_COLUMN_WIDTH,
		},
		{"fieldname": "chats", "label": _("Chats"), "fieldtype": "Int", "width": COUNT_COLUMN_WIDTH},
		{"fieldname": "runs", "label": _("Runs"), "fieldtype": "Int", "width": COUNT_COLUMN_WIDTH},
		{
			"fieldname": "failed_runs",
			"label": _("Failed runs"),
			"fieldtype": "Int",
			"width": COUNT_COLUMN_WIDTH,
		},
		{
			"fieldname": "thumbs_down",
			"label": _("Thumbs down"),
			"fieldtype": "Int",
			"width": COUNT_COLUMN_WIDTH,
		},
	]


def _summary(rows: list[dict]) -> list[dict]:
	return [
		_total(_("Chats"), rows, "chats"),
		_total(_("Runs"), rows, "runs"),
		_total(_("Failed runs"), rows, "failed_runs"),
		_total(_("Thumbs down"), rows, "thumbs_down"),
	]


def _total(label: str, rows: list[dict], fieldname: str) -> dict:
	return {"label": label, "value": sum(row[fieldname] for row in rows), "datatype": "Int"}
