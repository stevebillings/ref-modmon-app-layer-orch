from decimal import Decimal

import pytest

from domain.aggregates.product.validation import (
    validate_product_name,
    validate_product_price,
    validate_stock_quantity,
)
from domain.exceptions import ValidationError
from domain.validation import validate_positive_quantity


class TestValidateProductName:
    def test_valid_name(self) -> None:
        assert validate_product_name("Test Product") == "Test Product"

    def test_strips_whitespace(self) -> None:
        assert validate_product_name("  Test Product  ") == "Test Product"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_product_name("")
        assert exc_info.value.field == "name"

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_product_name("   ")
        assert exc_info.value.field == "name"

    def test_max_length(self) -> None:
        long_name = "a" * 200
        assert validate_product_name(long_name) == long_name

    def test_exceeds_max_length_raises(self) -> None:
        long_name = "a" * 201
        with pytest.raises(ValidationError) as exc_info:
            validate_product_name(long_name)
        assert exc_info.value.field == "name"
        assert "200" in exc_info.value.message


class TestValidateProductPrice:
    def test_valid_decimal(self) -> None:
        assert validate_product_price(Decimal("19.99")) == Decimal("19.99")

    def test_valid_string(self) -> None:
        assert validate_product_price("19.99") == Decimal("19.99")

    def test_valid_float(self) -> None:
        result = validate_product_price(19.99)
        assert result == Decimal("19.99")

    def test_valid_integer(self) -> None:
        assert validate_product_price(Decimal("10")) == Decimal("10")

    def test_one_decimal_place(self) -> None:
        assert validate_product_price(Decimal("10.5")) == Decimal("10.5")

    def test_zero_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_product_price(Decimal("0"))
        assert exc_info.value.field == "price"

    def test_negative_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_product_price(Decimal("-10.00"))
        assert exc_info.value.field == "price"

    def test_three_decimal_places_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_product_price(Decimal("10.999"))
        assert exc_info.value.field == "price"
        assert "2 decimal places" in exc_info.value.message

    def test_invalid_string_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_product_price("not a number")
        assert exc_info.value.field == "price"


class TestValidateStockQuantity:
    def test_valid_positive(self) -> None:
        assert validate_stock_quantity(100) == 100

    def test_zero_is_valid(self) -> None:
        assert validate_stock_quantity(0) == 0

    def test_negative_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_stock_quantity(-1)
        assert exc_info.value.field == "stock_quantity"


class TestValidatePositiveQuantity:
    def test_valid_positive(self) -> None:
        assert validate_positive_quantity(5) == 5

    def test_one_is_valid(self) -> None:
        assert validate_positive_quantity(1) == 1

    def test_zero_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_quantity(0)
        assert exc_info.value.field == "quantity"

    def test_negative_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_quantity(-1)
        assert exc_info.value.field == "quantity"
