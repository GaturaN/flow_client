// Copyright (c) 2026, Frappe Technologies and contributors
// License: MIT. See LICENSE

frappe.ui.form.on("Flow Settings", {
	refresh(frm) {
		const flow_is_set_up = frm.doc.__onload?.flow_is_set_up;
		frm.set_intro(
			flow_is_set_up
				? ""
				: __(
						"Flow isn't set up yet, so the chat icon is hidden for everyone. Add an enabled Flow Model and it appears."
				  ),
			"yellow"
		);
	},
});
