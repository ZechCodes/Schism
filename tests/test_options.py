from schism.utils.options import Option, NullOptionException
from pytest import raises


def test_options():
    assert isinstance(Option[str].Value("test"), Option.Value)


def test_value():
    assert Option[str].Value("test").value == "test"


def test_value_default():
    assert Option[str].Value("test").get("fail") == "test"


def test_null():
    with raises(NullOptionException):
        Option[str].Null.value


def test_null_default():
    assert Option[str].Null.get("test") == "test"


def test_null_singleton():
    assert Option[None].Null() is Option[None].Null
