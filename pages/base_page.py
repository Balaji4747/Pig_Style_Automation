import time
from pathlib import Path

from playwright.sync_api import Page

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

# Walks window.__PIXI_APP__.stage for VISIBLE nodes with a non-zero bounding
# box matching `name`, returning the LAST match's bounds (canvas-local
# pixels). The game reuses some node names (e.g. "startBtn") across
# several simultaneously-present popups/components (confirmed: splash,
# feature-intro, and Auto Spin all have their own "startBtn"); the one
# actually on top is consistently the LAST match in document order (PIXI
# draws children in array order, so later siblings render on top) —
# confirmed by testing against the real Auto Spin panel.
_PIXI_FIND_VISIBLE_NODE_JS = """
(name) => {
    const app = window.__PIXI_APP__;
    if (!app || !app.stage) return null;
    let found = null;
    (function walk(node) {
        if (!node) return;
        if (node.name === name && node.visible) {
            let b = null;
            try { b = node.getBounds(); } catch (e) {}
            if (b && b.width > 0 && b.height > 0) { found = { x: b.x, y: b.y, width: b.width, height: b.height }; }
        }
        if (node.children) for (const child of node.children) walk(child);
    })(app.stage);
    return found;
}
"""

# Same as above but for finding a node by its exact rendered text (PixText
# `.text` property, not pixel OCR) rather than by name — used for reusable
# button components that share a generic container name (e.g. "btnText")
# but have distinct, identifiable labels ("Buy bonus", "Set").
_PIXI_FIND_VISIBLE_TEXT_JS = """
(text) => {
    const app = window.__PIXI_APP__;
    if (!app || !app.stage) return null;
    let found = null;
    (function walk(node) {
        if (!node) return;
        if (node.visible && node.text === text) {
            let b = null;
            try { b = node.getBounds(); } catch (e) {}
            if (b && b.width > 0 && b.height > 0) { found = { x: b.x, y: b.y, width: b.width, height: b.height }; }
        }
        if (node.children) for (const child of node.children) walk(child);
    })(app.stage);
    return found;
}
"""


