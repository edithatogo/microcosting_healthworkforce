import pytest
from _pytest.capture import CaptureFixture

from src.main import main


def test_main_does_not_raise_exceptions(capsys: CaptureFixture[str]) -> None:
    """
    Tests that the main function runs without raising exceptions.
    """
    with pytest.raises(SystemExit):
        main()
