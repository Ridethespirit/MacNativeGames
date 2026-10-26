"""Run BotW's actual aspect selection/camera functions against synthetic camera memory, without UIKit or game assets."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def function(source, signature):
    start = source.index(signature + ' {')
    body = source.index('{', start)
    depth = 1
    end = body + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class BotwIpadAspect(unittest.TestCase):
    def test_tablet_camera_transitions_and_original_aspect_override(self):
        compiler = shutil.which('cc') or shutil.which('clang') or shutil.which('gcc')
        if not compiler:
            self.skipTest('A C compiler is required')
        source = (ROOT/'games/totk/runtime/game_patches_botw.c').read_text(encoding='utf-8')
        functions = '\n'.join(function(source, signature) for signature in (
            'static void botw_aspect_word(int on)',
            'static void botw_aspect_apply(void)',
            'float runtime_aspect_now(void)',
            'static void botw_aspect_phone(float a)',
            'void runtime_aspect_view(double w, double h)',
        ))
        probe = r'''
#include <assert.h>
#include <math.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "games/totk/runtime/aspect_math.h"
#include "games/totk/third_party/d2r_gfx/gfx/nvn/totk_ui_squeeze.h"
#define TARGET_OS_IPHONE 1
#define UW_CAMERA_SINGLETON 0
#define UW_PERSPECTIVE_VTABLE 64
static uint8_t *g_uw_main;
static float g_uw_wide, g_uw_view;
static _Atomic(uint32_t) g_uw_on;
static int g_uw_written;
static _Atomic int g_uw_effective;
static _Atomic uint32_t word;
static _Atomic uint32_t *g_uw_word = &word;
static const char *setting;
static const char *test_getenv(const char *key) { assert(!strcmp(key, "TOTK_ASPECT")); return setting; }
#define getenv test_getenv
static void runtime_fail(const char *message) { (void)message; abort(); }
''' + functions + r'''
static void close_to(double a, double b) { assert(fabs(a-b) < 1e-5); }
static float requested(void) { uint32_t bits = atomic_load(&word); float a; memcpy(&a, &bits, 4); return a; }
int main(void) {
    uint8_t module[128] = {0}, camera[512] = {0};
    uint8_t *proj = camera + 0x38;
    uint64_t pointer = (uintptr_t)camera, vtable = (uintptr_t)module + UW_PERSPECTIVE_VTABLE;
    memcpy(module, &pointer, 8); memcpy(proj, &vtable, 8);
    /* View can arrive before the game module. It is remembered for installation. */
    runtime_aspect_view(1024, 768); close_to(g_uw_view, 4.0/3);
    assert(!atomic_load(&g_uw_on));
    g_uw_main = module;
    botw_aspect_phone(g_uw_view); close_to(requested(), 4.0/3);
    const double views[][2] = {{1024,768}, {2360,1640}, {2560,1600}, {1558,720}, {1024,768}};
    for (unsigned i=0; i<sizeof views/sizeof *views; i++) {
        float original = 16.0f/9.0f, target = (float)(views[i][0]/views[i][1]);
        runtime_aspect_view(views[i][0], views[i][1]);
        close_to(requested(), target);
        assert(runtime_aspect_now() == 0); /* wait for camera, not a stretched old frame */
        memcpy(proj + 0xb0, &original, 4);
        botw_aspect_apply();
        float actual; memcpy(&actual, proj + 0xb0, 4); close_to(actual, target);
        assert(proj[8] == 1 && runtime_aspect_now() == 0);
        proj[8] = 0; /* simulate the game's matrix rebuild with the selected aspect */
        botw_aspect_apply(); close_to(runtime_aspect_now(), target);
        runtime_aspect_view(views[i][0], views[i][1]); close_to(runtime_aspect_now(), target);
        double ux, uy; totk_ui_squeeze(target, &ux, &uy);
        close_to((target/(16.0/9.0)) * uy/ux, 1); /* UI circles remain circular after present */
        /* A camera changed by the game must not keep a stale full-screen confirmation. */
        float other = 1.5f; memcpy(proj + 0xb0, &other, 4);
        botw_aspect_apply(); assert(runtime_aspect_now() == 0);
    }
    const float invalid[] = {0, -1, NAN, INFINITY, 0.49f, 8.01f, 16.0f/9.0f, 1.78f};
    for (unsigned i=0; i<sizeof invalid/sizeof *invalid; i++) {
        botw_aspect_phone(4.0f/3.0f); botw_aspect_phone(invalid[i]);
        assert(!atomic_load(&g_uw_on) && requested() == 0 && runtime_aspect_now() == 0);
    }
    const char *overrides[] = {"0", "16:9"};
    for (unsigned i=0; i<2; i++) {
        setting = NULL; botw_aspect_phone(4.0f/3.0f);
        float target = requested(); memcpy(proj + 0xb0, &target, 4); g_uw_written = 1;
        setting = overrides[i]; botw_aspect_phone(4.0f/3.0f); botw_aspect_apply();
        float actual; memcpy(&actual, proj + 0xb0, 4); close_to(actual, 16.0/9.0);
        assert(requested() == 0 && runtime_aspect_now() == 0);
    }
    puts("botw ipad aspect ok");
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'probe.c'
            exe = Path(d)/'probe.exe'
            path.write_text(probe, encoding='utf-8')
            build = subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
                                    '-I', str(ROOT), str(path), '-lm', '-o', str(exe)],
                                   capture_output=True, text=True, timeout=60)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('botw ipad aspect ok', run.stdout)


if __name__ == '__main__':
    unittest.main()
