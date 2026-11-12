# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

from frappe.model.document import Document

from flow.assistant.assistant import assistant_exists


class FlowSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		show_chat_icon: DF.Check
	# end: auto-generated types

	def onload(self):
		self.set_onload("flow_is_set_up", assistant_exists())
