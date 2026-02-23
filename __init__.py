from . import ui
from . import register_quadgrab
from . import overlay
from . import ops as operators
from . import properties
import bpy
import sys
import importlib
bl_info = {
    "name": "LKS QuadGrab",
    "author": "LKS",
    "version": (1, 1, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > QuadGrab",
    "description": "QuadGrab",
    "category": "3D View",
}


_PACKAGE = __package__  # "lks_quadgrab"


def _reload_package() -> None:
    """Recursively reload every cached module under this package.

    This lets you disable / re-enable the addon in Blender's preferences
    to pick up code changes without restarting Blender.  Modules are
    sorted so that leaf (deepest) modules reload first, keeping
    parent-imports consistent.
    """
    pkg_modules: list[str] = sorted(
        [name for name in sys.modules if name ==
            _PACKAGE or name.startswith(_PACKAGE + ".")],
        key=lambda n: n.count("."),
        reverse=True,
    )
    for mod_name in pkg_modules:
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception as exc:  # noqa: BLE001
            print(f"[{_PACKAGE}] reload skip {mod_name}: {exc}")


def register():
    _reload_package()
    register_quadgrab.register_addon()


def unregister():
    register_quadgrab.unregister_addon()
