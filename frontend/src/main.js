import { createApp, watch } from "vue";
import App from "@/App.vue";
import { useStore } from "@/store";
import { readPanelState, writePanelState } from "@/lib/panelState";
import { PANEL_MODES, fitLayout, readLayout } from "@/lib/panelLayout";
import { PanelFrame, currentViewport } from "@/panelFrame";
import { ChatIcon } from "@/chatIcon";
import { saveChatIconSwitch } from "@/api/client";
import "@/index.css";

const PANEL_SHORTCUT = "ctrl+i";

// Panel injected into the Frappe desk. The Vue app (with real frappe-ui
// components) mounts inside #flow-root; all bundle CSS is scoped to that id so
// nothing leaks onto the desk.
class FlowPanel {
	constructor() {
		const saved = readPanelState();
		this.visible = Boolean(saved.open);
		this.layout = readLayout(saved);

		this._mount();
		this._syncTheme();
		this._registerShortcut();
		this._mountChatIcon();
		this._render();

		window.addEventListener("resize", () => this._render());
		watch(this.store.sessionName, () => this._persist());
	}

	_mount() {
		this.store = useStore();

		this.root = document.createElement("div");
		this.root.id = "flow-root";
		document.body.appendChild(this.root);

		this.app = createApp(App, {
			onClose: () => this.hide(),
			onTogglePopOut: () => this.togglePopOut(),
		});
		this.app.mount(this.root);

		this.frame = new PanelFrame(this.root, {
			onDockedWidthChange: (dockedWidth) => this._changeLayout({ dockedWidth }),
			onFloatingWindowChange: (floatingWindow) => this._changeLayout({ floatingWindow }),
		});
	}

	// Mirror the desk's light/dark theme onto the panel root so scoped tokens
	// resolve to the right palette.
	_syncTheme() {
		const apply = () => {
			const theme = document.documentElement.getAttribute("data-theme") || "light";
			this.root.setAttribute("data-theme", theme);
		};
		apply();
		new MutationObserver(apply).observe(document.documentElement, {
			attributes: true,
			attributeFilter: ["data-theme"],
		});
	}

	_registerShortcut() {
		frappe.ui.keys.add_shortcut({
			shortcut: PANEL_SHORTCUT,
			action: () => this.toggle(),
			description: __("Toggle Flow panel"),
			ignore_inputs: true,
		});
	}

	_mountChatIcon() {
		const chatIcon = frappe.boot.flow_chat_icon;
		if (!chatIcon?.allowed) return;
		this.chatIcon = new ChatIcon({
			onOpen: () => this.show(),
			onTurnOff: () => (this.store.chatIconWanted.value = false),
			shortcutLabel: this._shortcutLabel(),
		});
		this.chatIcon.setPanelOpen(this.visible);
		this.chatIcon.setWanted(chatIcon.wanted);
		this.store.chatIconAllowed.value = true;
		this.store.chatIconWanted.value = chatIcon.wanted;
		watch(this.store.chatIconWanted, (wanted) => this._applyChatIconChoice(wanted));
	}

	_applyChatIconChoice(wanted) {
		this.chatIcon.setWanted(wanted);
		saveChatIconSwitch(wanted).then(() =>
			frappe.ui.toast({
				message: wanted
					? __("Chat icon turned on.")
					: __("Chat icon turned off. Press {0} to open Flow and turn it back on.", [
							this._shortcutLabel(),
					  ]),
			})
		);
	}

	_shortcutLabel() {
		return frappe.ui.keys.get_shortcut_label(PANEL_SHORTCUT);
	}

	show() {
		this.visible = true;
		this._render();
		this.store.restoreSession();
		this._persist();
		this.chatIcon?.setPanelOpen(true);
	}

	hide() {
		this.visible = false;
		this._render();
		this._persist();
		this.chatIcon?.setPanelOpen(false);
	}

	toggle() {
		this.visible ? this.hide() : this.show();
	}

	togglePopOut() {
		const isDocked = this.layout.mode === PANEL_MODES.DOCKED;
		this._changeLayout({ mode: isDocked ? PANEL_MODES.FLOATING : PANEL_MODES.DOCKED });
	}

	_changeLayout(change) {
		this.layout = { ...this.layout, ...change };
		this._render();
		this._persist();
	}

	_render() {
		const fitted = fitLayout(this.layout, currentViewport());
		this.frame.place(fitted, this.visible);
		this.store.panelPlacement.value = fitted.placement;
	}

	_persist() {
		writePanelState({
			open: this.visible,
			mode: this.layout.mode,
			width: this.layout.dockedWidth,
			floating: this.layout.floatingWindow,
			session: this.store.sessionName.value,
		});
	}
}

frappe.provide("frappe.flow");
$(document).on("app_ready", () => {
	frappe.flow.panel = new FlowPanel();
});
