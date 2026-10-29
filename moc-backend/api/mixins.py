"""
Dual-language payload input handling mixin for Django REST Framework serializers.
Intercepts raw incoming request dictionary in to_internal_value() before DRF field
validation, transparently mapping English alias keys to canonical Vietnamese fields.
"""
from rest_framework import serializers


class DualPayloadMixin:
    """
    Mixin to remap incoming English/legacy payload keys to standard Vietnamese fields.
    """
    FIELD_ALIASES = {}

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
        elif isinstance(data, dict):
            data = dict(data)

        aliases = getattr(self, "FIELD_ALIASES", {})
        for en_key, vi_key in aliases.items():
            if en_key in data and vi_key not in data:
                data[vi_key] = data[en_key]

        return super().to_internal_value(data)
