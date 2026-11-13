import { describe, test } from "node:test";
import assert from "node:assert/strict";
import {
	PANEL_MODES,
	PANEL_PLACEMENTS,
	clampDockedWidth,
	clampFloatingWindow,
	defaultFloatingWindow,
	fitLayout,
	readLayout,
} from "../src/lib/panelLayout.js";

const LAPTOP = { width: 1440, height: 900 };
const FITTING_WINDOW = { left: 100, top: 50, width: 480, height: 640 };
const FROM_BIG_MONITOR = { left: 2000, top: 1200, width: 1800, height: 1100 };
const FITTED_TO_LAPTOP = { left: 144, top: 90, width: 1296, height: 810 };

describe("docked width", () => {
	test("keeps a width between 360 px and half the screen", () => {
		assert.equal(clampDockedWidth(500, LAPTOP.width), 500);
	});

	test("stops at half the screen", () => {
		assert.equal(clampDockedWidth(1000, LAPTOP.width), 720);
		assert.equal(clampDockedWidth(720, LAPTOP.width), 720);
	});

	test("rounds half of an odd screen width down to whole pixels", () => {
		assert.equal(clampDockedWidth(1000, 1367), 683);
	});

	test("never goes below 360 px", () => {
		assert.equal(clampDockedWidth(200, LAPTOP.width), 360);
		assert.equal(clampDockedWidth(360, LAPTOP.width), 360);
	});
});

describe("floating window", () => {
	test("keeps a window that fits", () => {
		assert.deepEqual(clampFloatingWindow(FITTING_WINDOW, LAPTOP), FITTING_WINDOW);
	});

	test("stops at 90% of the screen's width and height", () => {
		const huge = { left: 0, top: 0, width: 5000, height: 5000 };
		assert.deepEqual(clampFloatingWindow(huge, LAPTOP), {
			left: 0,
			top: 0,
			width: 1296,
			height: 810,
		});
	});

	test("is never smaller than 360 x 400 px", () => {
		const tiny = { left: 10, top: 10, width: 100, height: 100 };
		assert.deepEqual(clampFloatingWindow(tiny, LAPTOP), {
			left: 10,
			top: 10,
			width: 360,
			height: 400,
		});
	});

	test("moves a window that hangs off the right and bottom edges back on screen", () => {
		const offEdge = { left: 1300, top: 800, width: 480, height: 640 };
		assert.deepEqual(clampFloatingWindow(offEdge, LAPTOP), {
			left: 960,
			top: 260,
			width: 480,
			height: 640,
		});
	});

	test("moves a window left of or above the screen back on screen", () => {
		const offStart = { left: -50, top: -20, width: 480, height: 640 };
		assert.deepEqual(clampFloatingWindow(offStart, LAPTOP), {
			left: 0,
			top: 0,
			width: 480,
			height: 640,
		});
	});

	test("shrinks and moves a window saved on a bigger monitor", () => {
		assert.deepEqual(clampFloatingWindow(FROM_BIG_MONITOR, LAPTOP), FITTED_TO_LAPTOP);
	});

	test("rounds the 90% limit down to whole pixels", () => {
		const huge = { left: 0, top: 0, width: 5000, height: 5000 };
		const oddLaptop = { width: 1366, height: 768 };
		assert.deepEqual(clampFloatingWindow(huge, oddLaptop), {
			left: 0,
			top: 0,
			width: 1229,
			height: 691,
		});
	});

	test("takes 90% of the height on a screen too short for 400 px", () => {
		const short = { width: 1024, height: 400 };
		assert.equal(clampFloatingWindow(FITTING_WINDOW, short).height, 360);
	});

	test("first opens at 480 x 640 px, 24 px from the bottom-right corner", () => {
		assert.deepEqual(defaultFloatingWindow(LAPTOP), {
			left: 936,
			top: 236,
			width: 480,
			height: 640,
		});
	});

	test("first opens within 90% of a small screen", () => {
		assert.deepEqual(defaultFloatingWindow({ width: 800, height: 600 }), {
			left: 296,
			top: 36,
			width: 480,
			height: 540,
		});
	});
});

