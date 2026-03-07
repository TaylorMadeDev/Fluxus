# ParameterDemo.py — Example script using Fluxus parameters
# Open the ⚙ Params dialog on this script to configure values visually.

# @header General Settings
# @param string player_name "Steve" -- Target player name
# @param int repeat_count 3 -- How many times to repeat the action
# @param bool verbose false -- Print extra debug info

# @header Movement
# @param float speed 1.5 -- Movement speed multiplier
# @param dropdown direction ["forward","backward","left","right","up","down"] -- Direction to move

# @header Chat
# @param string chat_prefix "[Fluxus]" -- Prefix for chat messages
# @param dropdown color ["white","red","green","blue","yellow","gold"] -- Message color

import minescript

# ── Script logic ──────────────────────────────────────────────────

minescript.echo(f"{chat_prefix} Parameter Demo started!")

if verbose:
    minescript.echo(f"  Player : {player_name}")
    minescript.echo(f"  Repeat : {repeat_count}")
    minescript.echo(f"  Speed  : {speed}")
    minescript.echo(f"  Dir    : {direction}")
    minescript.echo(f"  Color  : {color}")

for i in range(repeat_count):
    minescript.echo(f"{chat_prefix} [{color}] Iteration {i + 1}/{repeat_count} — moving {direction} at {speed}x speed")

minescript.echo(f"{chat_prefix} Done!")
