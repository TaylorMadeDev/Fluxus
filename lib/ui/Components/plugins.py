"""
Plugins system — editor plugins that provide additional completions,
snippets, and API data for third-party Minescript libraries.

Each plugin is a dict with:
  - name: display name
  - description: short description
  - version: plugin version
  - import_line: the import statement to use
  - completions: list of completion words
  - api_entries: list of APIEntry objects for docs/tooltips
  - snippets: dict of {name: code} snippet pairs
"""

import json
import os
from pathlib import Path
from .minescript_api import APIEntry

_PLUGINS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "plugins"
_PLUGINS_DIR.mkdir(exist_ok=True)


# ── Built-in Plugins ──────────────────────────────────────────────

_MINESCRIPT_PLUS_API = [
    APIEntry("Inventory.click_slot", "minescript_plus", "slot: int, right_button: bool = False",
             "Click on a slot in the inventory.", "v0.13+", "ms_plus_inv", returns="bool"),
    APIEntry("Inventory.shift_click_slot", "minescript_plus", "slot: int",
             "Shift-click a slot.", "v0.13+", "ms_plus_inv", returns="bool"),
    APIEntry("Inventory.find_item", "minescript_plus",
             "item_id: str, cust_name: str, container: bool, try_open: bool",
             "Find an item by ID/name.", "v0.13+", "ms_plus_inv", returns="int | None"),
    APIEntry("Screen.wait_screen", "minescript_plus", "name: str, delay: int",
             "Wait until a specific screen is open.", "v0.13+", "ms_plus_gui", returns="bool"),
    APIEntry("Screen.close_screen", "minescript_plus", "",
             "Close the current screen.", "v0.13+", "ms_plus_gui"),
    APIEntry("Gui.get_title", "minescript_plus", "",
             "Get the current title text.", "v0.13+", "ms_plus_gui", returns="str | None"),
    APIEntry("Gui.set_title", "minescript_plus", "text: str",
             "Set the title overlay text.", "v0.13+", "ms_plus_gui"),
    APIEntry("Gui.set_actionbar", "minescript_plus", "text: str, tinted: bool",
             "Set the actionbar text.", "v0.13+", "ms_plus_gui"),
    APIEntry("Key.press_key", "minescript_plus", "key_name: str, state: bool",
             "Simulate pressing a key.", "v0.13+", "ms_plus_client"),
    APIEntry("Client.pause_game", "minescript_plus", "",
             "Pause the game.", "v0.13+", "ms_plus_client", returns="bool"),
    APIEntry("Client.disconnect", "minescript_plus", "",
             "Disconnect from server.", "v0.13+", "ms_plus_client"),
    APIEntry("Player.get_game_mode", "minescript_plus", "",
             "Get the player's game mode.", "v0.13+", "ms_plus_player", returns="str"),
    APIEntry("Player.get_food_level", "minescript_plus", "",
             "Get the player's food level.", "v0.13+", "ms_plus_player", returns="float"),
    APIEntry("World.is_raining", "minescript_plus", "",
             "Check if it's raining.", "v0.13+", "ms_plus_world", returns="bool"),
    APIEntry("World.get_game_time", "minescript_plus", "",
             "Get total game time in ticks.", "v0.13+", "ms_plus_world", returns="int"),
    APIEntry("Trading.trade_offer", "minescript_plus", "offer_index: int",
             "Execute a trade.", "v0.13+", "ms_plus_trading", returns="bool"),
    APIEntry("Hud.add_text", "minescript_plus",
             "text: str, x: int, y: int, color: tuple, ...",
             "Add a HUD text element.", "v0.13+", "ms_plus_hud", returns="int"),
    APIEntry("Util.get_clipboard", "minescript_plus", "",
             "Get clipboard text.", "v0.13+", "ms_plus_util", returns="str"),
    APIEntry("Util.play_sound", "minescript_plus",
             "sound, sound_source, volume: float, pitch: float",
             "Play a sound.", "v0.13+", "ms_plus_util"),
    APIEntry("Event.register", "minescript_plus",
             "event_name: str, callback, once: bool = False",
             "Register an event listener.", "v0.13+", "ms_plus_events", returns="Listener"),
]

