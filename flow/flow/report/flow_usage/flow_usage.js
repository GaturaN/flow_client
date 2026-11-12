// Copyright (c) 2026, Frappe Technologies and contributors
// License: MIT. See LICENSE

const SYSTEM_MANAGER_ONLY_FILTERS = ["show", "user"];

frappe.query_reports["Flow Usage"] = {
	filters: [
		{
			fieldname: "period",
			label: __("Period"),
			fieldtype: "Select",
			options: ["Last 7 days", "Last 30 days", "Last 90 days"],
			default: "Last 7 days",
			reqd: 1,
		},
		{
			fieldname: "show",
			label: __("Show"),
			fieldtype: "Select",
			options: ["Whole site", "Just me"],
			default: "Whole site",
		},
		{
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User",
		},
	],
	onload(report) {
		if (frappe.user.has_role("System Manager")) return;
		SYSTEM_MANAGER_ONLY_FILTERS.forEach((fieldname) =>
			report.get_filter(fieldname).toggle(false)
		);
	},
};
