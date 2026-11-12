import {
	FLOATING_SIZE,
	PANEL_PLACEMENTS,
	SMALLEST_DOCKING_VIEWPORT_WIDTH,
	clampDockedWidth,
	clampFloatingWindow,
} from "@/lib/panelLayout";

const ABOVE_CHAT_ICON_BELOW_DIALOGS = "1040";
const GRIP_ABOVE_PANEL_CONTENT = "10";
const DOCKED_GRIP_WIDTH = "6px";
const DOCKED_WIDTH_VARIABLE = "--flow-docked-width";
const EMAIL_COMPOSER_CARD = ".email-composer-modal:not(.expanded) .modal-dialog";
const EMAIL_COMPOSER_EDGE_GAPS = "40px";
const DESK_ITEMS_PINNED_TO_WINDOW_EDGE = [
	".scroll-to-top.show",
	".modal-minimize .modal-dialog",
	EMAIL_COMPOSER_CARD,
];
const CONTROLS = "button, a, input, textarea, select";
const PRIMARY_BUTTON = 0;
const FLOATING_CORNER_RADIUS = "12px";
const FLOATING_BORDER = "1px solid var(--border-color, #e4e4e7)";
const FLOATING_SHADOW = "var(--shadow-2xl, 0 12px 40px rgba(0, 0, 0, 0.18))";
const FLOATING_MAX_PERCENT = FLOATING_SIZE.maxShareOfViewport * 100;

const PLACEMENT_STYLES = {
	[PANEL_PLACEMENTS.DOCKED]: ({ dockedWidth }) => ({
		position: "relative",
		flex: `0 0 ${dockedWidth}px`,
		width: `${dockedWidth}px`,
		height: "100dvh",
	}),
	[PANEL_PLACEMENTS.FLOATING]: ({ floatingWindow }) => ({
		position: "fixed",
		...edgeOppositeTheResizeGrip(floatingWindow),
		top: `${floatingWindow.top}px`,
		width: `${floatingWindow.width}px`,
		height: `${floatingWindow.height}px`,
		minWidth: `min(${FLOATING_SIZE.minWidth}px, ${FLOATING_MAX_PERCENT}vw)`,
		minHeight: `min(${FLOATING_SIZE.minHeight}px, ${FLOATING_MAX_PERCENT}vh)`,
		maxWidth: `${FLOATING_MAX_PERCENT}vw`,
		maxHeight: `${FLOATING_MAX_PERCENT}vh`,
		boxSizing: "border-box",
		resize: "both",
		overflow: "hidden",
		zIndex: ABOVE_CHAT_ICON_BELOW_DIALOGS,
		border: FLOATING_BORDER,
		borderRadius: FLOATING_CORNER_RADIUS,
		boxShadow: FLOATING_SHADOW,
	}),
	[PANEL_PLACEMENTS.COVERING]: () => ({
		position: "fixed",
		inset: "0",
		zIndex: ABOVE_CHAT_ICON_BELOW_DIALOGS,
	}),
};

export function currentViewport() {
	return { width: window.innerWidth, height: window.innerHeight };
}

export class PanelFrame {
	constructor(root, { onDockedWidthChange, onFloatingWindowChange }) {
		this.root = root;
		this.placement = null;
		this.placedWindow = null;
		this.visible = false;
		this.grip = this._addDockedGrip(onDockedWidthChange);
		this._moveByHeader(onFloatingWindowChange);
		this._followCornerResize(onFloatingWindowChange);
		this._keepPinnedDeskItemsBesideDockedChat();
	}

	place(fitted, visible) {
		const isDocked = fitted.placement === PANEL_PLACEMENTS.DOCKED;
		this.placement = fitted.placement;
		this.placedWindow = fitted.floatingWindow ?? null;
		this.visible = visible;
		this.root.style.cssText = "";
		Object.assign(this.root.style, PLACEMENT_STYLES[fitted.placement](fitted), {
			display: visible ? "" : "none",
		});
		this.grip.style.display = isDocked ? "" : "none";
		const dockedWidth = visible && isDocked ? fitted.dockedWidth : 0;
		document.documentElement.style.setProperty(DOCKED_WIDTH_VARIABLE, `${dockedWidth}px`);
	}

