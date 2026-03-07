"""
TextOverlay — Display custom text on the Minecraft HUD.
"""
import minescript
import time

# @ui.title "Text Overlay"

# @ui.page "Message"
# @ui.text message "Message" "Hello from Fluxus!" -- Text to display
# @ui.text prefix "Prefix" ">>>" -- Prefix before message
# @ui.color text_color "Color" #00ff88 -- Message color (visual reference)
# @ui.toggle bold "Bold" false -- Bold formatting
# @ui.toggle rainbow "Rainbow Mode" false -- Cycle through colors

# @ui.page "Timing"
# @ui.slider display_time "Duration (s)" 1 300 10 1 -- How long to show
# @ui.slider repeat_interval "Repeat (s)" 0 60 0 1 -- 0 = show once
# @ui.toggle fade_effect "Fade Effect" false -- Simulate fade with ellipsis

def main():
    print("=== Text Overlay ===")
    print(f"  Message: {message}")
    print(f"  Duration: {display_time}s")

    colors = ["§c", "§6", "§e", "§a", "§b", "§9", "§d"]
    color_idx = 0

    try:
        elapsed = 0
        while elapsed < display_time:
            if rainbow:
                color = colors[color_idx % len(colors)]
                color_idx += 1
                display = f"{prefix} {color}{message}"
            elif bold:
                display = f"{prefix} §l{message}"
            else:
                display = f"{prefix} {message}"

            if fade_effect and display_time - elapsed < 3:
                remaining = display_time - elapsed
                if remaining < 1:
                    display += "."
                elif remaining < 2:
                    display += ".."
                else:
                    display += "..."

            minescript.echo(display)

            if repeat_interval > 0:
                time.sleep(repeat_interval)
                elapsed += repeat_interval
            else:
                time.sleep(1)
                elapsed += 1

        print("Text overlay finished.")
    except KeyboardInterrupt:
        print("Text overlay stopped.")

main()
