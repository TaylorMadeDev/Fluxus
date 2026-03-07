"""
ProgressBar — Show a progress bar for long-running operations.
Demonstrates how to build reusable HUD progress indicators.
"""
import minescript
import time

# @ui.title "Progress Bar Demo"
# @ui.number total_steps "Total Steps" 1 1000 100 10 -- Number of steps to simulate
# @ui.slider speed "Speed (ms/step)" 10 500 50 10 -- Milliseconds per step
# @ui.dropdown style "Bar Style" blocks,arrows,dots,ascii -- Visual style
# @ui.toggle show_percent "Show Percentage" true -- Show % complete
# @ui.toggle show_eta "Show ETA" true -- Show estimated time remaining
# @ui.number bar_width "Bar Width" 10 50 20 5 -- Width of the progress bar

def make_bar(progress, width, style):
    """Generate a progress bar string."""
    filled = int(width * progress)
    empty = width - filled

    if style == "blocks":
        return "█" * filled + "░" * empty
    elif style == "arrows":
        return "▶" * filled + "─" * empty
    elif style == "dots":
        return "●" * filled + "○" * empty
    elif style == "ascii":
        return "#" * filled + "-" * empty
    return "=" * filled + " " * empty

def main():
    print("=== Progress Bar Demo ===")
    print(f"  Steps: {total_steps}")
    print(f"  Speed: {speed}ms/step")
    print(f"  Style: {style}")
    print()

    start_time = time.time()

    try:
        for i in range(int(total_steps) + 1):
            progress = i / total_steps
            bar = make_bar(progress, int(bar_width), style)

            parts = [f"[{bar}]"]

            if show_percent:
                parts.append(f"{progress * 100:.0f}%")

            if show_eta and i > 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                remaining = (total_steps - i) / rate if rate > 0 else 0
                parts.append(f"ETA: {remaining:.1f}s")

            parts.append(f"({i}/{int(total_steps)})")

            minescript.echo(" ".join(parts))
            time.sleep(speed / 1000.0)

        minescript.echo(f"✓ Complete! {total_steps} steps in {time.time() - start_time:.1f}s")
    except KeyboardInterrupt:
        print("Progress bar stopped.")

main()
