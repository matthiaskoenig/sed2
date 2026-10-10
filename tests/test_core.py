"""Tests for sed2 core data model."""

import pytest
from pydantic import BaseModel, ValidationError

from sed2.core import Reference, SId


class ModelWithSId(BaseModel):
    """Model with a single SId field, to exercise the constraint."""

    id: SId


def valid(id: str) -> None:
    """Assert that `id` is accepted as an SId."""
    ModelWithSId(id=id)


def invalid(id: str) -> None:
    """Assert that `id` is rejected as an SId."""
    with pytest.raises(ValidationError):
        ModelWithSId(id=id)


# --- valid SIds ---


def test_letter_start():
    """Test that an SId may start with a letter."""
    valid("a")


def test_underscore_start():
    """Test that an SId may start with an underscore."""
    valid("_model")


def test_uppercase_start():
    """Test that an SId may start with an uppercase letter."""
    valid("Model1")


def test_alphanumeric_body():
    """Test that an SId may contain letters, digits and underscores."""
    valid("model_1_A")


def test_single_letter():
    """Test that a single letter is an SId."""
    valid("x")


def test_single_underscore():
    """Test that a single underscore is an SId."""
    valid("_")


def test_long_id():
    """Test that the length of an SId is not restricted."""
    valid("a" * 200)


# --- invalid SIds ---


def test_digit_start():
    """Test that an SId may not start with a digit."""
    invalid("1model")


def test_hyphen():
    """Test that a hyphen is not allowed in an SId."""
    invalid("my-model")


def test_space():
    """Test that a space is not allowed in an SId."""
    invalid("my model")


def test_empty():
    """Test that the empty string is not an SId."""
    invalid("")


def test_dot():
    """Test that a dot is not allowed in an SId."""
    invalid("model.1")


def test_hash_prefix():
    """Test that a reference is not an SId."""
    invalid("#model")


# --- Reference ---


class ModelWithReference(BaseModel):
    """Model with a single Reference field, to exercise the constraint."""

    ref: Reference


def valid_ref(ref: str) -> None:
    """Assert that `ref` is accepted as a Reference."""
    ModelWithReference(ref=ref)


def invalid_ref(ref: str) -> None:
    """Assert that `ref` is rejected as a Reference."""
    with pytest.raises(ValidationError):
        ModelWithReference(ref=ref)


# valid References


def test_ref_letter_start():
    """Test that a reference may name a task starting with a letter."""
    valid_ref("#model")


def test_ref_underscore_start():
    """Test that a reference may name a task starting with an underscore."""
    valid_ref("#_model")


def test_ref_uppercase():
    """Test that a reference may name a task starting with an uppercase letter."""
    valid_ref("#Model1")


def test_ref_alphanumeric_body():
    """Test that a referenced task may contain letters, digits and underscores."""
    valid_ref("#model_1_A")


def test_ref_single_letter():
    """Test that a reference to a single letter task is valid."""
    valid_ref("#x")


def test_ref_single_underscore():
    """Test that a reference to a single underscore task is valid."""
    valid_ref("#_")


# invalid References


def test_ref_missing_hash():
    """Test that a reference without the leading hash is rejected."""
    invalid_ref("model")


def test_ref_digit_after_hash():
    """Test that a reference may not name a task starting with a digit."""
    invalid_ref("#1model")


def test_ref_hyphen():
    """Test that a hyphen is not allowed in a reference."""
    invalid_ref("#my-model")


def test_ref_space():
    """Test that a space is not allowed in a reference."""
    invalid_ref("#my model")


def test_ref_empty():
    """Test that the empty string is not a reference."""
    invalid_ref("")


def test_ref_hash_only():
    """Test that a bare hash is not a reference."""
    invalid_ref("#")


def test_ref_dot():
    """Test that the dotted port form is not matched by the Reference constraint."""
    invalid_ref("#model.output")
