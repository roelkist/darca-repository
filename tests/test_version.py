from darca_repository import __version__


def test_version_attributes_are_strings():
    assert isinstance(__version__.version, str)
    assert isinstance(__version__.copyright, str)
    assert isinstance(__version__.author, str)
