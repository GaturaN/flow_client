// Copyright (c) 2026, Frappe Technologies and contributors
// License: MIT. See LICENSE

frappe.ui.form.on("Flow Settings", {
	refresh(frm) {
		const flow_is_ready = frm.doc.__onload?.flow_is_ready;
		frm.set_intro(
			flow_is_ready
				? ""
				: __(
						"Flow isn't ready, so the chat icon is hidden for everyone. The Flow agent and its Flow Model must both be enabled. Saving the first enabled Flow Model creates the agent."
				  ),
			"yellow"
		);
	},
});
