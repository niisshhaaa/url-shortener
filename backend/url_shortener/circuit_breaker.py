# async circuit breaker (fail threshold = 3, reset = 10s)
import time
import asyncio
from typing import Optional

"""
CLOSED : calls/retries go through , failures are counted
OPEN: failures threshold exceeded, breaker open , calls/retries are blocked for cooldown period
HALF-OPEN: after cooldown, allow a small number of trial calls. 
If they succeed, go CLOSED and reset counters; if they fail, go back OPEN.
"""

class CircuitOpenError(RuntimeError):
    """Raised when circuit is open and calls should not be attempted."""
    pass


class CircuitBreaker:
    """
    Simple async circuit breaker.
    - opens after `fail_threshold` failures,
    - stays open for `recovery_timeout` seconds,
    - after timeout it enters a half-open state and tries one probe to go open or closed again.
    """

    def __init__(self, fail_threshold: int=3, recovery_time: float=10.0):
        self.fail_threshold = fail_threshold
        self.recovery_time = recovery_time
        self._failure_count = 0
        self._open_until:float=0.0
        self._lock = asyncio.Lock()
        self._half_open_probe_in_progress = False
        self._attempt=0

    async def allow_request(self)->bool:
        async with self._lock:

             # attempts to stop retrying at all
            if self._attempt>=2:
                print("Circuit breaker not allowing request.")
                return False
            
            now=time.time()
            if now < self._open_until:
                print("sleeping")
                await asyncio.sleep(delay=self._open_until-now)


            if self._open_until != 0.0 and now>=self._open_until:
                if not self._half_open_probe_in_progress:
                    self._half_open_probe_in_progress = True
                    return True
                return False
            
           

            #normal closed state  
            return True
        
    async def record_success(self)->None:
        async with self._lock:
            self._failure_count = 0
            self._open_until = 0.0
            self._half_open_probe_in_progress = False

    async def record_failure(self)->None:
        async with self._lock:
            self._failure_count = self._failure_count + 1

            if self._half_open_probe_in_progress:
                self._half_open_probe_in_progress = False
                self._open_until = time.time() + self.recovery_time
                self._failure_count = 0
                self._attempt+=1
            
            if self._failure_count >= self.fail_threshold:
                self._open_until = time.time() + self.recovery_time
                # keep fail_count at threshold (or reset to 0 )
                self._failure_count = 0
                self._attempt+=1

            print("Failure count:", self._failure_count)

            return 

    async def get_state(self) -> str:
        async with self._lock:
            return {
                "failure_count": self._failure_count,
                "open_until": self._open_until,
                "is_open": time.time() < self._open_until,
                "half_open_probe_in_progress": self._half_open_probe_in_progress,
                "attempt": self._attempt
            }
    
