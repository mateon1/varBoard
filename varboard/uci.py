import subprocess, threading, time

class UCIEngine:
    def __init__(self, path, extra_args=()):
        self.path = path
        self.extra_args = tuple(extra_args)
        self.running = False
        self.engine_process = None
        self.reader_thread = None
        self.log = []

    def reader(self, pipe):
        for l in pipe:
            self.log.append((time.time(), l.decode("utf-8")))

    def start(self):
        assert not self.running
        self.engine_process = subprocess.Popen((self.path,) + self.extra_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.reader_thread = threading.Thread(target=lambda: self.reader(self.engine_process.stdout))
        self.reader_thread.setName("UCI Reader " + self.reader_thread.name)
        self.reader_thread.start()
        self.running = True

    def send_command(self, command):
        assert self.running
        self.engine_process.stdin.write((command.strip() + "\n").encode("utf-8"))
        self.engine_process.stdin.flush()

if __name__ == "__main__": # TEMPORARY - for testing
    FISH = "/home/mateon/shared/dev/Stockfish/releases/fairy-stockfish-14.0.1-ana0-dev-6bdcdd8"
    uci = UCIEngine(FISH)
    uci.start()
    uci.send_command("uci")
    time.sleep(0.5)
    for ts, l in uci.log:
        if not "option" in l: continue
        print(f"{ts:.6f} {l.strip()}")
    uci.send_command("quit")
    uci.reader_thread.join()
