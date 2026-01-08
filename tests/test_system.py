#!/usr/bin/env python3
"""
Test suite for Phone System components
Run this to verify your installation
"""

import sys
import unittest
import logging

# Suppress logs during tests
logging.basicConfig(level=logging.ERROR)


class TestImports(unittest.TestCase):
    """Test that all required packages can be imported"""
    
    def test_pyqt5(self):
        """Test PyQt5 import"""
        try:
            from PyQt5 import QtWidgets, QtCore, QtGui
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"PyQt5 import failed: {e}")
    
    def test_sounddevice(self):
        """Test sounddevice import"""
        try:
            import sounddevice as sd
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"sounddevice import failed: {e}")
    
    def test_numpy(self):
        """Test numpy import"""
        try:
            import numpy as np
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"numpy import failed: {e}")
    
    def test_pjsua2(self):
        """Test PJSIP Python bindings"""
        try:
            import pjsua2 as pj
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"pjsua2 import failed: {e}\nRun install.py to install PJSIP")


class TestPhoneLine(unittest.TestCase):
    """Test PhoneLine class"""
    
    def setUp(self):
        from src.phone_line import PhoneLine, LineState, AudioOutput
        self.PhoneLine = PhoneLine
        self.LineState = LineState
        self.AudioOutput = AudioOutput
    
    def test_line_creation(self):
        """Test creating a phone line"""
        line = self.PhoneLine(line_id=1)
        self.assertEqual(line.line_id, 1)
        self.assertEqual(line.state, self.LineState.IDLE)
        self.assertEqual(line.audio_output, self.AudioOutput.IFB)
    
    def test_audio_toggle(self):
        """Test audio output toggling"""
        line = self.PhoneLine(line_id=1)
        self.assertEqual(line.audio_output, self.AudioOutput.IFB)
        
        line.toggle_audio_output()
        self.assertEqual(line.audio_output, self.AudioOutput.PL)
        
        line.toggle_audio_output()
        self.assertEqual(line.audio_output, self.AudioOutput.IFB)
    
    def test_dial(self):
        """Test dialing"""
        line = self.PhoneLine(line_id=1)
        result = line.dial("+15551234567")
        self.assertTrue(result)
        self.assertEqual(line.state, self.LineState.DIALING)
        self.assertEqual(line.remote_number, "+15551234567")
    
    def test_status_string(self):
        """Test status string generation"""
        line = self.PhoneLine(line_id=1)
        self.assertEqual(line.get_status_string(), "Available")
        
        line.dial("+15551234567")
        self.assertIn("+15551234567", line.get_status_string())


class TestConfiguration(unittest.TestCase):
    """Test configuration file handling"""
    
    def test_sip_config_exists(self):
        """Test SIP config file exists"""
        import os
        self.assertTrue(os.path.exists("config/sip_config.json"))
    
    def test_audio_config_exists(self):
        """Test audio config file exists"""
        import os
        self.assertTrue(os.path.exists("config/audio_config.json"))
    
    def test_sip_config_valid(self):
        """Test SIP config is valid JSON"""
        import json
        with open("config/sip_config.json") as f:
            config = json.load(f)
            self.assertIn("sip_server", config)
            self.assertIn("username", config)
            self.assertIn("password", config)
    
    def test_audio_config_valid(self):
        """Test audio config is valid JSON"""
        import json
        with open("config/audio_config.json") as f:
            config = json.load(f)
            self.assertIn("audio_device_name", config)
            self.assertIn("output_channels", config)


class TestAudioSystem(unittest.TestCase):
    """Test audio system detection"""
    
    def test_audio_device_detection(self):
        """Test audio device detection"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            self.assertGreater(len(devices), 0, "No audio devices found")
        except Exception as e:
            self.fail(f"Audio device detection failed: {e}")
    
    def test_audio_device_outputs(self):
        """Test for multi-output audio device"""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            multi_output_found = False
            
            for device in devices:
                if device['max_output_channels'] >= 4:
                    multi_output_found = True
                    break
            
            if not multi_output_found:
                self.skipTest("No 4+ channel audio interface found")
        except Exception as e:
            self.fail(f"Audio output check failed: {e}")


def main():
    """Run all tests"""
    print("="*60)
    print("Phone System Test Suite")
    print("="*60)
    print()
    
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestImports))
    suite.addTests(loader.loadTestsFromTestCase(TestPhoneLine))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestAudioSystem))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("="*60)
    if result.wasSuccessful():
        print("✓ All tests passed!")
        print("="*60)
        return 0
    else:
        print("✗ Some tests failed")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
