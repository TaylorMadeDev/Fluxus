# ── Fluxus GUI Values ─────────────────────────────────
target_x = 0
target_y = 64
target_z = 0
use_player_pos = False
offset_y = -1
show_neighbors = False
print_raw = False
format = "pretty"
# ── End GUI Values ────────────────────────────────────

"""
GetBlock — Query block information at coordinates.

Uses the Fluxus GUI Builder to provide an interactive coordinate input.
Set coordinates in the GUI panel and press ▶ Run to inspect the block.
"""
import minescript

# ─────────────────────────────────────────────────────────────
#  GUI Definition
# ─────────────────────────────────────────────────────────────

# @ui.title "Block Inspector"

# @ui.page "Coordinates"
# @ui.label "Enter the coordinates of the block to inspect."
# @ui.number target_x "X" -30000 30000 0 1 -- Block X coordinate
# @ui.number target_y "Y" -64 320 64 1 -- Block Y coordinate
# @ui.number target_z "Z" -30000 30000 0 1 -- Block Z coordinate
# @ui.separator
# @ui.toggle use_player_pos "Use Player Position" false -- Ignore XYZ above and use your current position
# @ui.number offset_y "Y Offset" -10 10 -1 1 -- Offset from player feet (e.g. -1 = block below)

# @ui.page "Options"
# @ui.toggle show_neighbors "Show Neighbors" false -- Also show the 6 adjacent blocks
# @ui.toggle print_raw "Print Raw Data" false -- Print the raw block state string
# @ui.dropdown format "Output Format" pretty,compact,json -- How to display results

# ─────────────────────────────────────────────────────────────
#  Script Logic
# ─────────────────────────────────────────────────────────────

def get_block_info(x, y, z):
    """Get block type at the given coordinates."""
    try:
        block = minescript.getblock(x, y, z)
        return block
    except Exception as e:
        return f"Error: {e}"


def format_output(x, y, z, block, fmt):
    """Format the block info for display."""
    if fmt == "pretty":
        print(f"╔══════════════════════════════╗")
        print(f"║  Block Inspector Result       ║")
        print(f"╠══════════════════════════════╣")
        print(f"║  Position: ({x}, {y}, {z})")
        print(f"║  Block:    {block}")
        print(f"╚══════════════════════════════╝")
    elif fmt == "compact":
        print(f"({x},{y},{z}) → {block}")
    elif fmt == "json":
        import json
        data = {"x": x, "y": y, "z": z, "block": str(block)}
        print(json.dumps(data, indent=2))


def show_neighbor_blocks(x, y, z):
    """Show blocks adjacent to the target."""
    directions = [
        ("North (Z-1)", (0, 0, -1)),
        ("South (Z+1)", (0, 0, 1)),
        ("East  (X+1)", (1, 0, 0)),
        ("West  (X-1)", (-1, 0, 0)),
        ("Above (Y+1)", (0, 1, 0)),
        ("Below (Y-1)", (0, -1, 0)),
    ]
    print("\n── Neighboring Blocks ──")
    for name, (dx, dy, dz) in directions:
        nx, ny, nz = x + dx, y + dy, z + dz
        block = get_block_info(nx, ny, nz)
        print(f"  {name}: {block}")


def main():
    # Determine coordinates
    if use_player_pos:
        try:
            px, py, pz = minescript.player_position()
            x, y, z = int(px), int(py) + offset_y, int(pz)
            print(f"Using player position with Y offset {offset_y}")
        except Exception:
            print("Could not get player position — using manual coordinates")
            x, y, z = target_x, target_y, target_z
    else:
        x, y, z = target_x, target_y, target_z

    # Get the block
    block = get_block_info(x, y, z)

    # Display result
    format_output(x, y, z, block, format)

    # Show raw data if requested
    if print_raw:
        print(f"\nRaw: {repr(block)}")

    # Show neighbors if requested
    if show_neighbors:
        show_neighbor_blocks(x, y, z)


main()
