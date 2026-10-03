"""Closed method registry. No dynamic imports or executable formula strings."""
from types import MappingProxyType

from .weighted_linear_regression import weighted_linear_regression

METHODS = MappingProxyType({"weighted_linear_regression": weighted_linear_regression})

