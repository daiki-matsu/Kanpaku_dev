import pytest
from src.main import hello_world

def test_hello_world():
    \"\"\"Test the hello_world function.\"\"\"
    result = hello_world()
    assert result == "Hello, World from Kanpaku Project!"
    assert isinstance(result, str)

def test_main_output(capsys):
    \"\"\"Test the main function output.\"\"\"
    from src.main import main
    main()
    captured = capsys.readouterr()
    assert "Hello, World from Kanpaku Project!" in captured.out
