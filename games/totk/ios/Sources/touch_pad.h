#import <UIKit/UIKit.h>

/* On-screen controller for iPhone/iPad, laid out like a Switch controller. It reports its state to the runtime through
   runtime_touch_pad_set (runtime/gamepad.m), which merges it with any physical controller. Hidden by default on iPad;
   Settings > Touch controls can restore it. Hidden mode also disables touch input, leaving the physical controller. */
@interface TOTKTouchPad : UIView
@end
