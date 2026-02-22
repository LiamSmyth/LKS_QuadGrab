import bpy

from . import properties
from . import operators
from . import ui


def register_addon() -> None:
    properties.register()
    operators.register()
    ui.register()


def unregister_addon() -> None:
    ui.unregister()
    operators.unregister()
    properties.unregister()
