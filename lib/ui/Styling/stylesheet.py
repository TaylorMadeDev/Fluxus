"""
Fluxus master stylesheet - assembles modular QSS fragments.
Each sub-module in styles/ owns a specific area of the UI.
"""

from .styles.base import get_base_styles
from .styles.topbar import get_topbar_styles
from .styles.sidebar import get_sidebar_styles
from .styles.editor import get_editor_styles
from .styles.panels import get_panel_styles
from .styles.components import get_component_styles


def get_app_stylesheet() -> str:
    """Return the complete application stylesheet."""
    return (
        get_base_styles()
        + get_topbar_styles()
        + get_sidebar_styles()
        + get_editor_styles()
        + get_panel_styles()
        + get_component_styles()
    )
