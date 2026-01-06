import sys
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QObject, Signal, Slot, QCoreApplication

# Add project root to path
sys.path.append('.')

from core.updater import UpdateChecker

class TestUpdateChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QCoreApplication instance for event loop
        if not QCoreApplication.instance():
            cls.app = QCoreApplication(sys.argv)

    def setUp(self):
        self.api_url = "http://mock-api.com"
        self.current_version = "1.0.0"

    @patch('core.updater.requests.get')
    @patch('core.updater.platform.system')
    def test_windows_update_correct(self, mock_system, mock_get):
        try:
            # Setup Windows environment
            mock_system.return_value = "Windows"
            
            # Mock API response
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "version": "1.0.1",
                "downloadUrl": "http://example.com/update.exe"
            }
            mock_get.return_value = mock_response
            
            checker = UpdateChecker(self.api_url, self.current_version)
            
            # Capture signals
            update_signal = MagicMock()
            checker.update_available.connect(update_signal)
            uptodate_signal = MagicMock()
            checker.up_to_date.connect(uptodate_signal)
            
            checker.run()
            
            # Verify
            mock_get.assert_called()
            call_args = mock_get.call_args[0][0]
            self.assertIn("platform=windows", call_args)
            
            update_signal.assert_called_with("1.0.1", "http://example.com/update.exe")
            uptodate_signal.assert_not_called()
            print("Test Windows Correct: PASS")
        except Exception as e:
            import traceback
            with open('error_log.txt', 'w') as f:
                traceback.print_exc(file=f)
            raise e

    @patch('core.updater.requests.get')
    @patch('core.updater.platform.system')
    def test_linux_update_correct(self, mock_system, mock_get):
        # Setup Linux environment
        mock_system.return_value = "Linux"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "version": "1.0.1",
            "downloadUrl": "http://example.com/update.deb"
        }
        mock_get.return_value = mock_response
        
        checker = UpdateChecker(self.api_url, self.current_version)
        
        update_signal = MagicMock()
        checker.update_available.connect(update_signal)
        
        checker.run()
        
        call_args = mock_get.call_args[0][0]
        self.assertIn("platform=linux", call_args)
        
        update_signal.assert_called()
        print("Test Linux Correct: PASS")

    @patch('core.updater.requests.get')
    @patch('core.updater.platform.system')
    def test_windows_wrong_extension(self, mock_system, mock_get):
        # Windows user gets .deb file (wrong configuration on server or wrong platform param)
        mock_system.return_value = "Windows"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "version": "1.0.1",
            "downloadUrl": "http://example.com/update.deb"
        }
        mock_get.return_value = mock_response
        
        checker = UpdateChecker(self.api_url, self.current_version)
        
        update_signal = MagicMock()
        checker.update_available.connect(update_signal)
        uptodate_signal = MagicMock()
        checker.up_to_date.connect(uptodate_signal)
        
        checker.run()
        
        # Should NOT emit update_available
        update_signal.assert_not_called()
        # Should emit up_to_date (as per logic to fail silently/gracefully)
        uptodate_signal.assert_called()
        print("Test Windows Wrong Extension: PASS")

    @patch('core.updater.requests.get')
    @patch('core.updater.platform.system')
    def test_linux_wrong_extension(self, mock_system, mock_get):
        # Linux user gets .exe file
        mock_system.return_value = "Linux"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "version": "1.0.1",
            "downloadUrl": "http://example.com/update.exe"
        }
        mock_get.return_value = mock_response
        
        checker = UpdateChecker(self.api_url, self.current_version)
        
        update_signal = MagicMock()
        checker.update_available.connect(update_signal)
        uptodate_signal = MagicMock()
        checker.up_to_date.connect(uptodate_signal)
        
        checker.run()
        
        update_signal.assert_not_called()
        uptodate_signal.assert_called()
        print("Test Linux Wrong Extension: PASS")

if __name__ == '__main__':
    unittest.main()