_MSPLUS_COMPLETIONS = [
    # Classes
    "Inventory", "Screen", "Gui", "Key", "Client", "Player",
    "Server", "World", "Trading", "Hud", "Util", "Keybind", "Event",
    # Inventory methods
    "click_slot", "shift_click_slot", "inventory_hotbar_swap",
    "open_targeted_chest", "take_items", "find_item",
    # Screen/Gui methods
    "wait_screen", "close_screen",
    "get_title", "get_subtitle", "get_actionbar",
    "set_title", "set_subtitle", "set_actionbar",
    "set_title_times", "reset_title_times", "clear_titles",
    # Key/Client methods
    "press_key", "pause_game", "disconnect",
    "is_local_server", "is_multiplayer_server", "get_options",
    # Player methods
    "get_latency", "get_game_mode", "is_creative", "is_survival",
    "get_skin_url", "get_food_level", "get_saturation_level",
    "get_player_block_position", "get_xp_levels", "get_experience_progress",
    # Server methods
    "is_local", "get_ping", "is_lan", "is_realm", "get_tablist",
    # World methods
    "is_raining", "is_thundering", "is_hardcore",
    "get_difficulty", "get_spawn_pos", "get_game_time", "get_day_time",
    "get_sign_text", "set_sign_text", "find_nearest_entity",
    "get_destroy_progress", "get_destroy_stage",
    # Trading methods
    "get_offers", "get_offer", "get_costA", "get_costB",
    "get_result", "trade_offer",
    # Hud methods
    "add_text", "update_text", "remove_text", "clear_texts",
    "add_item", "update_item", "remove_item", "clear_items",
    "show_hud", "show_text", "show_item",
    # Util methods
    "get_job_id", "get_clipboard", "set_clipboard",
    "get_distance", "get_nbt", "get_light_level",
    "play_sound", "get_soundevents", "get_soundsource", "show_toast",
    # Keybind methods
    "set_keybind", "modify_keybind", "remove_keybind",
    # Event methods
    "register", "unregister", "define_event",
    # Utility function
    "input",
]

BUILTIN_PLUGINS = {
    "minescriptplus": {
        "name": "MinescriptPlus",
        "description": "User-friendly API extending Minescript — Inventory, GUI, HUD, Events, Player, World, and more.",
        "version": "0.16.2-alpha",
        "import_line": "from minescript_plus import *",
        "completions": _MSPLUS_COMPLETIONS,
        "api_entries": _MINESCRIPT_PLUS_API,
        "snippets": {
            "Import MinescriptPlus": "from minescript_plus import *",
            "Get Title": "title = Gui.get_title()",
            "Set Actionbar": "Gui.set_actionbar('Hello!', True)",
            "Find Item": "slot = Inventory.find_item('diamond')",
            "Click Slot": "Inventory.click_slot(0)",
            "HUD Text": "idx = Hud.add_text('Hello', 10, 10)",
            "Play Sound": "Util.play_sound()",
            "Get Clipboard": "text = Util.get_clipboard()",
            "Chat Input": "msg = input('Enter message: ')",
            "Register Event": "await Event.register('on_title', my_callback)",
        },
        "enabled": True,
    },
}


# ── Plugin Registry ────────────────────────────────────────────────

class PluginRegistry:
    """Manages editor plugins — built-in and user-installed."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins = dict(BUILTIN_PLUGINS)
            cls._instance._load_user_plugins()
        return cls._instance

    def _load_user_plugins(self):
        """Load any .json plugin definitions from the plugins/ directory."""
        if not _PLUGINS_DIR.exists():
            return
        for f in _PLUGINS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                name = data.get("name", f.stem)
                self._plugins[f.stem] = {
                    "name": name,
                    "description": data.get("description", ""),
                    "version": data.get("version", "1.0.0"),
                    "import_line": data.get("import_line", f"import {f.stem}"),
                    "completions": data.get("completions", []),
                    "api_entries": [
                        APIEntry(
                            e["name"], e.get("module", f.stem),
                            e.get("signature", ""), e.get("description", ""),
                            e.get("since", ""), e.get("category", ""),
                            e.get("params", []), e.get("returns", ""),
                        )
                        for e in data.get("api_entries", [])
                    ],
                    "snippets": data.get("snippets", {}),
                    "enabled": data.get("enabled", True),
                }
            except Exception:
                pass

    def get_all_plugins(self) -> dict:
        return dict(self._plugins)

    def get_enabled_plugins(self) -> dict:
        return {k: v for k, v in self._plugins.items() if v.get("enabled", True)}

    def get_all_completions(self) -> list[str]:
        """Return completion words from all enabled plugins."""
        words = []
        for plugin in self.get_enabled_plugins().values():
            words.extend(plugin.get("completions", []))
        return sorted(set(words))

    def get_all_api_entries(self) -> list[APIEntry]:
        """Return API entries from all enabled plugins."""
        entries = []
        for plugin in self.get_enabled_plugins().values():
            entries.extend(plugin.get("api_entries", []))
        return entries

    def get_all_snippets(self) -> dict[str, str]:
        """Return snippets from all enabled plugins."""
        snippets = {}
        for plugin in self.get_enabled_plugins().values():
            snippets.update(plugin.get("snippets", {}))
        return snippets

    def set_enabled(self, plugin_id: str, enabled: bool):
        if plugin_id in self._plugins:
            self._plugins[plugin_id]["enabled"] = enabled

    def get_import_lines(self) -> list[str]:
        """Return import lines for all enabled plugins."""
        lines = []
        for plugin in self.get_enabled_plugins().values():
            line = plugin.get("import_line", "")
            if line:
                lines.append(line)
        return lines


def get_plugin_registry() -> PluginRegistry:
    """Get the singleton plugin registry."""
    return PluginRegistry()
