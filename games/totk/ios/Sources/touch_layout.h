/* Touch geometry in points, independent of UIKit so tablet reach and safe-area bounds can be checked without a device. */
#pragma once
#include <math.h>

enum { TOUCH_BUTTON_SIZE = 46 };

typedef struct {
    double x, y, width, height;
    double stick_radius, diamond, column, outer, inner, stick_inset, top;
} TouchPadLayout;

static inline TouchPadLayout touch_pad_layout(double x, double y, double w, double h, double side, int phone, int pad) {
    /* Keep the tablet controls near the bottom corners, at phone-like distances rather than scaling their spacing
       with a 13-inch screen. The view still covers the whole screen for floating sticks and controller wake-up. */
    double height = pad ? fmin(h, 360) : h;
    TouchPadLayout a = {.x = x, .y = y + h - height, .width = w, .height = height};
    a.stick_radius = fmin(70, height * .16);
    a.diamond = fmin(52, height * .14);
    a.column = pad ? fmin(w * .14, 100) : w * .14;
    double shift = 0, span = pad ? fmin(w, 800) : w;
    if (phone) {
        /* Preserve the phone's reduced edge gap (including its notch inset). */
        double edge_gap = side + a.column - (a.diamond + TOUCH_BUTTON_SIZE / 2.0);
        a.column = fmax(a.column - edge_gap / 2, a.stick_radius + 4);
        shift = (side + w * .05 - TOUCH_BUTTON_SIZE / 2.0) / 2;
    }
    a.outer = span * .05 - shift;
    a.inner = span * .16 - shift;
    a.stick_inset = a.column + a.stick_radius * (pad ? .75 : 1.9);
    a.top = pad ? fmax(TOUCH_BUTTON_SIZE / 2.0, fmin(36, a.diamond * .68)) : height * .12;
    return a;
}