class BasePage:
    """Common waits, canvas interaction (by PIXI node name or raw coordinate),
    and screenshot helpers shared by all page objects. All locators/node
    names/coordinates live in page subclasses, never in tests."""

    CANVAS_SELECTOR = "canvas"
    DEFAULT_TIMEOUT_MS = 10_000

    def __init__(self, page: Page):
        self.page = page

    def goto(self, url: str) -> None:
        self.page.goto(url)

    def click_canvas(self, x: float, y: float) -> None:
        """Click at (x, y) pixel offset relative to the canvas element."""
        canvas = self.page.locator(self.CANVAS_SELECTOR).first
        box = canvas.bounding_box()
        if box is None:
            raise RuntimeError(f"Canvas '{self.CANVAS_SELECTOR}' not found or not visible")
        self.page.mouse.click(box["x"] + x, box["y"] + y)

    def is_pixi_ready(self) -> bool:
        """Whether window.__PIXI_APP__.stage exists yet. Must be checked
        before trusting get_pixi_node_or_none()'s False/None result as "node
        not visible" rather than "PIXI hasn't initialized yet" (the two are
        indistinguishable from get_pixi_node alone, and conflating them
        causes false "already dismissed/not showing" positives during the
        earliest loading phase, before the game's PIXI app attaches)."""
        return bool(self.page.evaluate("() => !!(window.__PIXI_APP__ && window.__PIXI_APP__.stage)"))

    def get_pixi_node(self, name: str) -> dict:
        """Return the bounds (x, y, width, height, in canvas-local pixels) of
        the topmost (last in document order) visible PIXI scene-graph node
        named `name`."""
        bounds = self.page.evaluate(_PIXI_FIND_VISIBLE_NODE_JS, name)
        if bounds is None:
            raise RuntimeError(f"PIXI node '{name}' not found or not visible")
        return bounds

    def get_pixi_node_or_none(self, name: str) -> dict | None:
        try:
            return self.get_pixi_node(name)
        except RuntimeError:
            return None

    def is_pixi_node_interactive(self, name: str) -> bool:
        """Whether the named, visible PIXI node's own `interactive` flag is
        true — distinct from (and stricter than) visible+non-zero-bounds.

        Confirmed live (D-034): a control's `visible`/bounds can look
        completely normal while its `interactive` flag is still `false`
        (e.g. the Bet button for ~26s after a spin, well past the client's
        own win-presentation animation finishing) — a click lands on the
        right canvas pixel but is a clean no-op, no exception, nothing to
        catch. Use `wait_for_pixi_interactive()` before clicking a control
        shortly after a spin rather than guessing a fixed delay."""
        return bool(
            self.page.evaluate(
                """(name) => {
                    const app = window.__PIXI_APP__;
                    if (!app || !app.stage) return false;
                    let node = null;
                    (function walk(n) {
                        if (!n || node) return;
                        if (n.name === name && n.visible) node = n;
                        if (n.children) for (const c of n.children) walk(c);
                    })(app.stage);
                    return !!(node && node.interactive);
                }""",
                name,
            )
        )

    def wait_for_pixi_interactive(self, name: str, timeout_ms: int = 30_000) -> None:
        """Poll until the named PIXI node's own `interactive` flag is true.
        See `is_pixi_node_interactive()` for why this check exists."""
        self.wait_for(lambda: self.is_pixi_node_interactive(name), timeout_ms=timeout_ms)

    def click_pixi_button(self, name: str) -> None:
        """Click the center of a named, visible PIXI button. Preferred over
        click_canvas() with hardcoded coordinates: the bounds are read live
        from the running game, so this doesn't break if layout shifts."""
        bounds = self.get_pixi_node(name)
        center_x = bounds["x"] + bounds["width"] / 2
        center_y = bounds["y"] + bounds["height"] / 2
        self.click_canvas(center_x, center_y)

    def get_pixi_text(self, name: str) -> str:
        """Return the rendered `.text` of a named PIXI text node (e.g.
        "megawaysText" -> "MEGAWAYS"). Reads the actual text content of the
        already-rendered object, not pixel OCR."""
        bounds_and_text = self.page.evaluate(
            "(name) => { const a=window.__PIXI_APP__; if(!a||!a.stage) return null; let r=null;"
            " (function w(n){ if(!n) return; if(n.name===name && n.visible && n.text!==undefined){ r=n.text; }"
            " if(n.children) for(const c of n.children) w(c); })(a.stage); return r; }",
            name,
        )
        if bounds_and_text is None:
            raise RuntimeError(f"PIXI text node '{name}' not found or not visible")
        return bounds_and_text

    def click_pixi_text(self, text: str) -> None:
        """Click the center of the visible node whose rendered text exactly
        matches `text` — for reusable button components that share a
        generic container name but have distinct labels (e.g. "Buy bonus",
        "Set", "Cancel")."""
        bounds = self.page.evaluate(_PIXI_FIND_VISIBLE_TEXT_JS, text)
        if bounds is None:
            raise RuntimeError(f"No visible PIXI node with text '{text}' found")
        self.click_canvas(bounds["x"] + bounds["width"] / 2, bounds["y"] + bounds["height"] / 2)

    def get_sibling_value_text(self, label_node_name: str, label_text: str, value_node_name: str) -> str:
        """Find the visible node named `label_node_name` with text ==
        `label_text` (e.g. a "titleText" reading "BET"), then return the
        text of its sibling named `value_node_name` (e.g. "valueText").
        Robust against reused generic names (e.g. both BALANCE and BET use
        "titleText"/"valueText" pairs) since it matches by shared parent,
        not by document order."""
        result = self.page.evaluate(
            """([labelNodeName, labelText, valueNodeName]) => {
                const app = window.__PIXI_APP__;
                if (!app || !app.stage) return null;
                let result = null;
                (function walk(node) {
                    if (!node || result) return;
                    if (node.name === labelNodeName && node.visible && node.text === labelText) {
                        const parent = node.parent;
                        if (parent && parent.children) {
                            for (const sibling of parent.children) {
                                if (sibling.name === valueNodeName && sibling.visible) { result = sibling.text; break; }
                            }
                        }
                    }
                    if (node.children) for (const child of node.children) walk(child);
                })(app.stage);
                return result;
            }""",
            [label_node_name, label_text, value_node_name],
        )
        if result is None:
            raise RuntimeError(f"Could not find '{value_node_name}' sibling of '{label_node_name}'=='{label_text}'")
        return result

    def get_displayed_integer_near_label(self, label_node_name: str, label_text: str, timeout_ms: int = 3_000) -> int:
        """Find the visible node named `label_node_name` with text ==
        `label_text` (e.g. "megawaysText" == "MEGAWAYS"), then return the
        integer value of the nearest visible sibling/cousin whose text is
        digits-and-commas only (confirmed: the MEGAWAYS ways counter is
        rendered as an *unnamed* text node, so it can't be found by name —
        this locates it by proximity to its named label instead).

        Retries for `timeout_ms`: the counter briefly transitions after a
        spin (confirmed: an immediate read right after the spin response
        can miss it) before settling on the new value."""
        text = None
        deadline = time.monotonic() + timeout_ms / 1000
        while text is None and time.monotonic() < deadline:
            text = self._find_displayed_integer_near_label(label_node_name, label_text)
            if text is None:
                self.page.wait_for_timeout(200)
        if text is None:
            raise RuntimeError(f"Could not find a numeric value near label '{label_text}'")
        return int(text.replace(",", ""))

    def _find_displayed_integer_near_label(self, label_node_name: str, label_text: str) -> str | None:
        return self.page.evaluate(
            """([labelNodeName, labelText]) => {
                const app = window.__PIXI_APP__;
                if (!app || !app.stage) return null;
                let labelBounds = null;
                (function findLabel(node) {
                    if (!node || labelBounds) return;
                    if (node.name === labelNodeName && node.visible && node.text === labelText) {
                        try { labelBounds = node.getBounds(); } catch (e) {}
                    }
                    if (node.children) for (const child of node.children) findLabel(child);
                })(app.stage);
                if (!labelBounds) return null;
                let best = null, bestDist = Infinity;
                (function findNumber(node) {
                    if (!node) return;
                    if (node.visible && node.text !== undefined && /^[0-9,]+$/.test(String(node.text || ''))) {
                        let b = null; try { b = node.getBounds(); } catch (e) {}
                        if (b) {
                            const dx = (b.x + b.width / 2) - (labelBounds.x + labelBounds.width / 2);
                            const dy = (b.y + b.height / 2) - (labelBounds.y + labelBounds.height / 2);
                            const dist = Math.sqrt(dx * dx + dy * dy);
                            if (dist < bestDist) { bestDist = dist; best = node.text; }
                        }
                    }
                    if (node.children) for (const child of node.children) findNumber(child);
                })(app.stage);
                return best;
            }""",
            [label_node_name, label_text],
        )

    def wait_for(self, condition, timeout_ms: int = DEFAULT_TIMEOUT_MS, interval_ms: int = 200) -> None:
        """Poll a zero-arg callable until it returns truthy, or raise TimeoutError."""
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            if condition():
                return
            self.page.wait_for_timeout(interval_ms)
        raise TimeoutError(f"Condition not met within {timeout_ms}ms")

    def screenshot(self, name: str) -> Path:
        directory = REPORTS_DIR / "screenshots"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{name}.png"
        self.page.screenshot(path=str(path))
        return path

    def wait_for_canvas_stable(
        self, timeout_ms: int = 10_000, check_interval_ms: int = 200, stable_checks: int = 2
    ) -> None:
        """Fallback wait for canvas animations (win rollups, reel-stop
        settling, popups) with no exposed "done" event: polls screenshots of
        the canvas element until `stable_checks` consecutive captures, each
        `check_interval_ms` apart, are byte-identical. Prefer waiting on a
        specific signal (a network response, a PIXI node appearing/
        disappearing) wherever one exists — this is a last resort for when
        none does."""
        canvas = self.page.locator(self.CANVAS_SELECTOR).first
        previous = canvas.screenshot()
        stable_count = 0
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            self.page.wait_for_timeout(check_interval_ms)
            current = canvas.screenshot()
            if current == previous:
                stable_count += 1
                if stable_count >= stable_checks:
                    return
            else:
                stable_count = 0
            previous = current
        raise TimeoutError(f"Canvas did not stabilize within {timeout_ms}ms")
