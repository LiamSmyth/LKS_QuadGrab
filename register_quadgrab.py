import bpy

from . import properties
from . import ops as operators
from . import overlay
from . import ui


def register_addon() -> None:
    properties.register()
    operators.register()
    overlay.register()
    ui.register()


def unregister_addon() -> None:
    ui.unregister()
    overlay.unregister()
    operators.unregister()
    properties.unregister()