	_keepPinnedDeskItemsBesideDockedChat() {
		const dockedWidth = `var(${DOCKED_WIDTH_VARIABLE}, 0px)`;
		const style = document.createElement("style");
		style.textContent = `@media (min-width: ${SMALLEST_DOCKING_VIEWPORT_WIDTH}px) {
			${DESK_ITEMS_PINNED_TO_WINDOW_EDGE.join(", ")} { margin-inline-end: ${dockedWidth}; }
			${EMAIL_COMPOSER_CARD} { max-width: calc(100vw - ${EMAIL_COMPOSER_EDGE_GAPS} - ${dockedWidth}); }
		}`;
		document.head.appendChild(style);
	}

	_addDockedGrip(onDockedWidthChange) {
		const grip = document.createElement("div");
		Object.assign(grip.style, {
			position: "absolute",
			top: "0",
			insetInlineStart: "0",
			width: DOCKED_GRIP_WIDTH,
			height: "100%",
			cursor: "ew-resize",
			touchAction: "none",
			zIndex: GRIP_ABOVE_PANEL_CONTENT,
		});
		this.root.appendChild(grip);
		grip.addEventListener("pointerdown", (event) =>
			this._drag(event, (move) => {
				const viewport = currentViewport();
				onDockedWidthChange(
					clampDockedWidth(dockedWidthAt(move.clientX, viewport.width), viewport.width)
				);
			})
		);
		return grip;
	}

	_moveByHeader(onFloatingWindowChange) {
		this.root.addEventListener("pointerdown", (event) => {
			if (this.placement !== PANEL_PLACEMENTS.FLOATING || !this._grabsHeader(event)) return;
			const start = { x: event.clientX, y: event.clientY, window: this._currentWindow() };
			this._drag(event, (move) => {
				const moved = {
					...start.window,
					left: start.window.left + move.clientX - start.x,
					top: start.window.top + move.clientY - start.y,
				};
				onFloatingWindowChange(clampFloatingWindow(moved, currentViewport()));
			});
		});
	}

	_followCornerResize(onFloatingWindowChange) {
		new ResizeObserver(() => {
			if (this.placement !== PANEL_PLACEMENTS.FLOATING || !this.visible) return;
			const current = this._currentWindow();
			if (hasSameSize(current, this.placedWindow)) return;
			onFloatingWindowChange(clampFloatingWindow(current, currentViewport()));
		}).observe(this.root);
	}

	_grabsHeader(event) {
		const header = this.root.querySelector("header");
		if (!header?.contains(event.target) || event.target.closest(CONTROLS)) return false;
		return isWithin(event.target.getBoundingClientRect(), header.getBoundingClientRect());
	}

	_currentWindow() {
		const box = this.root.getBoundingClientRect();
		return {
			left: Math.round(box.left),
			top: Math.round(box.top),
			width: Math.round(box.width),
			height: Math.round(box.height),
		};
	}

	_drag(event, onMove) {
		if (event.button !== PRIMARY_BUTTON) return;
		event.preventDefault();
		event.currentTarget.setPointerCapture(event.pointerId);
		document.body.style.userSelect = "none";
		const onEnd = () => {
			document.removeEventListener("pointermove", onMove);
			document.removeEventListener("pointerup", onEnd);
			document.removeEventListener("pointercancel", onEnd);
			document.body.style.userSelect = "";
		};
		document.addEventListener("pointermove", onMove);
		document.addEventListener("pointerup", onEnd);
		document.addEventListener("pointercancel", onEnd);
	}
}

function hasSameSize(floatingWindow, otherWindow) {
	return (
		floatingWindow.width === otherWindow?.width &&
		floatingWindow.height === otherWindow?.height
	);
}

function edgeOppositeTheResizeGrip({ left, width }) {
	if (!isRightToLeft()) return { left: `${left}px` };
	return { right: `${window.innerWidth - left - width}px` };
}

function dockedWidthAt(pointerX, viewportWidth) {
	return isRightToLeft() ? pointerX : viewportWidth - pointerX;
}

function isRightToLeft() {
	return document.documentElement.dir === "rtl";
}

function isWithin(inner, outer) {
	return (
		inner.left >= outer.left &&
		inner.right <= outer.right &&
		inner.top >= outer.top &&
		inner.bottom <= outer.bottom
	);
}
