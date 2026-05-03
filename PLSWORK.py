import os
import time
import sys
import multiprocessing as mp


input_file = "bgm022.ogg"
MAX_KEY_LEN = 4
BYTE_RANGE = range(256)


# -------------------------
# KEY STREAM
# -------------------------
def key_stream(key_len):
    if key_len == 1:
        for a in BYTE_RANGE:
            yield (a,)
    elif key_len == 2:
        for a in BYTE_RANGE:
            for b in BYTE_RANGE:
                yield (a, b)
    elif key_len == 3:
        for a in BYTE_RANGE:
            for b in BYTE_RANGE:
                for c in BYTE_RANGE:
                    yield (a, b, c)
    elif key_len == 4:
        for a in BYTE_RANGE:
            for b in BYTE_RANGE:
                for c in BYTE_RANGE:
                    for d in BYTE_RANGE:
                        yield (a, b, c, d)


# -------------------------
# FEEDER
# -------------------------
def feeder(key_len, key_queue, stop_flag):
    for key in key_stream(key_len):
        if stop_flag.value:
            break
        key_queue.put(key)


# -------------------------
# WORKER
# -------------------------
def worker(data, data_len, key_len, key_queue, stop_flag, shared_best):
    while not stop_flag.value:

        try:
            key = key_queue.get(timeout=1)
        except:
            return

        klen = len(key)

        for offset in range(key_len):

            # FAST OGG HEADER CHECK
            if data[0] ^ key[offset % klen] != ord('O'):
                continue
            if data[1] ^ key[(offset + 1) % klen] != ord('g'):
                continue
            if data[2] ^ key[(offset + 2) % klen] != ord('g'):
                continue
            if data[3] ^ key[(offset + 3) % klen] != ord('S'):
                continue

            out = bytearray(data_len)

            for i in range(data_len):
                out[i] = data[i] ^ key[(i + offset) % klen]

            shared_best["key"] = key
            shared_best["offset"] = offset
            shared_best["data"] = out
            stop_flag.value = True
            return


# -------------------------
# MAIN
# -------------------------
def main():
    data = open(input_file, "rb").read()
    data_len = len(data)

    manager = mp.Manager()
    stop_flag = manager.Value('b', False)
    shared_best = manager.dict()

    cpu_count = mp.cpu_count()

    for key_len in range(1, MAX_KEY_LEN + 1):

        key_queue = manager.Queue(maxsize=5000)

        feeder_proc = mp.Process(
            target=feeder,
            args=(key_len, key_queue, stop_flag)
        )
        feeder_proc.start()

        processes = []

        for _ in range(cpu_count):
            p = mp.Process(
                target=worker,
                args=(data, data_len, key_len, key_queue, stop_flag, shared_best)
            )
            p.start()
            processes.append(p)

        # -------------------------
        # FAST LIVE UI LOOP
        # -------------------------
        last_print = 0

        while any(p.is_alive() for p in processes):

            now = time.time()
            if now - last_print < 0.2:
                continue
            last_print = now

            running = sum(p.is_alive() for p in processes)

            if "key" in shared_best:
                status = f"BEST KEY: {shared_best['key']} | OFFSET: {shared_best['offset']}"
            else:
                status = "Searching..."

            line = (
                f"[CPU {cpu_count}/{running}] "
                f"[KeyLen {key_len}] "
                f"[Queue {key_queue.qsize() if hasattr(key_queue,'qsize') else '?'}] "
                f"{status}"
            )

            sys.stdout.write("\r" + line + " " * 10)
            sys.stdout.flush()

            if stop_flag.value:
                break

        feeder_proc.terminate()

        for p in processes:
            p.join()

        if stop_flag.value:
            break

    # -------------------------
    # OUTPUT
    # -------------------------
    if "data" in shared_best:
        open("output.ogg", "wb").write(shared_best["data"])

        print("\n\n🎯 FOUND WOOOOOOOOOO!")
        print("Key:", shared_best["key"])
        print("Offset:", shared_best["offset"])


if __name__ == "__main__":
    mp.freeze_support()
    main()