# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import frappe

from flow.chat_icon import chat_icon_state_for
from flow.knowledge.extract import FILE_EXTENSIONS


def boot_session(bootinfo):
	# Single source of truth for file types the ingest pipeline can extract
	bootinfo.flow_supported_file_types = sorted(FILE_EXTENSIONS)
	bootinfo.flow_chat_icon = chat_icon_state_for(frappe.session.user)
