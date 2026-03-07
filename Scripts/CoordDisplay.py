"""
CoordDisplay — Persistent coordinate display on HUD.
Shows player XYZ, facing direction, biome, and dimension.
"""
import minescript
import time
import math

# @ui.title "Coordinate Display"
# @ui.toggle show_facing "Show Facing" true -- Show cardinal direction
# @ui.toggle show_chunk "Show Chunk" true -- Show chunk coordinates
# @ui.toggle show_block "Block Under" false -- Show block type below feet
# @ui.slider update_rate "Update (ms)" 100 2000 500 100 -- Update interval
# @ui.dropdown format "Format" full,compact,minimal -- Display format

def get_facing(yaw):
    """Convert yaw angle to cardinal direction."""
    yaw = yaw % 360
    if yaw < 0:
        yaw += 360
    directions = ["S", "SW", "W", "NW", "N", "NE", "E", "SE"]
    idx = int((yaw + 22.5) / 45) % 8
    return directions[idx]

def main():
    print("=== Coordinate Display ===")
    try:
        while True:
            x, y, z = minescript.player_position()
            ix, iy, iz = int(x), int(y), int(z)

            if format == "minimal":
                minescript.echo(f"{ix} {iy} {iz}")
            elif format == "compact":
                msg = f"XYZ: {ix}/{iy}/{iz}"
                if show_chunk:
                    cx, cz = ix // 16, iz // 16
                    msg += f" | Chunk: {cx},{cz}"
                minescript.echo(msg)
            else:  # full
                lines = [f"X: {x:.1f}  Y: {y:.1f}  Z: {z:.1f}"]

                if show_facing:
                    try:
                        # Try to get player look direction
                        info = minescript.player()
                        yaw = getattr(info, 'yaw', 0)
                        facing = get_facing(yaw)
                        lines.append(f"Facing: {facing} ({yaw:.0f}°)")
                    except Exception:
                        pass

                if show_chunk:
                    cx, cz = ix // 16, iz // 16
                    local_x, local_z = ix % 16, iz % 16
                    lines.append(f"Chunk: [{cx}, {cz}] Local: [{local_x}, {local_z}]")

                if show_block:
                    try:
                        block = minescript.getblock(ix, iy - 1, iz)
                        lines.append(f"Standing on: {block}")
                    except Exception:
                        pass

                minescript.echo(" | ".join(lines))

            time.sleep(update_rate / 1000.0)
    except KeyboardInterrupt:
        print("Coordinate display stopped.")

main()
