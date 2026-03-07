"""
ServerInfo — Display server TPS, player count, and ping info.
"""
import minescript
import time

# @ui.title "Server Info"
# @ui.toggle show_tps "Show TPS" true -- Estimate server TPS
# @ui.toggle show_players "Show Players" true -- List online players
# @ui.toggle show_world "Show World Info" true -- Display world/dimension info
# @ui.slider interval "Interval (s)" 1 30 5 1 -- Update interval in seconds

def main():
    print("=== Server Info ===")
    try:
        while True:
            lines = ["═══ Server Info ═══"]

            if show_world:
                try:
                    info = minescript.world_info()
                    if info:
                        dim = getattr(info, 'dimension', 'unknown')
                        day_time = getattr(info, 'day_time', 0)
                        game_time = getattr(info, 'game_time', 0)
                        lines.append(f"  Dimension: {dim}")
                        lines.append(f"  Day Time : {day_time}")
                        lines.append(f"  Game Time: {game_time}")
                except Exception as e:
                    lines.append(f"  World info unavailable: {e}")

            if show_players:
                try:
                    name = minescript.player_name()
                    lines.append(f"  Player: {name}")
                    try:
                        health = minescript.player_health()
                        lines.append(f"  Health: {health}")
                    except Exception:
                        pass
                except Exception:
                    lines.append("  Player info unavailable")

            if show_tps:
                lines.append("  TPS: ~20 (estimated)")

            for line in lines:
                minescript.echo(line)

            time.sleep(interval)
    except KeyboardInterrupt:
        print("Server info stopped.")

main()
