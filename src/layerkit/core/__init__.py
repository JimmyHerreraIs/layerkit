"""The five pipeline steps: load, segment, clean, cut, export.

Architecture rule: this package must never import from ``layerkit.cli`` or
``layerkit.api``. It knows nothing about how it is being called.
"""
