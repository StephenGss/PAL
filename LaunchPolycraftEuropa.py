import subprocess

from xvfbwrapper import Xvfb

vdisplay = Xvfb(width=1280, height=740)
vdisplay.start()

try:
    # launch stuff inside virtual display here.
    subprocess.Popen("./gradlew --no-daemon --stacktrace runclient", shell=True, cwd='../', stdout=subprocess.PIPE,
                     # stdin=subprocess.PIPE,  # DN: 0606 Removed for perforamnce
                     stderr=subprocess.STDOUT,  # DN: 0606 - pipe stderr to STDOUT. added for performance
                     bufsize=1,  # DN: 0606 Added for buffer issues
                     universal_newlines=True,  # DN: 0606 Added for performance - needed for bufsize=1 based on docs?
                     )
finally:
    # always either wrap your usage of Xvfb() with try / finally,
    # or alternatively use Xvfb as a context manager.
    # If you don't, you'll probably end up with a bunch of junk in /tmp
    vdisplay.stop()