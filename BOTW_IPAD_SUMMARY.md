# BotW iPad support

Implemented on Windows; **no IPA was built, signed, installed or played here**. BotW 1.6.0 is the primary verification target. No game assets, real keys or dumps were added. Prepared for Mac build and real-device verification.

## Findings

- `build_app.py --platform ios` already routes both `botw160` and `botw190` through `games/totk/ios/tools/build_ipa.py`. It selects `GAME_BOTW` and the version define, BotW patches/manifests/shader list, optional DLC and the separate `org.macnativegames.botw` identity. Only native **visionOS**, not iPadOS, is gated to TotK.
- `ios/project.yml` already targets device families **1,2**, both landscape orientations, a scene delegate and `UILaunchScreen: {}`. The empty source Info.plist is populated by XcodeGen; a missing storyboard is not a missing launch screen. Xcode derives `UIDeviceFamily` from the [target build setting](https://help.apple.com/xcode/mac/current/en.lproj/itcaec37c2a6.html).
- The shared touch view respected safe-area insets, floating sticks and controller hiding, but tablet control spacing grew with screen size. Metal drawable layout updates were compiled only for visionOS, leaving iOS/iPadOS vulnerable to stale launch/resize dimensions.
- The original BotW mobile path deliberately letterboxed views narrower than 16:9, while TotK could follow them. The full-screen follow-up now accepts tablet ratios through the shared aspect arithmetic, preserving vertical field of view and using the existing BotW camera writer and HUD correction. Narrower views show less at the sides. Device verification is still pending.
- Both BotW versions already use handheld 960×540 rendering and a 1280×720 canvas on iOS, with the game's upscale. The shared runtime reports a roughly 3.2 GiB game pool plus host/GPU overhead. The increased-memory-limit entitlement and installer profile checks already exist; [Apple does not guarantee extra memory on every device](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.kernel.increased-memory-limit). No larger heaps or native-resolution tablet rendering were enabled.

## Changes

- `games/totk/ios/tools/build_ipa.py`: validate the actual Xcode product's universal device family, landscape support (including iPad overrides) and launch-screen declaration before packaging.
- `games/totk/ios/Sources/touch_layout.h` (new), `touch_pad.m`: compact iPad controls in the bottom 360 safe-area points, bounded side spacing and nearer resting sticks. Preserve iPhone geometry and controller behavior. This shared improvement also applies to TotK.
- `games/totk/ios/Sources/main.m`, `games/totk/runtime/frontend_ios.m`: synchronize drawable/camera dimensions on iOS layout changes and resize the startup labels/progress bar; retain the existing drawable pixel budget.
- `games/totk/runtime/game_patches_botw.c`: follow iPad ratios below 16:9, release the override at native 16:9 or when explicitly disabled, and clear stale camera confirmation on a ratio change or camera mismatch.
- Tests: `tests/test_ios_layout.py`, `tests/test_ios_touch_layout.c` (new); extend `tests/test_ios_packaging.py` and `tests/test_game_selection.py`.
- Documentation: `docs/install.md`, `docs/install.zh-CN.md`, `README.md`, and this summary distinguish build support from verified gameplay.

## Controller-only iPad preference

Both Zelda games now default to a hidden, non-interactive touch layer on iPad, including the virtual sticks and FPS button. Touching the display or disconnecting the controller does not restore it. The system Settings pane has a shared `TOTK_TOUCH_CONTROLS` preference: device default (iPad hidden, iPhone automatic), hidden/controller only, automatic (the existing controller/touch wake-up behavior), and always visible. Changes are read when defaults change and when returning to the app. Hiding clears active touch buttons/sticks and releases the virtual controller state without changing physical-controller input. The shared Settings bundle is also copied into BotW builds; only TotK's docked-mode setting is removed there. With controls hidden, FPS remains configurable in system Settings after relaunch.

BotW continues to reuse TotK's universal iOS app, Metal resize handling, controller backend and installer. BotW keeps its own version-specific patches, shaders, camera handling and game-data identity; its iPad gameplay still needs verification.

## Build and install on a Mac

Use an Apple silicon Mac with macOS 26+, full Xcode 26+ including iOS/Metal toolchains, and the dependencies in [the install guide](docs/install.md#iphone-and-ipad). Use only your own dumped game, update, keys and firmware. Pair the iPad (iPadOS 26+), enable Developer Mode and add your signing account to Xcode.

```sh
python3.14 build_app.py ~/Games/botw-base.nsp -k ~/keys/prod.keys \
  --update ~/Games/botw-1.6.0.nsp --firmware ~/Games/firmware \
  --platform ios --ios-game-data documents -o ~/Games/BotW.ipa
python3.14 games/totk/ios/tools/install_device.py ~/Games/BotW.ipa \
  --device "<iPad name>" --game-data ~/Games/BotW_build/totk/extracted/botw160/romfs/romfs.bin
```

Keep `BotW-shader-seed` beside the IPA. Adjust the image path if using `--work`. A combined 1.6.0 XCI needs no `--update`; separate optional DLC uses `--dlc`. Saves stay in the BotW app's `Documents/save` container. 1.9.0 already follows the same build route but remains experimental on mobile.

## Validation and remaining TODOs

- Full-screen follow-up adds `tests/test_botw_ipad_aspect.py`: compiles the actual BotW ratio-selection and camera-update functions against synthetic camera memory, exercising tablet/phone transitions, native-aspect overrides, invalid ratios, stale camera confirmation and HUD proportion arithmetic. It replaces the old source-string check that expected tablet letterboxing. The updated targeted suite passed **34 tests with 1 macOS SDK test skipped**; `git diff --check` passed. It does not execute game camera machine code or Metal/UIKit. First-frame 4:3 camera initialization, maps, menus, cutscenes and world markers remain device checks.

- Windows: **34 targeted tests passed, 1 macOS SDK test skipped**, using Python 3.11 and a temporary portable Zig C compiler. This covered iOS layout, selected packaging tests, display pacing, visionOS configuration, aspect arithmetic and game selection. The C geometry probe exercised mini/4:3/11-inch/13-inch and inset/window-sized areas, control separation and the previous iPhone geometry. Test inputs were synthetic; runtime source guards do not prove UIKit behavior.
- `git diff --check` passed. The full Python 3.14/macOS source gate remains to run: `make check`. The existing POSIX deletion tests were not part of this Windows subset.
- Controller-only follow-up: reran the same 35 targeted tests (**34 passed, 1 macOS SDK test skipped**), validated the Settings plist and confirmed the touch preference survives BotW's Settings filtering. These checks do not execute UIKit; verify the default hidden state, ignored screen touches, controller disconnect/reconnect, and all visibility choices on both games with an iPad. Confirm changing visibility releases held virtual buttons/sticks and that the choice persists across relaunches.
- **TODO (Mac):** build a real 1.6.0 IPA; confirm the final plist has `UIDeviceFamily = [1,2]`, sign with the memory entitlement, and install on iPad and iPhone.
- **TODO (device):** test cold launch in both device orientations, rotation both ways, letterboxing/HUD proportions, home-indicator clearance, simultaneous sticks/buttons, 30/60 selection, controller connect/disconnect, background/resume, saves and optional DLC. Check TotK for shared-layout regressions.
- **TODO (device):** verify window resizing and shader-import progress on iPadOS 26+. The existing landscape/`UIRequiresFullScreen` policy remains; full multitasking adoption is outside this patch ([Apple migration guidance](https://developer.apple.com/documentation/technotes/tn3192-migrating-your-app-from-the-deprecated-uirequiresfullscreen-key)). A TODO comment marks the layout hook.
- **TODO (device):** sustained play in busy areas, memory/thermal measurements and missing shader variants. No minimum BotW iPad model or performance claim is established; memory-pressure termination and incomplete shader coverage remain risks.
