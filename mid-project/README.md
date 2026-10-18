# Mid-project: lap stopwatch

The assembly stopwatch is implemented in `stopwatch/`. See [its instructions](stopwatch/README.md) and [presentation procedure](stopwatch/PRESENTATION.md).

## Contents

- `tools/`: unchanged Python course tools copied from `../iot-rz-py/s2/`.
  - `as21.py`: S2 assembly to object code.
  - `sim21.py`: simulator with interrupt support.
  - `cpu.py`, `load.py`, `iot.py`: simulator dependencies.
  - `lister.py`: optional assembly listing utility.
- `examples/add.txt`: unchanged course example from `../iot-rz-py/s2/add.txt`; prints `3`.
- `src/`: unused setup placeholder; the implementation is in `stopwatch/stopwatch.txt`.
- `stopwatch/`: assembly source, build helper, interactive simulation, checks and presentation instructions.

## Run the copied example

Requires Python 3; no additional packages are needed. From this folder in PowerShell:

```powershell
Set-Location examples
'add.txt' | python ../tools/as21.py
python ../tools/sim21.py
```

At `object file:`, enter `add.obj`. At `>>`, enter `g` to run, then `q` to quit. The example prints `3` and stops.

To produce an optional listing:

```powershell
'add.txt' | python ../tools/lister.py
```

The assembler writes `add.obj` and `add-f.txt` beside the source; the listing tool writes `add.lis`. Run from the source's directory and supply a simple filename because these course tools derive output names from the first dot in the input path.

The project program will be written in S2 assembly. Python runs the course assembler and simulator. Simulator ticks represent simulated execution, not automatically real seconds.
