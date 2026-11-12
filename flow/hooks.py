app_name = "flow"
app_title = "Flow"
app_publisher = "Shrihari Mahabal"
app_description = "Frappe Flow — native AI agents, tools, and triggers for Frappe"
app_email = "shriharimahabal08@gmail.com"
app_license = "agpl-3.0"

export_python_type_annotations = True

# Vite-built (frontend/src) AI panel bundle. Served directly from public/ — the
# /assets path bypasses the desk's esbuild pipeline. Run `yarn build` in the app root.
# /assets URLs get no cache-busting query from Frappe, so append ?v=<mtime>:
# the stable filename keeps the hook simple while a rebuild invalidates the cache.
import os as _os


def _flow_panel_asset(filename: str) -> str:
	path = _os.path.join(_os.path.dirname(__file__), "public", "flow_panel", filename)
	try:
		version = int(_os.path.getmtime(path))
	except OSError:
		version = 0
	return f"/assets/flow/flow_panel/{filename}?v={version}"


add_to_apps_screen = [
	{
		"name": app_name,
		"logo": "/assets/flow/images/flow-logo.svg",
		"title": app_title,
		"route": "/desk/flow",
		"has_permission": "flow.apps_screen.is_desk_user",
	}
]

standard_navbar_items = [
	{
		"item_label": "Show Flow chat icon",
		"item_type": "Action",
		"action": "frappe.flow.panel.turnChatIconOn()",
		"condition": "eval: frappe.flow?.panel?.isChatIconOff?.()",
		"icon": "message-circle",
		"is_standard": 1,
	}
]

app_include_js = [_flow_panel_asset("flow_panel.js")]
app_include_css = [_flow_panel_asset("flow_panel.css")]

doc_events = {
	"*": {
		"after_insert": "flow.triggers.dispatch",
		"on_update": "flow.triggers.dispatch",
		"on_submit": "flow.triggers.dispatch",
		"on_cancel": "flow.triggers.dispatch",
		"on_trash": "flow.triggers.dispatch",
	}
}

# Flow's references to other docs are bookkeeping — they must never block deleting
# the referenced doc. A knowledge chunk indexes a doc; a Flow Run records the doc a
# trigger acted on. The incremental sweep removes orphaned chunks afterwards.
# A session's Flow Model reference is historical bookkeeping and must not block deletion.
ignore_links_on_delete = ["Flow Knowledge Chunk", "Flow Run", "Flow Session"]

default_log_clearing_doctypes = {
	"Flow Session": 90,
}

scheduler_events = {
	"daily": [
		"flow.knowledge.ingest.sync_due_sources",
	],
	"cron": {
		"*/5 * * * *": [
			"flow.triggers.dispatch_scheduled",
		],
	},
}

after_install = [
	"flow.chat_icon.add_user_switch",
	"frappe.core.doctype.navbar_settings.navbar_settings.sync_standard_items",
]

after_migrate = ["flow.assistant.sync_builtin_assistant", "flow.chat_icon.add_user_switch"]

extend_bootinfo = "flow.boot.boot_session"
