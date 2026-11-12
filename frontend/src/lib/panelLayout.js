export const PANEL_MODES = Object.freeze({ DOCKED: "docked", FLOATING: "floating" });
export const PANEL_PLACEMENTS = Object.freeze({ ...PANEL_MODES, COVERING: "covering" });

export const SMALLEST_DOCKING_VIEWPORT_WIDTH = 768;
export const DOCKED_WIDTH = Object.freeze({ min: 360, default: 420, maxShareOfViewport: 0.5 });
export const FLOATING_SIZE = Object.freeze({
	minWidth: 360,
	minHeight: 400,
	defaultWidth: 480,
	defaultHeight: 640,
	maxShareOfViewport: 0.9,
});
export const FLOATING_EDGE_GAP = 24;

const WINDOW_KEYS = ["left", "top", "width", "height"];

export function fitLayout(layout, viewport) {
	if (viewport.width < SMALLEST_DOCKING_VIEWPORT_WIDTH) {
		return { placement: PANEL_PLACEMENTS.COVERING };
	}
	return {
		placement: layout.mode,
		dockedWidth: clampDockedWidth(layout.dockedWidth, viewport.width),
		floatingWindow: clampFloatingWindow(
			layout.floatingWindow ?? defaultFloatingWindow(viewport),
			viewport
		),
	};
}

export function readLayout(saved) {
	return {
		mode: saved.mode === PANEL_MODES.FLOATING ? PANEL_MODES.FLOATING : PANEL_MODES.DOCKED,
		dockedWidth: Number.isFinite(saved.width) ? saved.width : DOCKED_WIDTH.default,
		floatingWindow: isWindow(saved.floating) ? saved.floating : null,
	};
}

export function clampDockedWidth(width, viewportWidth) {
	const widest = Math.floor(viewportWidth * DOCKED_WIDTH.maxShareOfViewport);
	return clamp(width, DOCKED_WIDTH.min, widest);
}

export function clampFloatingWindow(floatingWindow, viewport) {
	const width = clamp(
		floatingWindow.width,
		FLOATING_SIZE.minWidth,
		largestFloating(viewport.width)
	);
	const height = clamp(
		floatingWindow.height,
		FLOATING_SIZE.minHeight,
		largestFloating(viewport.height)
	);
	return {
		left: clamp(floatingWindow.left, 0, viewport.width - width),
		top: clamp(floatingWindow.top, 0, viewport.height - height),
		width,
		height,
	};
}

export function defaultFloatingWindow(viewport) {
	const size = clampFloatingWindow(
		{
			left: 0,
			top: 0,
			width: FLOATING_SIZE.defaultWidth,
			height: FLOATING_SIZE.defaultHeight,
		},
		viewport
	);
	return clampFloatingWindow(
		{
			...size,
			left: viewport.width - size.width - FLOATING_EDGE_GAP,
			top: viewport.height - size.height - FLOATING_EDGE_GAP,
		},
		viewport
	);
}

function largestFloating(viewportLength) {
	return Math.floor(viewportLength * FLOATING_SIZE.maxShareOfViewport);
}

function isWindow(value) {
	return WINDOW_KEYS.every((key) => Number.isFinite(value?.[key]));
}

function clamp(value, smallest, largest) {
	return Math.min(largest, Math.max(smallest, value));
}
