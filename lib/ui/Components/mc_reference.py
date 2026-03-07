"""
MC Reference — Minecraft entity, item, biome, enchantment, potion reference
panels with search and a command builder.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QScrollArea,
    QSizePolicy, QSpinBox, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from ..Colors.palette import COLORS

# ════════════════════════════════════════════════════════════════════
#  Data tables
# ════════════════════════════════════════════════════════════════════

ENTITIES = [
    ("zombie", "Hostile", "Undead mob that attacks players"),
    ("skeleton", "Hostile", "Ranged undead mob with bow"),
    ("creeper", "Hostile", "Explodes when near players"),
    ("spider", "Hostile", "Wall-climbing mob, neutral in daylight"),
    ("enderman", "Neutral", "Teleporting mob, hostile if looked at"),
    ("pig", "Passive", "Drops porkchop, can be saddled"),
    ("cow", "Passive", "Drops beef and leather, can be milked"),
    ("sheep", "Passive", "Drops wool, can be sheared"),
    ("chicken", "Passive", "Drops feathers and eggs"),
    ("villager", "Passive", "Trades items, has professions"),
    ("iron_golem", "Neutral", "Protects villagers, drops iron"),
    ("wolf", "Neutral", "Can be tamed with bones"),
    ("cat", "Passive", "Can be tamed, scares creepers"),
    ("horse", "Passive", "Rideable, can be armored"),
    ("bat", "Passive", "Flying cave mob"),
    ("blaze", "Hostile", "Nether mob, shoots fireballs"),
    ("ghast", "Hostile", "Large flying Nether mob"),
    ("wither_skeleton", "Hostile", "Nether skeleton, withers targets"),
    ("piglin", "Neutral", "Nether mob, barters gold"),
    ("ender_dragon", "Boss", "End dimension boss"),
    ("wither", "Boss", "Summoned boss, drops nether star"),
    ("warden", "Hostile", "Deep dark mob, extremely powerful"),
    ("allay", "Passive", "Collects items, follows note blocks"),
    ("axolotl", "Passive", "Aquatic mob, assists in combat"),
    ("bee", "Neutral", "Pollinates flowers, produces honey"),
    ("dolphin", "Neutral", "Aquatic, gives swimming speed"),
    ("fox", "Passive", "Nocturnal, picks up items"),
    ("goat", "Neutral", "Mountain mob, rams entities"),
    ("frog", "Passive", "Eats slimes, produces froglights"),
    ("camel", "Passive", "Two-rider mount, desert biome"),
    ("sniffer", "Passive", "Digs up ancient seeds"),
    ("breeze", "Hostile", "Trial chamber mob, wind attacks"),
    ("armadillo", "Passive", "Drops scute for wolf armor"),
]

ITEMS = [
    ("diamond_sword", "Combat", "Melee weapon, 7 attack damage"),
    ("diamond_pickaxe", "Tools", "Mines all ores, fast mining"),
    ("diamond_axe", "Tools", "Chops wood, 9 attack damage"),
    ("diamond_shovel", "Tools", "Digs dirt/sand/gravel"),
    ("netherite_sword", "Combat", "Best melee weapon, 8 damage"),
    ("netherite_pickaxe", "Tools", "Best pickaxe, mines everything"),
    ("bow", "Combat", "Ranged weapon, uses arrows"),
    ("crossbow", "Combat", "Ranged, can use fireworks"),
    ("trident", "Combat", "Throwable melee/ranged weapon"),
    ("shield", "Combat", "Blocks melee and projectile damage"),
    ("elytra", "Transport", "Glider wings from End ships"),
    ("totem_of_undying", "Combat", "Prevents death once"),
    ("ender_pearl", "Transport", "Teleports player on throw"),
    ("golden_apple", "Food", "Gives absorption and regen"),
    ("enchanted_golden_apple", "Food", "Powerful buffs, uncraftable"),
    ("diamond", "Material", "Used for tools, armor, enchanting"),
    ("netherite_ingot", "Material", "Upgrades diamond gear"),
    ("emerald", "Currency", "Villager trading currency"),
    ("redstone", "Redstone", "Powers redstone circuits"),
    ("glowstone", "Decoration", "Light source block"),
    ("end_crystal", "Utility", "Heals ender dragon, explodes"),
    ("tnt", "Explosive", "Destroys blocks on ignition"),
    ("beacon", "Utility", "Provides area effect buffs"),
    ("conduit", "Utility", "Underwater breathing and vision"),
    ("shulker_box", "Storage", "Portable chest, keeps items"),
    ("compass", "Navigation", "Points to spawn/lodestone"),
    ("clock", "Utility", "Shows time of day"),
    ("map", "Navigation", "Shows explored terrain"),
    ("spyglass", "Utility", "Zooms in view"),
    ("brush", "Archaeology", "Used on suspicious blocks"),
    ("mace", "Combat", "Smash attack from heights"),
    ("wind_charge", "Combat", "Breeze projectile item"),
]

BIOMES = [
    ("plains", "Temperate", "Flat grassland, villages spawn"),
    ("forest", "Temperate", "Dense trees, wolves spawn"),
    ("desert", "Hot", "Sand terrain, temples and villages"),
    ("jungle", "Hot", "Tall trees, parrots, temples"),
    ("taiga", "Cold", "Spruce forest, foxes, villages"),
    ("snowy_plains", "Cold", "Snow-covered flat terrain"),
    ("swamp", "Temperate", "Water features, slimes, witch huts"),
    ("mountains", "Cold", "High terrain, goats, emerald ore"),
    ("ocean", "Aquatic", "Deep water, monuments, shipwrecks"),
    ("deep_ocean", "Aquatic", "Very deep water, monuments"),
    ("river", "Aquatic", "Narrow water between biomes"),
    ("beach", "Aquatic", "Sandy shore between land and ocean"),
    ("mushroom_fields", "Special", "Mycelium ground, mooshrooms"),
    ("nether_wastes", "Nether", "Default Nether biome"),
    ("crimson_forest", "Nether", "Red Nether forest, hoglins"),
    ("warped_forest", "Nether", "Blue Nether forest, endermen"),
    ("soul_sand_valley", "Nether", "Soul sand, ghasts, skeletons"),
    ("basalt_deltas", "Nether", "Basalt columns, magma cubes"),
    ("the_end", "End", "Void dimension, ender dragon"),
    ("end_highlands", "End", "End cities, chorus plants"),
    ("end_midlands", "End", "Between end islands"),
    ("cherry_grove", "Temperate", "Cherry blossom trees, pink petals"),
    ("mangrove_swamp", "Hot", "Mangrove trees, mud blocks"),
    ("deep_dark", "Underground", "Sculk, warden, ancient city"),
    ("dripstone_caves", "Underground", "Pointed dripstone stalactites"),
    ("lush_caves", "Underground", "Glow berries, azalea, axolotls"),
    ("meadow", "Temperate", "Flower fields at mountain bases"),
    ("savanna", "Hot", "Acacia trees, llamas, villages"),
    ("badlands", "Hot", "Terracotta terrain, gold ore"),
    ("frozen_ocean", "Cold", "Ice-covered ocean, polar bears"),
]

ENCHANTMENTS = [
    ("sharpness", "V", "Sword/Axe", "Increases melee damage"),
    ("smite", "V", "Sword/Axe", "Extra damage to undead"),
    ("bane_of_arthropods", "V", "Sword/Axe", "Extra damage to spiders"),
    ("knockback", "II", "Sword", "Pushes back targets"),
    ("fire_aspect", "II", "Sword", "Sets targets on fire"),
    ("looting", "III", "Sword", "Increases mob drops"),
    ("sweeping_edge", "III", "Sword", "Increases sweep damage"),
    ("efficiency", "V", "Tools", "Faster mining speed"),
    ("fortune", "III", "Tools", "Increases block drops"),
    ("silk_touch", "I", "Tools", "Mines blocks as-is"),
    ("unbreaking", "III", "All", "Increases durability"),
    ("mending", "I", "All", "XP repairs item"),
    ("protection", "IV", "Armor", "Reduces all damage"),
    ("fire_protection", "IV", "Armor", "Reduces fire damage"),
    ("blast_protection", "IV", "Armor", "Reduces explosion damage"),
    ("projectile_protection", "IV", "Armor", "Reduces projectile damage"),
    ("thorns", "III", "Armor", "Damages attackers"),
    ("feather_falling", "IV", "Boots", "Reduces fall damage"),
    ("depth_strider", "III", "Boots", "Faster underwater movement"),
    ("frost_walker", "II", "Boots", "Freezes water underfoot"),
    ("soul_speed", "III", "Boots", "Faster on soul sand"),
    ("swift_sneak", "III", "Leggings", "Faster sneaking"),
    ("respiration", "III", "Helmet", "Extends underwater breathing"),
    ("aqua_affinity", "I", "Helmet", "Normal mining speed underwater"),
    ("power", "V", "Bow", "Increases arrow damage"),
    ("punch", "II", "Bow", "Increases arrow knockback"),
    ("flame", "I", "Bow", "Arrows set fire"),
    ("infinity", "I", "Bow", "Infinite normal arrows"),
    ("loyalty", "III", "Trident", "Returns thrown trident"),
    ("riptide", "III", "Trident", "Launches player in rain/water"),
    ("channeling", "I", "Trident", "Summons lightning in storms"),
    ("impaling", "V", "Trident", "Extra damage to aquatic mobs"),
    ("multishot", "I", "Crossbow", "Shoots 3 arrows at once"),
    ("piercing", "IV", "Crossbow", "Arrows pass through entities"),
    ("quick_charge", "III", "Crossbow", "Faster loading"),
    ("wind_burst", "III", "Mace", "Launches player upward on hit"),
    ("density", "V", "Mace", "Increases fall damage bonus"),
    ("breach", "IV", "Mace", "Reduces target armor effectiveness"),
]

POTIONS = [
    ("speed", "Increases movement speed", "3:00 / 8:00", "sugar"),
    ("slowness", "Decreases movement speed", "1:30 / 4:00", "fermented_spider_eye"),
    ("haste", "Faster mining speed", "Beacon only", "—"),
    ("strength", "Increases melee damage", "3:00 / 8:00", "blaze_powder"),
    ("instant_health", "Heals instantly", "Instant", "glistering_melon_slice"),
    ("instant_damage", "Damages instantly", "Instant", "fermented_spider_eye"),
    ("jump_boost", "Higher jumping", "3:00 / 8:00", "rabbit_foot"),
    ("regeneration", "Heals over time", "0:45 / 1:30", "ghast_tear"),
    ("fire_resistance", "Immune to fire/lava", "3:00 / 8:00", "magma_cream"),
    ("water_breathing", "Breathe underwater", "3:00 / 8:00", "pufferfish"),
    ("invisibility", "Invisible to mobs", "3:00 / 8:00", "fermented_spider_eye"),
    ("night_vision", "See in the dark", "3:00 / 8:00", "golden_carrot"),
    ("weakness", "Decreases melee damage", "1:30 / 4:00", "fermented_spider_eye"),
    ("poison", "Damages over time", "0:45 / 1:30", "spider_eye"),
    ("slow_falling", "Reduces fall speed", "1:30 / 4:00", "phantom_membrane"),
    ("turtle_master", "Slowness IV + Resistance III", "0:20 / 0:40", "turtle_shell"),
    ("wind_charged", "Launches wind burst on hit", "Instant", "breeze_rod"),
    ("weaving", "Spawns cobwebs on hit", "Instant", "cobweb"),
    ("oozing", "Spawns slimes on death", "Instant", "slime_ball"),
    ("infested", "Spawns silverfish on hit", "Instant", "stone"),
]


# ════════════════════════════════════════════════════════════════════
#  Reference list widget (reusable for each tab)
# ════════════════════════════════════════════════════════════════════

class _RefList(QFrame):
    """Searchable reference list with detail view."""

    copy_requested = Signal(str)

    def __init__(self, headers: list[str], data: list[tuple], parent=None):
        super().__init__(parent)
        self._headers = headers
        self._data = data
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.setLayout(layout)

        # Search
        self._search = QLineEdit()
        self._search.setObjectName("SearchInput")
        self._search.setPlaceholderText("Search…")
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        # Category filter
        categories = sorted({row[1] for row in self._data if len(row) > 1})
        if categories:
            cat_row = QHBoxLayout()
            cat_row.setSpacing(4)
            self._cat_combo = QComboBox()
            self._cat_combo.addItem("All")
            self._cat_combo.addItems(categories)
            self._cat_combo.currentTextChanged.connect(lambda: self._filter())
            cat_row.addWidget(QLabel("Filter:"))
            cat_row.addWidget(self._cat_combo)
            cat_row.addStretch()
            layout.addLayout(cat_row)

        # List
        self._list = QListWidget()
        self._list.setObjectName("RefList")
        self._list.setAlternatingRowColors(True)
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS.get('bg_surface', '#16162e')};
                color: {COLORS.get('text_primary', '#e8e6f0')};
                border: 1px solid {COLORS.get('border', '#2a2a4a')};
                border-radius: 4px;
                font-family: 'Consolas'; font-size: 11px;
            }}
            QListWidget::item {{ padding: 4px 8px; }}
            QListWidget::item:selected {{
                background: {COLORS.get('accent', '#7c6aef')};
            }}
            QListWidget::item:alternate {{
                background: {COLORS.get('bg_root', '#0e0e1e')};
            }}
        """)
        self._list.currentItemChanged.connect(self._show_detail)
        layout.addWidget(self._list, 1)

        # Detail panel
        self._detail = QLabel("")
        self._detail.setWordWrap(True)
        self._detail.setObjectName("RefDetail")
        self._detail.setStyleSheet(
            f"color: {COLORS.get('text_secondary', '#a0a0c0')};"
            f" padding: 8px; font-size: 11px;"
            f" background: {COLORS.get('bg_root', '#0e0e1e')};"
            f" border: 1px solid {COLORS.get('border', '#2a2a4a')};"
            f" border-radius: 4px;"
        )
        self._detail.setMinimumHeight(50)
        layout.addWidget(self._detail)

        # Copy button
        copy_btn = QPushButton("📋 Copy ID")
        copy_btn.setObjectName("SmallButton")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self._on_copy)
        layout.addWidget(copy_btn)

        self._filter()

    def _filter(self, _text: str = ""):
        query = self._search.text().strip().lower()
        cat = self._cat_combo.currentText() if hasattr(self, '_cat_combo') else "All"
        self._list.clear()
        for row in self._data:
            name = row[0]
            category = row[1] if len(row) > 1 else ""
            desc = row[2] if len(row) > 2 else ""
            if query and query not in name.lower() and query not in desc.lower():
                continue
            if cat != "All" and category != cat:
                continue
            display = f"{name}  ({category})" if category else name
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, row)
            self._list.addItem(item)

    def _show_detail(self, item):
        if not item:
            return
        row = item.data(Qt.UserRole)
        parts = []
        for h, v in zip(self._headers, row):
            parts.append(f"<b>{h}:</b> {v}")
        self._detail.setText("<br>".join(parts))

    def _on_copy(self):
        item = self._list.currentItem()
        if item:
            row = item.data(Qt.UserRole)
            self.copy_requested.emit(row[0])


