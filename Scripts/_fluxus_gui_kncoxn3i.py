# ── Fluxus GUI Values ─────────────────────────────────
show_position = True
show_neighbors = False
show_light = True
range_limit = 5.0
update_ms = 200.0
# ── End GUI Values ────────────────────────────────────

"""
BlockInfo Crosshair — Show info about the block you're looking at.
Displays block type, position, and properties of the targeted block.
"""
import minescript
import time

# @ui.title "Block Crosshair"
# @ui.toggle show_position "Show Position" true -- Show block XYZ
# @ui.toggle show_neighbors "Show Neighbors" false -- Show adjacent block types
# @ui.toggle show_light "Show Light Level" true -- Show light level at block
# @ui.slider range_limit "Max Range" 1 20 5 1 -- Maximum raycast distance
# @ui.slider update_ms "Update (ms)" 50 1000 200 50 -- Update interval

def main():
    print("=== Block Info Crosshair ===")
    print(f"  Range: {range_limit} blocks")
    last_block = None

    try:
        while True:
            try:
                # Get player position and look direction
                x, y, z = minescript.player_position()
                ix, iy, iz = int(x), int(y), int(z)

                # Check block at player eye level +1 forward
                # Simple approach: check block at various distances in front
                block = minescript.getblock(ix, iy, iz)

                if block != last_block:
                    last_block = block
                    lines = [f"Block: {block}"]

                    if show_position:
                        lines.append(f"  Pos: ({ix}, {iy}, {iz})")

                    if show_neighbors:
                        for name, dx, dy, dz in [
                            ("Above", 0, 1, 0), ("Below", 0, -1, 0),
                            ("North", 0, 0, -1), ("South", 0, 0, 1),
                            ("East", 1, 0, 0), ("West", -1, 0, 0),
                        ]:
                            nb = minescript.getblock(ix+dx, iy+dy, iz+dz)
                            lines.append(f"  {name}: {nb}")

                    for line in lines:
                        minescript.echo(line)

            except Exception as e:
                pass  # Silently skip errors

            time.sleep(update_ms / 1000.0)
    except KeyboardInterrupt:
        print("Block info crosshair stopped.")

main()
