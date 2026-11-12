# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import json
from pathlib import Path
from xml.etree import ElementTree

import frappe
from frappe.apps import get_apps
from frappe.boot import get_app_data
from frappe.tests import IntegrationTestCase

FLOW_TILE = {
	"name": "flow",
	"logo": "/assets/flow/images/flow-logo.svg",
	"title": "Flow",
	"route": "/desk/flow",
}
CLERK = "apps-screen-clerk@example.com"


class TestAppsScreen(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_a_desk_user_sees_the_flow_tile_on_the_apps_screen(self):
		_make_desk_user(CLERK)
		frappe.set_user(CLERK)

		flow = next(app for app in _boot_app_data() if app["app_name"] == FLOW_TILE["name"])

		self.assertEqual(
			(flow["on_apps_screen"], flow["app_route"], flow["app_logo_url"]),
			(True, FLOW_TILE["route"], FLOW_TILE["logo"]),
		)

	def test_a_desk_user_gets_the_flow_tile_from_the_apps_list(self):
		_make_desk_user(CLERK)
		frappe.set_user(CLERK)

		self.assertEqual(_flow_tile_on(_apps_page()), FLOW_TILE)

	def test_flow_leaves_the_desk_logo_to_other_apps(self):
		self.assertEqual(frappe.get_hooks("app_logo_url", app_name="flow"), [])

	def test_desktop_icon_is_flows_app_icon(self):
		icon = json.loads(Path(frappe.get_app_path("flow", "desktop_icon", "flow.json")).read_text())
		identity = ("name", "label", "icon_type", "app", "hidden", "standard", "link", "logo_url")

		self.assertEqual(
			tuple(icon[key] for key in identity),
			("Flow", "Flow", "App", "flow", 0, 1, FLOW_TILE["route"], FLOW_TILE["logo"]),
		)

	def test_logo_declares_its_size(self):
		logo = ElementTree.parse(frappe.get_app_path("flow", "public", "images", "flow-logo.svg")).getroot()

		self.assertEqual((logo.get("width"), logo.get("height")), ("100", "100"))


def _apps_page() -> list[dict]:
	_forget_this_requests_cache()
	return get_apps()


def _boot_app_data() -> list[dict]:
	_forget_this_requests_cache()
	return get_app_data()


def _forget_this_requests_cache() -> None:
	request_cache = getattr(frappe.local, "request_cache", None)
	if request_cache is not None:
		request_cache.clear()


def _flow_tile_on(apps: list[dict]) -> dict | None:
	tile = next((app for app in apps if app["name"] == FLOW_TILE["name"]), None)
	return tile and {key: tile.get(key) for key in FLOW_TILE}


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