# ════════════════════════════════════════════════════════════════════
#  Command Builder
# ════════════════════════════════════════════════════════════════════

class _CommandBuilder(QFrame):
    """Interactive Minecraft command builder."""

    copy_requested = Signal(str)

    COMMANDS = {
        "/give": {"args": ["player", "item", "count"], "template": "/give {player} minecraft:{item} {count}"},
        "/summon": {"args": ["entity", "x", "y", "z"], "template": "/summon minecraft:{entity} {x} {y} {z}"},
        "/tp": {"args": ["target", "x", "y", "z"], "template": "/tp {target} {x} {y} {z}"},
        "/setblock": {"args": ["x", "y", "z", "block"], "template": "/setblock {x} {y} {z} minecraft:{block}"},
        "/fill": {"args": ["x1", "y1", "z1", "x2", "y2", "z2", "block"], "template": "/fill {x1} {y1} {z1} {x2} {y2} {z2} minecraft:{block}"},
        "/effect": {"args": ["player", "effect", "duration", "amplifier"], "template": "/effect give {player} minecraft:{effect} {duration} {amplifier}"},
        "/enchant": {"args": ["player", "enchantment", "level"], "template": "/enchant {player} minecraft:{enchantment} {level}"},
        "/time": {"args": ["value"], "template": "/time set {value}"},
        "/weather": {"args": ["type"], "template": "/weather {type}"},
        "/gamemode": {"args": ["mode", "player"], "template": "/gamemode {mode} {player}"},
        "/kill": {"args": ["target"], "template": "/kill {target}"},
        "/clear": {"args": ["player", "item"], "template": "/clear {player} minecraft:{item}"},
        "/xp": {"args": ["amount", "player"], "template": "/xp add {player} {amount}"},
        "/msg": {"args": ["player", "message"], "template": "/msg {player} {message}"},
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._inputs: dict[str, QLineEdit] = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self.setLayout(layout)

        # Command selector
        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(8)
        cmd_row.addWidget(QLabel("Command:"))
        self._cmd_combo = QComboBox()
        self._cmd_combo.addItems(sorted(self.COMMANDS.keys()))
        self._cmd_combo.currentTextChanged.connect(self._update_args)
        cmd_row.addWidget(self._cmd_combo, 1)
        layout.addLayout(cmd_row)

        # Args form (dynamic)
        self._args_container = QWidget()
        self._args_layout = QVBoxLayout()
        self._args_layout.setContentsMargins(0, 0, 0, 0)
        self._args_layout.setSpacing(4)
        self._args_container.setLayout(self._args_layout)
        layout.addWidget(self._args_container)

        # Preview
        preview_lbl = QLabel("Preview:")
        preview_lbl.setStyleSheet(f"color: {COLORS.get('text_secondary', '#a0a0c0')}; font-weight: 600;")
        layout.addWidget(preview_lbl)

        self._preview = QLabel("")
        self._preview.setWordWrap(True)
        self._preview.setStyleSheet(
            f"color: {COLORS.get('accent', '#7c6aef')};"
            f" font-family: Consolas; font-size: 12px;"
            f" padding: 8px;"
            f" background: {COLORS.get('bg_root', '#0e0e1e')};"
            f" border: 1px solid {COLORS.get('border', '#2a2a4a')};"
            f" border-radius: 4px;"
        )
        layout.addWidget(self._preview)

        # Buttons
        btn_row = QHBoxLayout()
        copy_btn = QPushButton("📋 Copy Command")
        copy_btn.setObjectName("AccentButton")
        copy_btn.setCursor(Qt.PointingHandCursor)
        copy_btn.clicked.connect(self._on_copy)
        btn_row.addWidget(copy_btn)

        run_btn = QPushButton("▶ Run via minescript.execute()")
        run_btn.setObjectName("SmallButton")
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.clicked.connect(self._on_run)
        btn_row.addWidget(run_btn)
        layout.addLayout(btn_row)

        # Minescript code preview
        self._ms_code = QLabel("")
        self._ms_code.setWordWrap(True)
        self._ms_code.setStyleSheet(
            f"color: {COLORS.get('text_muted', '#6a6a8a')};"
            f" font-family: Consolas; font-size: 10px; padding: 4px;"
        )
        layout.addWidget(self._ms_code)

        layout.addStretch()
        self._update_args()

    def _update_args(self, _cmd: str = ""):
        # Clear old
        self._inputs.clear()
        while self._args_layout.count():
            child = self._args_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # clear sub-layouts
                while child.layout().count():
                    sub = child.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        cmd = self._cmd_combo.currentText()
        info = self.COMMANDS.get(cmd, {})
        for arg in info.get("args", []):
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(f"{arg}:")
            lbl.setFixedWidth(80)
            lbl.setStyleSheet(f"color: {COLORS.get('text_secondary', '#a0a0c0')};")
            row.addWidget(lbl)
            inp = QLineEdit()
            inp.setObjectName("SearchInput")
            inp.setPlaceholderText(f"Enter {arg}…")
            inp.textChanged.connect(self._update_preview)
            row.addWidget(inp)
            self._inputs[arg] = inp
            self._args_layout.addLayout(row)

        self._update_preview()

    def _build_command(self) -> str:
        cmd = self._cmd_combo.currentText()
        info = self.COMMANDS.get(cmd, {})
        template = info.get("template", "")
        values = {k: v.text().strip() or f"<{k}>" for k, v in self._inputs.items()}
        try:
            return template.format(**values)
        except Exception:
            return template

    def _update_preview(self, _=None):
        command = self._build_command()
        self._preview.setText(command)
        self._ms_code.setText(f'minescript.execute("{command}")')

    def _on_copy(self):
        self.copy_requested.emit(self._build_command())

    def _on_run(self):
        try:
            import minescript
            minescript.execute(self._build_command())
        except Exception:
            pass  # not in Minecraft


# ════════════════════════════════════════════════════════════════════
#  Main MC Reference Panel (tabbed)
# ════════════════════════════════════════════════════════════════════

class MCReferencePanel(QFrame):
    """Tabbed panel with entity, item, biome, enchantment, potion reference + command builder."""

    copy_requested = Signal(str)  # text to copy to clipboard

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MCReferencePanel")
        self._build()

    def _build(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Header
        header = QFrame()
        header.setObjectName("SettingsHeader")
        header.setFixedHeight(36)
        hl = QHBoxLayout()
        hl.setContentsMargins(12, 0, 12, 0)
        header.setLayout(hl)
        title = QLabel("📚  Minecraft Reference")
        title.setObjectName("PanelTitle")
        hl.addWidget(title)
        hl.addStretch()
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        tabs.setObjectName("RefTabs")
        tabs.setDocumentMode(True)

        # Entity tab
        entity_list = _RefList(["ID", "Category", "Description"], ENTITIES)
        entity_list.copy_requested.connect(self.copy_requested.emit)
        tabs.addTab(entity_list, "🧟 Entities")

        # Item tab
        item_list = _RefList(["ID", "Category", "Description"], ITEMS)
        item_list.copy_requested.connect(self.copy_requested.emit)
        tabs.addTab(item_list, "⛏ Items")

        # Biome tab
        biome_list = _RefList(["ID", "Type", "Description"], BIOMES)
        biome_list.copy_requested.connect(self.copy_requested.emit)
        tabs.addTab(biome_list, "🌍 Biomes")

        # Enchantment tab
        ench_list = _RefList(["ID", "Max Level", "Applies To", "Description"], ENCHANTMENTS)
        ench_list.copy_requested.connect(self.copy_requested.emit)
        tabs.addTab(ench_list, "✨ Enchantments")

        # Potion tab
        pot_list = _RefList(["ID", "Effect", "Duration", "Ingredient"], POTIONS)
        pot_list.copy_requested.connect(self.copy_requested.emit)
        tabs.addTab(pot_list, "🧪 Potions")

        # Command builder
        cmd_builder = _CommandBuilder()
        cmd_builder.copy_requested.connect(self.copy_requested.emit)
        tabs.addTab(cmd_builder, "⌨ Commands")

        layout.addWidget(tabs, 1)
