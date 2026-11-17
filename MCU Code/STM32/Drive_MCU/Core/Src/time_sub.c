#include <sys/time.h>
#include "cmsis_os.h"

/* micro-ROS links the C library's gettimeofday, which is empty on this board.
   This version gives the time since boot, from the FreeRTOS tick (1 tick = 1 ms),
   and removes the "_gettimeofday is not implemented" linker warning. */
int _gettimeofday(struct timeval *tv, void *tzvp)
{
  (void) tzvp;
  if (tv != NULL)
  {
    uint32_t ms = osKernelGetTickCount();
    tv->tv_sec  = ms / 1000U;
    tv->tv_usec = (ms % 1000U) * 1000U;
  }
  return 0;
}