describe("saved layout", () => {
	test("with nothing saved, opens docked at 420 px with no window yet", () => {
		assert.deepEqual(readLayout({}), {
			mode: PANEL_MODES.DOCKED,
			dockedWidth: 420,
			floatingWindow: null,
		});
	});

	test("old full-screen state opens docked at the saved width", () => {
		const oldState = { open: true, fullscreen: true, width: 600, session: "S-1" };
		assert.deepEqual(readLayout(oldState), {
			mode: PANEL_MODES.DOCKED,
			dockedWidth: 600,
			floatingWindow: null,
		});
	});

	test("a saved floating window comes back as it was", () => {
		const saved = { mode: "floating", width: 500, floating: FITTING_WINDOW };
		assert.deepEqual(readLayout(saved), {
			mode: PANEL_MODES.FLOATING,
			dockedWidth: 500,
			floatingWindow: FITTING_WINDOW,
		});
	});

	test("damaged values fall back to the defaults", () => {
		const damaged = { mode: "sideways", width: "wide", floating: { left: 1 } };
		assert.deepEqual(readLayout(damaged), {
			mode: PANEL_MODES.DOCKED,
			dockedWidth: 420,
			floatingWindow: null,
		});
	});

	test("a saved window missing any one side is ignored", () => {
		for (const side of ["left", "top", "width", "height"]) {
			const { [side]: _missing, ...incomplete } = FITTING_WINDOW;
			const saved = { mode: "floating", floating: incomplete };
			assert.equal(readLayout(saved).floatingWindow, null, `missing ${side}`);
		}
	});
});

describe("placement on a screen", () => {
	const docked = { mode: PANEL_MODES.DOCKED, dockedWidth: 420, floatingWindow: null };
	const floating = { mode: PANEL_MODES.FLOATING, dockedWidth: 420, floatingWindow: null };

	test("docks on a screen 768 px wide or wider", () => {
		assert.equal(fitLayout(docked, { width: 768, height: 1024 }).placement, "docked");
	});

	test("covers a screen narrower than 768 px, whatever the chosen mode", () => {
		const tablet = { width: 767, height: 1024 };
		assert.deepEqual(fitLayout(floating, tablet), { placement: PANEL_PLACEMENTS.COVERING });
		assert.deepEqual(fitLayout(docked, tablet), { placement: PANEL_PLACEMENTS.COVERING });
	});

	test("fits an old full-screen state's wide width to half the screen", () => {
		const oldState = { open: true, fullscreen: true, width: 1200 };
		const fitted = fitLayout(readLayout(oldState), LAPTOP);
		assert.equal(fitted.placement, PANEL_PLACEMENTS.DOCKED);
		assert.equal(fitted.dockedWidth, 720);
	});

	test("shrinks and moves a saved window that no longer fits the screen", () => {
		const saved = { ...floating, floatingWindow: FROM_BIG_MONITOR };
		assert.deepEqual(fitLayout(saved, LAPTOP).floatingWindow, FITTED_TO_LAPTOP);
	});

	test("puts a first pop-out at the default window", () => {
		assert.deepEqual(
			fitLayout(floating, LAPTOP).floatingWindow,
			defaultFloatingWindow(LAPTOP)
		);
	});

	test("keeps a chosen width and window that fit", () => {
		const chosen = {
			mode: PANEL_MODES.FLOATING,
			dockedWidth: 500,
			floatingWindow: FITTING_WINDOW,
		};
		assert.deepEqual(fitLayout(chosen, LAPTOP), {
			placement: PANEL_PLACEMENTS.FLOATING,
			dockedWidth: 500,
			floatingWindow: FITTING_WINDOW,
		});
	});
});
