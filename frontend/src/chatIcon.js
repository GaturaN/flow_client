const ICON_SIZE = 46;
const EDGE_GAP = 20;
const HIDE_BUTTON_SIZE = 24;
const HIDE_BUTTON_OVERHANG = -8;
const HIDE_BUTTON_FONT_SIZE = 14;
const HIDE_BUTTON_FADE = "opacity 0.12s ease";
const ABOVE_PAGE_BELOW_DIALOGS = 1030;
const TOUCH_SCREEN = "(hover: none)";

const DARK_FILL = "var(--ink-gray-9, #171717)";
const LIGHT_FILL = "var(--surface-base, #ffffff)";
const RAISED_SHADOW = "var(--shadow-lg, 0 4px 14px rgba(0, 0, 0, 0.18))";

const CHAT_BUBBLE = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>`;

export class ChatIcon {
	constructor({ onOpen }) {
		this.panelIsOpen = false;
		this.hiddenUntilRefresh = false;
		this.root = this._buildRoot(onOpen);
		document.body.appendChild(this.root);
	}

	setPanelOpen(isOpen) {
		this.panelIsOpen = isOpen;
		this._render();
	}

	_hideUntilRefresh() {
		this.hiddenUntilRefresh = true;
		this._render();
	}

	_render() {
		const visible = !this.panelIsOpen && !this.hiddenUntilRefresh;
		this.root.style.display = visible ? "block" : "none";
	}

	_buildRoot(onOpen) {
		const root = document.createElement("div");
		root.className = "flow-chat-icon";
		Object.assign(root.style, {
			position: "fixed",
			insetInlineEnd: `${EDGE_GAP}px`,
			bottom: `${EDGE_GAP}px`,
			zIndex: String(ABOVE_PAGE_BELOW_DIALOGS),
		});
		const hideButton = this._buildHideButton();
		root.append(this._buildOpenButton(onOpen), hideButton);
		this._revealOnHover(root, hideButton);
		return root;
	}

	_buildOpenButton(onOpen) {
		const button = document.createElement("button");
		button.type = "button";
		button.className = "flow-chat-icon-open";
		button.innerHTML = CHAT_BUBBLE;
		label(button, __("Chat with Flow (Ctrl+I)"));
		Object.assign(button.style, {
			width: `${ICON_SIZE}px`,
			height: `${ICON_SIZE}px`,
			borderRadius: "50%",
			border: "0",
			display: "grid",
			placeItems: "center",
			cursor: "pointer",
			background: DARK_FILL,
			color: LIGHT_FILL,
			boxShadow: RAISED_SHADOW,
		});
		button.addEventListener("click", onOpen);
		return button;
	}

	_buildHideButton() {
		const button = document.createElement("button");
		button.type = "button";
		button.className = "flow-chat-icon-hide";
		button.textContent = "×";
		label(button, __("Hide until the page is refreshed"));
		Object.assign(button.style, {
			position: "absolute",
			top: `${HIDE_BUTTON_OVERHANG}px`,
			insetInlineStart: `${HIDE_BUTTON_OVERHANG}px`,
			width: `${HIDE_BUTTON_SIZE}px`,
			height: `${HIDE_BUTTON_SIZE}px`,
			lineHeight: `${HIDE_BUTTON_SIZE}px`,
			padding: "0",
			borderRadius: "50%",
			border: "0",
			cursor: "pointer",
			fontSize: `${HIDE_BUTTON_FONT_SIZE}px`,
			background: LIGHT_FILL,
			color: DARK_FILL,
			boxShadow: RAISED_SHADOW,
			opacity: "0",
			transition: HIDE_BUTTON_FADE,
		});
		button.addEventListener("click", () => this._hideUntilRefresh());
		return button;
	}

	_revealOnHover(root, hideButton) {
		const reveal = () => (hideButton.style.opacity = "1");
		const conceal = () => (hideButton.style.opacity = "0");
		if (window.matchMedia(TOUCH_SCREEN).matches) {
			reveal();
			return;
		}
		root.addEventListener("mouseenter", reveal);
		root.addEventListener("mouseleave", conceal);
		root.addEventListener("focusin", reveal);
		root.addEventListener("focusout", conceal);
	}
}

function label(element, text) {
	element.title = text;
	element.setAttribute("aria-label", text);
}
