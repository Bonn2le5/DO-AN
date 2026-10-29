import inspect
from django.db import models

# Compatibility patch for Django 4.x / 5.x / 6.x
# In Django 5.1+, 'check' was deprecated in favor of 'condition'.
# In Django 6.0+, 'check' was removed and CheckConstraint only accepts 'condition'.
_orig_check_constraint_init = models.CheckConstraint.__init__

def _compatible_check_constraint_init(self, *args, **kwargs):
    sig = inspect.signature(_orig_check_constraint_init)
    if "condition" in sig.parameters and "check" in kwargs:
        kwargs["condition"] = kwargs.pop("check")
    elif "check" in sig.parameters and "condition" in kwargs:
        kwargs["check"] = kwargs.pop("condition")
    return _orig_check_constraint_init(self, *args, **kwargs)

models.CheckConstraint.__init__ = _compatible_check_constraint_init
