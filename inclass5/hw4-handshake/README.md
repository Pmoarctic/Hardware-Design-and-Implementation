# Homework 4: semaphore handshake

## Submit

- `application-only.txt`: application code only, including declarations, initialization, and processes A and B.
- `output-screenshot.png`: screenshot of a browser displaying the actual recorded build and simulator output.

The work has been prepared locally; it has not been uploaded to the course site.

## Run manually in PowerShell

Run these commands one at a time. No run.ps1 is needed.

```powershell
cd "E:\CEDT\Hardware Design and Implementation\inclass5\hw4-handshake"
..\iot-rz\test\rz36.exe handshake-rz.txt | Set-Content -Encoding ascii handshake-s.txt
..\iot-rz\test\as21.exe handshake-s.txt
..\iot-rz\test\sim21.exe handshake-s.obj
```

At the simulator's `>` prompt, type `g` and press Enter. Capture your terminal if you prefer a screenshot directly from your own terminal. Type `q` and press Enter to exit.

Compile `handshake-rz.txt`, which contains both the MOS support code and the application. `application-only.txt` is the submission excerpt and cannot be compiled by itself. If you change the program, update the matching application section in both files before rebuilding.

## How the handshake works

Both semaphores start at zero. A writes a number to `shareVar`, signals `toB`, and waits on `toA`. B waits on `toB`, adds one to the shared number, and signals `toA`. A then reads and prints the reply. A uses the returned number as the next number it sends. Both processes repeat five times and terminate.

The assignment does not specify the starting number; this version starts at zero. The round trips are 0 -> 1, 1 -> 2, 2 -> 3, 3 -> 4, and 4 -> 5. A prints:

```text
1
2
3
4
5
```

The semaphores ensure only the process whose turn it is accesses the shared value. A separate mutex is unnecessary. The `interrupt0` lines in the real output are diagnostics from the course simulator during task switching.

## Build details

The MOS support code is copied unchanged from `../mos_rz2.txt`, up to the original reader/writer application. The course executables are in `../iot-rz/test`. Compiler, assembler, and simulator all returned exit code 0, and the five printed values were checked in order.

- `handshake-rz.txt`: complete compilable source.
- `handshake-s.txt`, `handshake-s.obj`, `handshake-s.lis`: assembly, object code, and listing.
- `build-and-run-log.txt`: recorded commands, exit codes, and actual output.
- `run-output.txt`: unfiltered simulator output.
- `output.html`: local viewer used for the screenshot.
