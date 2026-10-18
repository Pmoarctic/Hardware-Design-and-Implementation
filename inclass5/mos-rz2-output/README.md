# MOS-RZ2 assignment output

The source was compiled with rz36.exe, assembled with as21.exe, and run with sim21.exe from the local `../iot-rz/test` course bundle. All three returned exit code 0. The original ZIP was not present; the existing extracted tools were used.

The source is an unchanged copy of `../mos_rz2.txt`, which is byte-for-byte identical to `../iot-rz/test/mos-rz2.txt`.

The reader printed `+1 +2 +3 +4 +5`. The `interrupt0` lines are simulator diagnostics emitted during task switching. Both processes complete their five iterations.

Files:
- `output-screenshot.png`: screenshot of the browser displaying the actual recorded command log, ready to attach to your submission.
- `output.html`: local viewer for that command log.
- `build-and-run-log.txt`: compile, assemble, and run commands, exit codes, and simulator output.
- `run-output.txt`: unfiltered simulator output.
- `assemble-output.txt`: assembler diagnostics (empty on this successful run).
- `mos-rz2.txt`: unchanged RZ source.
- `mos-rz2-s.txt`: compiler-generated assembly.
- `mos-rz2-s.obj`: assembled object code.
- `mos-rz2-s.lis`: assembly listing and symbols.
- `run.ps1`: repeatable build and run script using the adjacent course tools.

To rerun from PowerShell in this folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1
```

To run the simulator interactively:

```powershell
..\iot-rz\test\sim21.exe mos-rz2-s.obj
```

Enter `g` to execute and `q` to quit. Rerunning the script refreshes the logs and HTML; the PNG records the run captured during preparation. No course-site submission has been made.
