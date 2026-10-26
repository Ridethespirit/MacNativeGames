#include <assert.h>
#include <stdio.h>
#include "../games/totk/ios/Sources/touch_layout.h"

static void close_to(double a, double b) { assert(fabs(a - b) < 1e-6); }

static void tablet(double x, double y, double w, double h) {
    TouchPadLayout a = touch_pad_layout(x, y, w, h, x, 0, 1);
    double hit = fmin(36, a.diamond * .68), r = TOUCH_BUTTON_SIZE / 2.0;
    /* Controls stay inside the safe area and within a bounded reach on both sides of a large screen. */
    close_to(a.y + a.height, y + h);
    assert(a.height <= 360 && a.y >= y);
    assert(a.column + a.diamond + hit <= 190);
    assert(a.column - a.diamond - hit >= 0);
    assert(a.inner + hit <= 170);
    assert(a.outer - r >= 0 && a.outer + r <= w);
    assert(a.inner - a.outer > 2 * hit);  /* L/ZL and R/ZR do not share hit targets */
    assert(a.top - r >= 0 && a.height * .88 + r <= a.height);
    assert(a.height * .42 - a.diamond - hit >= 0);
    assert(hypot(a.stick_inset - a.column, a.height * .38 - a.diamond) > a.stick_radius + hit);
    assert(a.stick_inset - a.stick_radius >= 0 && a.stick_inset + a.stick_radius < w / 2);
    assert(a.height * .80 + a.stick_radius <= a.height);
    assert(hypot(a.stick_inset - a.outer, a.height * .08) > a.stick_radius + hit);  /* L3/R3 clear the sticks */
    assert(hypot(a.column - a.inner, a.height * .42 - a.diamond - a.top) > 2 * hit);  /* upper diamond/shoulder */
}

int main(void) {
    /* Representative safe-area sizes in points: mini, 4:3, 11-inch and 13-inch; windowed and inset bounds too. */
    tablet(0, 0, 1133, 723);
    tablet(0, 0, 1024, 748);
    tablet(0, 24, 1180, 776);
    tablet(0, 24, 1366, 980);
    tablet(24, 24, 900, 620);
    tablet(0, 0, 744, 340);
    TouchPadLayout small = touch_pad_layout(0, 0, 1024, 748, 0, 0, 1);
    TouchPadLayout large = touch_pad_layout(0, 0, 1366, 1004, 0, 0, 1);
    close_to(small.column, large.column); close_to(small.inner, large.inner);
    close_to(small.stick_inset, large.stick_inset);
    /* iPhone 14 landscape, with notch and home-indicator insets: preserve the previous layout. */
    TouchPadLayout phone = touch_pad_layout(47, 0, 750, 369, 47, 1, 0);
    close_to(phone.y, 0); close_to(phone.height, 369);
    close_to(phone.stick_radius, 59.04); close_to(phone.diamond, 51.66);
    close_to(phone.column, 66.33); close_to(phone.outer, 6.75); close_to(phone.inner, 89.25);
    close_to(phone.stick_inset, 178.506);
    puts("touch layout ok");
    return 0;
}
