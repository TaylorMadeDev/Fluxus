"""
Clock — Real-time clock overlay on HUD.
Shows the current real-world time on the Minecraft HUD.
"""
import minescript
import time

# @ui.title "Clock Overlay"
# @ui.toggle show_date "Show Date" true -- Show date alongside time
# @ui.toggle use_24h "24-Hour Format" false -- Use 24-hour time format
# @ui.dropdown position "Position" top-left,top-right,bottom-left,bottom-right -- HUD position
# @ui.slider refresh_rate "Refresh (ms)" 100 5000 1000 100 -- How often to update

def main():
    print("=== Clock Overlay ===")
    print(f"  Show date  : {show_date}")
    print(f"  24-hour    : {use_24h}")
    print(f"  Position   : {position}")
    print(f"  Refresh    : {refresh_rate}ms")
    print()

    try:
        while True:
            now = time.localtime()
            if use_24h:
                t = time.strftime("%H:%M:%S", now)
            else:
                t = time.strftime("%I:%M:%S %p", now)

            if show_date:
                d = time.strftime("%Y-%m-%d", now)
                display = f"{d}  {t}"
            else:
                display = t

            minescript.echo(f"[Clock] {display}")
            time.sleep(refresh_rate / 1000.0)
    except KeyboardInterrupt:
        print("Clock stopped.")

main()
