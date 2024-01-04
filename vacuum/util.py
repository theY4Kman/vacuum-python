import os
import threading


class StaticContentNamedPipe(threading.Thread, str):
    """Facilitates passing in-memory content to a spawned process as a named pipe (Unix-like only)

    >>> import subprocess
    >>> with StaticContentNamedPipe('my content') as named_pipe:
    ...     proc = subprocess.run(['cat', named_pipe], pass_fds=[named_pipe],
    ...                           stdout=subprocess.PIPE, text=True)
    ...     print(proc.stdout)
    ...
    my content
    """

    def __new__(cls, content, *, mode='w'):
        # NOTE: we inherit from str and override __new__ to enable direct usage
        #       of a StaticContentNamedPipe within Popen args. Its string value
        #       is equivalent to named_pipe.name.
        r, w = os.pipe()
        filename = f'/dev/fd/{r}'
        self = super().__new__(cls, filename)
        self.r, self.w = r, w
        self._filename = filename
        return self

    def __init__(self, content, *, mode='w'):
        self.content = content
        self.mode = mode
        super().__init__(name=f"{self.__class__.__name__}({self._filename})")

    def run(self):
        with open(self.w, self.mode) as fp:
            fp.write(self.content)

    @property
    def name(self):
        return self._filename

    @property
    def fileno(self):
        return self.r

    def __str__(self):
        return self._filename

    def __int__(self):
        # int(passed_fd) is used by Popen when currying file descriptors to spawned processes.
        # Since we want the spawned process to read from our named pipe, we use the read-side's fd.
        return self.r

    def __hash__(self):
        # set(pass_fds) is used by Popen when currying file descriptors to spawned processes
        # to ensure each distinct fd is only handled once.
        return hash(int(self))

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        os.close(self.r)
