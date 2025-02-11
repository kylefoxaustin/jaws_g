#!/usr/bin/env python3

import argparse
import os
import sys
import resource
import mmap
import random
import time
import signal
import psutil

class Jaws:
    def __init__(self, percentage, static_mode):
        self.percentage = percentage
        self.static_mode = static_mode
        self.buffer = None
        self.buffer_size = 0
        self.page_size = resource.getpagesize()

        # Get total system memory
        total_memory = psutil.virtual_memory().total
        self.buffer_size = int(total_memory * (self.percentage / 100))
        # Round down to nearest page size
        self.buffer_size = (self.buffer_size // self.page_size) * self.page_size
        if self.buffer_size == 0:
            print("Error: Calculated buffer size is zero.  Increase percentage.")
            sys.exit(1)


    def create_buffer(self):
        """Creates and locks a memory buffer."""
        try:
            # Use mmap with MAP_LOCKED for memory locking.  MAP_ANONYMOUS for anonymous mapping (not file-backed)
            # Use -1 for fd for anonymous mapping.  prot is for read/write access.
            flags = mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS | mmap.MAP_LOCKED
            self.buffer = mmap.mmap(-1, self.buffer_size, flags=flags, prot=mmap.PROT_READ | mmap.PROT_WRITE)
            #  Removed deprecated mlock call.  MAP_LOCKED already does this
        except Exception as e:
            print(f"Error creating buffer: {e}")
            sys.exit(1)


    def random_access(self):
        """Performs random reads and writes to the buffer."""
        if not self.buffer:
            print("Error: Buffer not created.")
            return

        print("Starting random memory access. Press Ctrl+C to exit.")
        try:
            while True:
                # Simulate bursty traffic (short, frequent accesses)
                for _ in range(random.randint(5, 20)):  # Short bursts
                    offset = random.randint(0, self.buffer_size - 1)
                    # Ensure offset is within valid bounds for writing a byte
                    if offset < self.buffer_size:
                      self.buffer[offset] = random.randint(0, 255)  # Write a random byte
                    
                    #read a value
                    if offset < self.buffer_size:
                        value = self.buffer[offset] # Read a byte

                # Simulate longer duration traffic (longer pauses)
                time.sleep(random.uniform(0.01, 0.2))  # Shorter pauses (more frequent)

                # Simulate longer, less frequent accesses.
                for _ in range(random.randint(1,5)):
                    offset = random.randint(0, self.buffer_size - 1)
                    if offset < self.buffer_size:
                      self.buffer[offset] = random.randint(0, 255)
                    if offset < self.buffer_size:
                        value = self.buffer[offset]

                time.sleep(random.uniform(0.1, 1.5)) # Longer pauses (less frequent)
        except KeyboardInterrupt:
            pass # Handle ctrl-c gracefully, loop is exited.

    def report_utilization(self):
        """Reports the memory utilization of the process."""
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        print(f"Jaws Memory Utilization: {mem_info.rss / (1024 * 1024):.2f} MB / Requested: {self.buffer_size / (1024 * 1024):.2f} MB")


    def cleanup(self):
        """Releases the allocated memory buffer."""
        if self.buffer:
            try:
                self.buffer.close()
                print("Memory buffer released.")
            except Exception as e:
                print(f"Error releasing buffer: {e}")
            self.buffer = None  # Set to None after releasing

    def run(self):
      self.create_buffer()
      self.report_utilization()

      if not self.static_mode:
        self.random_access()
      else:
        print("Static buffer created.  Press Ctrl-C to exit.")
        try:
          while True:
            time.sleep(1) # Sleep to avoid busy-waiting.
        except KeyboardInterrupt:
          pass  # Exit gracefully

      self.cleanup()



def signal_handler(sig, frame):
    """Handles Ctrl+C gracefully."""
    print("\nCtrl+C detected. Exiting...")
    if jaws_instance:
        jaws_instance.cleanup()
    sys.exit(0)


jaws_instance = None  # Global instance for signal handler

def main():
    global jaws_instance

    parser = argparse.ArgumentParser(description="Jaws: Memory Consumption Tool",
                                     formatter_class=argparse.RawTextHelpFormatter)  # Use RawTextHelpFormatter
    parser.add_argument("-low", action="store_true", help="Consume 30% of total RAM")
    parser.add_argument("-mid", action="store_true", help="Consume 50% of total RAM")
    parser.add_argument("-high", action="store_true", help="Consume 75% of total RAM")
    parser.add_argument("-static", action="store_true", help="Create a static buffer (no random access)")
    parser.add_argument("--help", action="help", default=argparse.SUPPRESS,
                    help="Show this help message and exit")


    args = parser.parse_args()

    if not (args.low or args.mid or args.high):
        print("Error: Must specify one of -low, -mid, or -high.")
        parser.print_help()
        sys.exit(1)

    if args.low:
        percentage = 30
    elif args.mid:
        percentage = 50
    elif args.high:
        percentage = 75
    else: # Should never happen, but good practice
        print("Error: Invalid memory option.")
        sys.exit(1)


    jaws_instance = Jaws(percentage, args.static)
    signal.signal(signal.SIGINT, signal_handler)  # Register signal handler
    jaws_instance.run()


if __name__ == "__main__":
    main()

