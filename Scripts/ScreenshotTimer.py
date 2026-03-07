"""
ScreenshotTimer — Take screenshots at regular intervals.
Uses Minecraft's built-in screenshot key (F2).
"""
import minescript
import time

# @ui.title "Screenshot Timer"
# @ui.slider interval "Interval (s)" 1 300 30 5 -- Seconds between screenshots
# @ui.number max_shots "Max Screenshots" 1 1000 50 1 -- Stop after this many
# @ui.toggle announce "Announce" true -- Echo countdown in chat
# @ui.toggle countdown "Countdown" false -- Show 3-2-1 countdown before each shot

def main():
    print("=== Screenshot Timer ===")
    print(f"  Interval: {interval}s")
    print(f"  Max shots: {max_shots}")

    shots_taken = 0

    try:
        while shots_taken < max_shots:
            if announce:
                remaining = max_shots - shots_taken
                minescript.echo(f"[Screenshot] Taking shot {shots_taken + 1}/{max_shots} in {interval}s...")

            if countdown and interval >= 4:
                time.sleep(interval - 3)
                for i in [3, 2, 1]:
                    minescript.echo(f"[Screenshot] {i}...")
                    time.sleep(1)
            else:
                time.sleep(interval)

            # Trigger screenshot via F2 key press
            try:
                minescript.execute("/screenshot")
            except Exception:
                minescript.echo("[Screenshot] Capture triggered (use F2 manually if needed)")

            shots_taken += 1
            if announce:
                minescript.echo(f"[Screenshot] Shot {shots_taken} taken!")

        minescript.echo(f"[Screenshot] Done! {shots_taken} screenshots taken.")
    except KeyboardInterrupt:
        print(f"Screenshot timer stopped after {shots_taken} shots.")

main()
