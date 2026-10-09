"""Offline startup checks, executed during the image build."""
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

class Executed(Exception):
    pass

class StartupTests(unittest.TestCase):
    def invoke(self, command):
        with patch('sys.argv', ['entrypoint.py', command]), patch('os.execvp', side_effect=Executed):
            runpy.run_path('/opt/docker/entrypoint.py', run_name='__main__')

    def test_bootstrap_preserve_and_worker_gate(self):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                with patch.dict(os.environ, {'DASH_USER': 'test', 'DASH_PASS': 'test-password'}):
                    with self.assertRaises(Executed):
                        self.invoke('dashboard')
                    from instagram_ai_agent.core.config import NicheConfig
                    import yaml
                    config = NicheConfig(**yaml.safe_load(Path('niche.yaml').read_text()))
                    self.assertTrue(config.safety.require_review)
                    self.assertTrue(Path('.setup-required').exists())
                    with self.assertRaises(SystemExit):
                        self.invoke('run')
                    original = Path('niche.yaml').read_bytes()
                    with self.assertRaises(Executed):
                        self.invoke('dashboard')
                    self.assertEqual(original, Path('niche.yaml').read_bytes())
                    Path('.setup-required').unlink()
                    with self.assertRaises(Executed):
                        self.invoke('run')
                with patch.dict(os.environ, {'DASH_USER': '', 'DASH_PASS': ''}):
                    with self.assertRaises(SystemExit):
                        self.invoke('dashboard')
            finally:
                os.chdir(previous)

if __name__ == '__main__':
    unittest.main()
