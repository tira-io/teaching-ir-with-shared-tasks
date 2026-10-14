from pytest import mark

from cli.utils import group_user_name


@mark.parametrize(
    ("prefix", "group", "expected"),
    [
        ("ir-25", "Team 1", "ir-25-team-1"),
        ("ir-25", "  Die Sucher!  ", "ir-25-die-sucher"),
        ("ir-25", "Schöne Grüße", "ir-25-schone-grusse"),
    ],
)
def test_group_user_name(prefix: str, group: str, expected: str) -> None:
    assert group_user_name(prefix, group) == expected
