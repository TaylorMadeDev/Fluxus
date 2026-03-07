"""
FPS Counter — Display current FPS and frame time stats.
"""
import minescript
import time

# @ui.title "FPS Counter"
# @ui.toggle show_avg "Show Average" true -- Show rolling average FPS
# @ui.toggle show_min_max "Show Min/Max" false -- Show min/max frame times
# @ui.slider sample_window "Sample Window" 10 120 60 10 -- Frames to average over
# @ui.dropdown display_mode "Display Mode" simple,detailed,graph -- How to show FPS

def main():
    print("=== FPS Counter ===")
    print(f"  Show average : {show_avg}")
    print(f"  Show min/max : {show_min_max}")
    print(f"  Sample window: {sample_window}")
    print(f"  Display mode : {display_mode}")
    print()

    frame_times = []
    last_time = time.perf_counter()

    try:
        while True:
            now = time.perf_counter()
            dt = now - last_time
            last_time = now

            if dt > 0:
                frame_times.append(dt)
                if len(frame_times) > sample_window:
                    frame_times.pop(0)

            if len(frame_times) > 1:
                avg_dt = sum(frame_times) / len(frame_times)
                fps = 1.0 / avg_dt if avg_dt > 0 else 0

                if display_mode == "simple":
                    minescript.echo(f"FPS: {fps:.0f}")
                elif display_mode == "detailed":
                    msg = f"FPS: {fps:.0f} | Frame: {avg_dt*1000:.1f}ms"
                    if show_min_max and frame_times:
                        mn = min(frame_times) * 1000
                        mx = max(frame_times) * 1000
                        msg += f" | Min: {mn:.1f}ms Max: {mx:.1f}ms"
                    minescript.echo(msg)
                elif display_mode == "graph":
                    bar_len = int(min(fps / 2, 30))
                    bar = "█" * bar_len + "░" * (30 - bar_len)
                    minescript.echo(f"[{bar}] {fps:.0f} FPS")

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("FPS Counter stopped.")

main()
