def percent_to_pixels(canvas_box: dict, x_pct: float, y_pct: float) -> tuple[float, float]:
    """Convert coordinates given as a percentage (0-100) of canvas width/height
    into pixel offsets, so page classes can define responsive click targets
    that don't break when the canvas is resized between viewports."""
    return canvas_box["width"] * x_pct / 100, canvas_box["height"] * y_pct / 100
