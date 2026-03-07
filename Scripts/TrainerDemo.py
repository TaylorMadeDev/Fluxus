"""
TrainerDemo — Showcase of the Fluxus Script GUI Builder.

This script demonstrates all @ui annotation types.
Open it in the editor and the GUI panel will appear on the right!

The values you set in the GUI panel get injected as Python variables
when you press ▶ Run.
"""
import minescript

# ─────────────────────────────────────────────────────────────
#  GUI Definition  (parsed by the editor — NOT executed as code)
# ─────────────────────────────────────────────────────────────

# @ui.title "Trainer Menu"

# ──── Movement Page ────────────────────────────────────────
# @ui.page "Movement"
# @ui.toggle fly_enabled "Enable Fly" false -- Toggle creative flight
# @ui.slider fly_speed "Fly Speed" 1 10 5 1 -- Blocks per second
# @ui.toggle sprint_enabled "Auto Sprint" true -- Always sprint when moving forward
# @ui.separator
# @ui.label "Use the button below to teleport to your saved home."
# @ui.button teleport_home "🏠 Teleport Home" -- Teleport to saved home coords
# @ui.number home_x "Home X" -30000 30000 0 1 -- Home X coordinate
# @ui.number home_y "Home Y" -64 320 64 1 -- Home Y coordinate
# @ui.number home_z "Home Z" -30000 30000 0 1 -- Home Z coordinate

# ──── Combat Page ──────────────────────────────────────────
# @ui.page "Combat"
# @ui.toggle auto_attack "Auto Attack" false -- Automatically attack hostile mobs
# @ui.dropdown weapon "Weapon Slot" sword,axe,bow,crossbow -- Preferred weapon type
# @ui.slider attack_reach "Attack Reach" 1 6 3 0.5 -- Reach distance in blocks
# @ui.toggle show_health "Show Mob Health" true -- Display health above mobs

# ──── Display Page ─────────────────────────────────────────
# @ui.page "Display"
# @ui.text chat_prefix "Chat Prefix" "[Fluxus]" -- Prefix added to chat messages
# @ui.color highlight_color "Highlight Color" #00ff88 -- Color for ESP highlights
# @ui.toggle show_coords "Show Coordinates" true -- Always display coords on HUD
# @ui.dropdown hud_position "HUD Position" top-left,top-right,bottom-left,bottom-right -- Where the HUD overlay appears
# @ui.slider hud_opacity "HUD Opacity" 0 100 80 5 -- Transparency of HUD overlay

# ─────────────────────────────────────────────────────────────
#  Script Logic  (runs when you press ▶ Run)
# ─────────────────────────────────────────────────────────────

def main():
    """Main entry point — uses the GUI-injected variables."""

    print(f"=== Trainer Menu Active ===")
    print()

    # ── Movement ───────────────────────────────────────────
    print("── Movement Settings ──")
    print(f"  Fly enabled : {fly_enabled}")
    if fly_enabled:
        print(f"  Fly speed   : {fly_speed} blocks/s")
    print(f"  Auto sprint : {sprint_enabled}")
    print(f"  Home coords : ({home_x}, {home_y}, {home_z})")
    print()

    # ── Combat ─────────────────────────────────────────────
    print("── Combat Settings ──")
    print(f"  Auto attack : {auto_attack}")
    print(f"  Weapon      : {weapon}")
    print(f"  Reach       : {attack_reach}")
    print(f"  Mob health  : {show_health}")
    print()

    # ── Display ────────────────────────────────────────────
    print("── Display Settings ──")
    print(f"  Chat prefix : {chat_prefix}")
    print(f"  Highlight   : {highlight_color}")
    print(f"  Show coords : {show_coords}")
    print(f"  HUD pos     : {hud_position}")
    print(f"  HUD opacity : {hud_opacity}%")
    print()

    # ── Example: Teleport Home ─────────────────────────────
    if fly_enabled:
        print(f"  [Fly] Would set fly speed to {fly_speed}")

    if auto_attack:
        print(f"  [Combat] Auto-attack active with {weapon}, reach {attack_reach}")

    # Show current player position for reference
    try:
        x, y, z = minescript.player_position()
        print(f"\n  Current position: ({x:.1f}, {y:.1f}, {z:.1f})")
    except Exception:
        print("\n  (Could not get player position — run this in Minecraft!)")

    print("\n=== Trainer Menu Config Loaded ===")


# Run it
main()
