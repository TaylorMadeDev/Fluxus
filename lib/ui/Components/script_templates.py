"""
ScriptTemplates — pre-built script starters and template picker.
"""

from pathlib import Path

_TEMPLATES = {
    "Blank Script": {
        "description": "Empty script with basic imports",
        "code": (
            "# New Minescript Script\n"
            "import minescript\n\n"
            "# Your code here\n"
        ),
    },
    "Chat Command": {
        "description": "Script that responds to a chat command",
        "code": (
            "# Chat Command Script\n"
            "import minescript\n\n"
            "def on_chat(msg):\n"
            '    if msg.startswith("!hello"):\n'
            '        minescript.echo("Hello from Fluxus!")\n'
            "\n"
            "# Register chat listener\n"
            "try:\n"
            "    minescript.register_chat_listener(on_chat)\n"
            "except AttributeError:\n"
            '    minescript.echo("Chat listener requires Minescript 4.0+")\n'
        ),
    },
    "Block Builder": {
        "description": "Place blocks in a pattern around the player",
        "code": (
            "# Block Builder\n"
            "import minescript\n\n"
            "def build_wall(width=5, height=3, block='stone'):\n"
            "    x, y, z = minescript.player_position()\n"
            "    for dx in range(width):\n"
            "        for dy in range(height):\n"
            '            minescript.execute(f"setblock {x+dx} {y+dy} {z+1} {block}")\n'
            '    minescript.echo(f"Built {width}x{height} wall!")\n'
            "\n"
            "build_wall()\n"
        ),
    },
    "Entity Scanner": {
        "description": "Find and list nearby entities",
        "code": (
            "# Entity Scanner\n"
            "import minescript\n\n"
            "entities = minescript.entities()\n"
            'minescript.echo(f"Found {len(entities)} entities nearby:")\n'
            "for e in entities:\n"
            "    etype = getattr(e, 'type', 'unknown')\n"
            "    name = getattr(e, 'name', '')\n"
            "    label = f'{etype}' + (f' ({name})' if name else '')\n"
            "    minescript.echo(f'  - {label}')\n"
        ),
    },
    "Teleporter": {
        "description": "Save and teleport between locations",
        "code": (
            "# Teleporter - save and restore positions\n"
            "import minescript\n"
            "import json\n"
            "from pathlib import Path\n\n"
            "SAVE_FILE = Path(__file__).parent / 'saved_positions.json'\n\n"
            "def save_position(name='default'):\n"
            "    pos = minescript.player_position()\n"
            "    data = _load()\n"
            "    data[name] = list(pos)\n"
            "    SAVE_FILE.write_text(json.dumps(data))\n"
            "    minescript.echo(f'Saved position \"{name}\" at {pos}')\n\n"
            "def goto(name='default'):\n"
            "    data = _load()\n"
            "    if name in data:\n"
            "        x, y, z = data[name]\n"
            "        minescript.execute(f'tp {x} {y} {z}')\n"
            "        minescript.echo(f'Teleported to \"{name}\"')\n"
            "    else:\n"
            "        minescript.echo(f'No saved position \"{name}\"')\n\n"
            "def _load():\n"
            "    try:\n"
            "        return json.loads(SAVE_FILE.read_text())\n"
            "    except Exception:\n"
            "        return {}\n\n"
            "# Usage: save_position('home') then goto('home')\n"
            "save_position('home')\n"
        ),
    },
    "Block Scanner": {
        "description": "Scan a region and report block types",
        "code": (
            "# Block Scanner\n"
            "import minescript\n"
            "from collections import Counter\n\n"
            "def scan_region(radius=5):\n"
            "    px, py, pz = minescript.player_position()\n"
            "    blocks = Counter()\n"
            "    for dx in range(-radius, radius+1):\n"
            "        for dy in range(-radius, radius+1):\n"
            "            for dz in range(-radius, radius+1):\n"
            "                b = minescript.getblock(int(px+dx), int(py+dy), int(pz+dz))\n"
            "                if b != 'minecraft:air':\n"
            "                    blocks[b] += 1\n"
            "    minescript.echo(f'--- Block scan ({radius*2+1}^3 region) ---')\n"
            "    for block, count in blocks.most_common(10):\n"
            "        minescript.echo(f'  {block}: {count}')\n\n"
            "scan_region(5)\n"
        ),
    },
    "Timer/Loop": {
        "description": "Run code on a timer interval",
        "code": (
            "# Timer Loop Script\n"
            "import minescript\n"
            "import time\n\n"
            "INTERVAL = 5  # seconds between ticks\n"
            "MAX_TICKS = 12  # stop after this many\n\n"
            "for tick in range(MAX_TICKS):\n"
            "    pos = minescript.player_position()\n"
            "    minescript.echo(f'Tick {tick+1}: pos = {int(pos[0])}, {int(pos[1])}, {int(pos[2])}')\n"
            "    time.sleep(INTERVAL)\n\n"
            "minescript.echo('Timer finished.')\n"
        ),
    },
    "Plugin Skeleton": {
        "description": "Full plugin structure with init/cleanup",
        "code": (
            "# Plugin Skeleton\n"
            "import minescript\n"
            "import atexit\n\n"
            "PLUGIN_NAME = 'MyPlugin'\n"
            "PLUGIN_VERSION = '1.0.0'\n\n"
            "def init():\n"
            "    minescript.echo(f'{PLUGIN_NAME} v{PLUGIN_VERSION} loaded!')\n\n"
            "def cleanup():\n"
            "    minescript.echo(f'{PLUGIN_NAME} shutting down.')\n\n"
            "def main():\n"
            "    # Your main plugin logic here\n"
            "    pass\n\n"
            "atexit.register(cleanup)\n"
            "init()\n"
            "main()\n"
        ),
    },
}


def list_templates() -> dict[str, dict]:
    """Return dict of template_name -> {description, code}."""
    return dict(_TEMPLATES)


def get_template(name: str, is_pyj: bool = False) -> str:
    """Return the code for a named template, with correct import for file type."""
    code = _TEMPLATES.get(name, {}).get("code", "")
    if is_pyj:
        # Replace Python import with Pyjinn import
        code = code.replace("import minescript", "from system.pyj.minescript import *")
    return code


def get_template_names() -> list[str]:
    return list(_TEMPLATES.keys())


def get_import_statement(is_pyj: bool = False) -> str:
    """Return the correct minescript import for Python or Pyjinn."""
    if is_pyj:
        return "from system.pyj.minescript import *"
    return "import minescript"
