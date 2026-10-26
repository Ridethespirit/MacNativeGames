"""Shared iPad touch geometry and source guards for UIKit paths that require an Apple device."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOTK = ROOT/'games/totk'


class IosLayout(unittest.TestCase):
    def test_tablet_reach_safe_area_and_phone_geometry(self):
        compiler = shutil.which('cc') or shutil.which('clang') or shutil.which('gcc')
        if not compiler:
            self.skipTest('A C compiler is required')
        with tempfile.TemporaryDirectory() as d:
            exe = Path(d)/'touch-layout.exe'
            build = subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
                                    str(ROOT/'tests/test_ios_touch_layout.c'), '-lm', '-o', str(exe)],
                                   capture_output=True, text=True, timeout=60)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('touch layout ok', run.stdout)

    def test_metal_view_relayouts_on_ios_too(self):
        source = (TOTK/'ios/Sources/main.m').read_text(encoding='utf-8')
        view = source.split('@implementation TOTKMetalView', 1)[1].split('@end', 1)[0]
        self.assertNotIn('#if', view)
        self.assertIn('runtime_ios_sync_drawable(self)', view)
        self.assertIn('runtime_ios_sync_safe_area(self)', view)

    def test_universal_target_launch_screen_and_memory_entitlement(self):
        import plistlib
        project = (TOTK/'ios/project.yml').read_text(encoding='utf-8')
        self.assertIn('TARGETED_DEVICE_FAMILY: "1,2"', project)
        self.assertIn('UILaunchScreen: {}', project)
        self.assertIn('UIInterfaceOrientationLandscapeLeft', project)
        self.assertIn('UIInterfaceOrientationLandscapeRight', project)
        ents = plistlib.loads((TOTK/'ios/Sources/TOTK.entitlements').read_bytes())
        self.assertIs(ents['com.apple.developer.kernel.increased-memory-limit'], True)
        build = (TOTK/'ios/tools/build_ipa.py').read_text(encoding='utf-8')
        self.assertIn('if not vision: validate_ios_product(app)', build)


if __name__ == '__main__':
    unittest.main()
