import pytest

from business_analyst.security.pagination import parse_pagination


def test_default_pagination():
    assert parse_pagination().limit == 50
    assert parse_pagination().offset == 0


def test_string_pagination_is_parsed():
    result = parse_pagination(limit="25", offset="100")
    assert result.limit == 25
    assert result.offset == 100


@pytest.mark.parametrize(
    ("limit", "offset"),
    [
        (0, 0),
        (101, 0),
        (-1, 0),
        (10, -1),
        ("abc", 0),
        (10, "invalid"),
    ],
)
def test_invalid_pagination_is_rejected(limit, offset):
    with pytest.raises(ValueError):
        parse_pagination(
            limit=limit,
            offset=offset,
            max_limit=100,
        )
