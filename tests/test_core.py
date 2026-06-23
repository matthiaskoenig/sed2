"""Tests for sed2 core data model."""
import pytest
from pydantic import BaseModel, ValidationError

from sed2.core import SId, Reference


class ModelWithSId(BaseModel):
    id: SId


def valid(id: str) -> None:
    ModelWithSId(id=id)


def invalid(id: str) -> None:
    with pytest.raises(ValidationError):
        ModelWithSId(id=id)


# --- valid SIds ---

def test_letter_start():
    valid("a")

def test_underscore_start():
    valid("_model")

def test_uppercase_start():
    valid("Model1")

def test_alphanumeric_body():
    valid("model_1_A")

def test_single_letter():
    valid("x")

def test_single_underscore():
    valid("_")

def test_long_id():
    valid("a" * 200)


# --- invalid SIds ---

def test_digit_start():
    invalid("1model")

def test_hyphen():
    invalid("my-model")

def test_space():
    invalid("my model")

def test_empty():
    invalid("")

def test_dot():
    invalid("model.1")

def test_hash_prefix():
    invalid("#model")


# --- Reference ---

class ModelWithReference(BaseModel):
    ref: Reference


def valid_ref(ref: str) -> None:
    ModelWithReference(ref=ref)


def invalid_ref(ref: str) -> None:
    with pytest.raises(ValidationError):
        ModelWithReference(ref=ref)


# valid References

def test_ref_letter_start():
    valid_ref("#model")

def test_ref_underscore_start():
    valid_ref("#_model")

def test_ref_uppercase():
    valid_ref("#Model1")

def test_ref_alphanumeric_body():
    valid_ref("#model_1_A")

def test_ref_single_letter():
    valid_ref("#x")

def test_ref_single_underscore():
    valid_ref("#_")


# invalid References

def test_ref_missing_hash():
    invalid_ref("model")

def test_ref_digit_after_hash():
    invalid_ref("#1model")

def test_ref_hyphen():
    invalid_ref("#my-model")

def test_ref_space():
    invalid_ref("#my model")

def test_ref_empty():
    invalid_ref("")

def test_ref_hash_only():
    invalid_ref("#")

def test_ref_dot():
    invalid_ref("#model.output")
