/*
 * turbo_sim.c — LD_PRELOAD shim for task_1b_launch
 *
 * Eliminates the two major wall-clock bottlenecks in the MuJoCo simulator:
 *   1. nanosleep() — the frame-rate limiter that sleeps between physics steps
 *   2. glfwSwapInterval() — forces vsync off so swapBuffers doesn't block
 *
 * Compile:
 *   gcc -O2 -shared -fPIC turbo_sim.c -o turbo_sim.so -ldl
 *
 * Usage:
 *   LD_PRELOAD=./turbo_sim.so LD_LIBRARY_PATH=./lib ./task_1b_launch
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <time.h>

/* 1. Eliminate the frame-rate limiter sleep.
 *    The simulator calls nanosleep() to cap to ~60 FPS wall-clock.
 *    By returning immediately, physics steps run back-to-back. */
int nanosleep(const struct timespec *req, struct timespec *rem) {
    (void)req;
    (void)rem;
    return 0;
}

/* 2. Disable vsync so glfwSwapBuffers() doesn't block on display refresh.
 *    The simulator calls glfwSwapInterval(1) during init. We force it to 0. */
typedef void (*swap_interval_fn)(int);
void glfwSwapInterval(int interval) {
    static swap_interval_fn real_fn = NULL;
    if (!real_fn) {
        real_fn = (swap_interval_fn)dlsym(RTLD_NEXT, "glfwSwapInterval");
    }
    (void)interval;
    if (real_fn) real_fn(0);
}
