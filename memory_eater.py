# import time
#
# data = []
# chunk_mb = 50
#
# print("Starting memory allocation...")
# while True:
#     # Allocate 50 MB of actual memory (bytearray forces physical RAM usage)
#     data.append(bytearray(chunk_mb * 1024 * 1024))
#     print(f"Allocated ~{len(data) * chunk_mb} MB")
#     time.sleep(0.2)
