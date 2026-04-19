import pytest
import os
from src.executor.safe_io import SafeIO

class TestSafeIO:
    """SafeIO class unit tests for Sprint 1"""

    def test_initialization(self, temp_project_dir):
        """SafeIO initialization test"""
        safe_io = SafeIO(base_project_dir=temp_project_dir)
        assert safe_io.base_dir == os.path.abspath(temp_project_dir)
        assert os.path.exists(safe_io.base_dir)

    def test_safe_path_validation(self, safe_io_instance):
        """Safe path validation test"""
        # Valid paths
        assert safe_io_instance._is_safe_path("test.txt") == True
        assert safe_io_instance._is_safe_path("subdir/test.txt") == True
        assert safe_io_instance._is_safe_path("deep/nested/path/file.txt") == True
        
        # Invalid paths (directory traversal)
        assert safe_io_instance._is_safe_path("../outside.txt") == False
        assert safe_io_instance._is_safe_path("/etc/passwd") == False
        assert safe_io_instance._is_safe_path("../../../system") == False

    def test_safe_read_success(self, safe_io_instance, temp_project_dir):
        """Successful file reading test"""
        # Create test file
        test_content = "This is a test file content.\nSecond line."
        test_file = os.path.join(temp_project_dir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Read file
        result = safe_io_instance.safe_read("test.txt")
        
        assert result["status"] == "success"
        assert result["action"] == "read"
        assert result["path"] == "test.txt"
        assert result["content"] == test_content
        assert "logs" in result

    def test_safe_read_file_not_found(self, safe_io_instance):
        """File not found error test"""
        result = safe_io_instance.safe_read("nonexistent.txt")
        
        assert result["status"] == "error"
        assert result["action"] == "read"
        assert result["path"] == "nonexistent.txt"
        assert "見つかりませぬ" in result["logs"].lower() 

    def test_safe_read_path_violation(self, safe_io_instance):
        """Path violation test"""
        result = safe_io_instance.safe_read("../etc/passwd")
        
        assert result["status"] == "error"
        assert result["action"] == "read"
        assert result["path"] == "../etc/passwd"
        logs = result["logs"]
        if isinstance(logs, str):
            assert "不敬なる越権行為" in logs.lower()
        else:
            assert "不敬なる越権行為" in str(logs).lower()

    def test_safe_write_success(self, safe_io_instance):
        """Successful file writing test"""
        test_content = "New file content for testing."
        
        # Write file
        result = safe_io_instance.safe_write("new_test.txt", test_content)
        
        assert result["status"] == "success"
        assert result["action"] == "write"
        assert result["path"] == "new_test.txt"
        assert "logs" in result
        
        # Verify file was created and content is correct
        read_result = safe_io_instance.safe_read("new_test.txt")
        assert read_result["status"] == "success"
        assert read_result["content"] == test_content

    def test_safe_write_nested_directory(self, safe_io_instance):
        """Writing to nested directory test"""
        test_content = "Content in nested directory"
        
        # Write to nested path
        result = safe_io_instance.safe_write("subdir/nested/test.txt", test_content)
        
        assert result["status"] == "success"
        
        # Verify file exists in nested directory
        read_result = safe_io_instance.safe_read("subdir/nested/test.txt")
        assert read_result["status"] == "success"
        assert read_result["content"] == test_content

    def test_safe_write_path_violation(self, safe_io_instance):
        """Path violation test for write"""
        test_content = "This should not be written"
        
        result = safe_io_instance.safe_write("../dangerous.txt", test_content)
        
        assert result["status"] == "error"
        assert result["action"] == "write"
        assert result["path"] == "../dangerous.txt"
        assert "不敬なる越権行為" in result["logs"].lower() or "不敬なる越権行為" in result["logs"]

    def test_safe_write_empty_content(self, safe_io_instance):
        """Empty content writing test"""
        result = safe_io_instance.safe_write("empty.txt", "")
        
        assert result["status"] == "success"
        
        read_result = safe_io_instance.safe_read("empty.txt")
        assert read_result["status"] == "success"
        assert read_result["content"] == ""

    def test_safe_write_unicode_content(self, safe_io_instance):
        """Unicode content writing test"""
        unicode_content = "Japanese:  Japanese text:  Japanese text"
        
        result = safe_io_instance.safe_write("unicode.txt", unicode_content)
        
        assert result["status"] == "success"
        
        read_result = safe_io_instance.safe_read("unicode.txt")
        assert read_result["status"] == "success"
        assert read_result["content"] == unicode_content
