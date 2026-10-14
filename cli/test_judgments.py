from string import ascii_letters, digits

from pytest import raises, warns

from cli.judgments import _generate_password, _project_name


def test_project_name() -> None:
    assert _project_name("ir-25", "42") == "ir-25-42"


def test_project_name_empty_query_id() -> None:
    with raises(ValueError):
        _project_name("ir-25", "")


def test_project_name_too_long() -> None:
    with warns(UserWarning):
        name = _project_name("ir-25", "x" * 200)
    assert len(name) == 100
    assert name.startswith("ir-25-")


def test_generate_password() -> None:
    password = _generate_password(length=16)
    assert len(password) == 16
    assert set(password) <= set(ascii_letters + digits)


def test_generate_password_is_random() -> None:
    assert len({_generate_password() for _ in range(10)}) == 10
