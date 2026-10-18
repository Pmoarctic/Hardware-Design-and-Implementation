# Presentation procedure (about 5 minutes)

## Before presenting

1. Open PowerShell and run:

   ```powershell
   Set-Location 'E:\CEDT\Hardware Design and Implementation\mid-project\stopwatch'
   python build.py
   python test_stopwatch.py
   python simulator.py
   ```

2. Confirm the test summary says `OK`. Keep the simulator window and `stopwatch.txt` ready to show. `stopwatch.lis` is useful if asked about instruction addresses.
3. Press Reset. Start with `00:00.00`, PAUSED and an empty table.
4. Keep the window focused for S/L/R shortcuts. Buttons work too. Avoid holding keys.

## Live sequence

| Approximate stage | Your action | What the audience should see | What to explain |
|---|---|---|---|
| 0:00-0:30 | Introduce the project. | Initial window. | “This is an S2 assembly stopwatch. A timer interrupt updates elapsed time, and a button interrupt records laps while timing continues.” |
| 0:30-1:00 | Press S; wait roughly 3 seconds. | Time and INT0 count increase. | “The simulated timer raises INT0 every 1,000 CPU cycles. The assembly handler increments elapsed ticks when running is enabled.” |
| 1:00-1:30 | Press L, wait briefly, then press L again. | Two rows appear and the clock keeps advancing. | “INT2 saves the current elapsed count in RAM. It subtracts the previous capture to calculate lap duration, then returns with RETI.” |
| 1:30-2:00 | Point to the event log and main-loop counter. | INT2 log entries with return PCs; main-loop passes continue increasing. | “The CPU returns to the interrupted program after handling each request. The log is shown after the ISR returns.” |
| 2:00-2:30 | Press S to pause; wait 2 seconds. Press L once. | Elapsed time stays fixed; lap request is ignored. INT0 still increases. | “Timer interrupts still arrive, but the running flag prevents time accumulation. Paused laps are deliberately rejected.” |
| 2:30-3:00 | Press S to resume, then L. | Time continues from its paused value and a third lap is saved. | “Pausing preserves elapsed time and previous laps. Paused time is excluded from the next lap duration.” |
| 3:00-3:30 | Optional: keep clicking L until 10 rows, then once more. | Full-memory message; existing rows stay intact; timer continues. | “The assembly bounds check prevents writing beyond the ten allocated lap slots.” |
| 3:30-4:00 | Press R. | Timer stops at zero; all rows disappear. | “The reset command clears the state and both arrays in its interrupt handler.” |
| 4:00-5:00 | Show assembly labels and explain the architecture. | `timer_isr`, `button_isr`, `save_lap`, `button_done`, `main_loop`. | Walk through the sequence below. |

Capture times are chosen live; do not promise exact timestamps. Several quick presses within one tick can legitimately produce a zero-duration lap.

## Code explanation to rehearse

1. Initialization sets the stack pointer, writes ISR addresses to vector locations 1000 and 1002, configures timer0 and enables IRQ0/IRQ2.
2. `main_loop` counts normal execution passes, then uses `wfi` to wait for an interrupt.
3. The CPU saves the return PC in r31 and jumps to the appropriate ISR. The handler saves r0-r15 with `trap r29 #15`.
4. `timer_isr` checks `running` and increments `elapsed`.
5. For a Lap button, `save_lap` checks running state and capacity, writes the timestamp and duration, then increments `lap_count`.
6. `trap r29 #16` restores the registers; `reti` restores execution at the saved PC.

Button flow: **button -> mailbox + IRQ2 request -> course interrupt dispatcher -> assembly ISR -> RAM updated -> RETI -> display reads RAM**.

## Likely questions

**Is the project written in assembly or Python?**

All stopwatch behavior, state changes and lap arithmetic run as assembled S2 instructions. Python is the course CPU simulator plus the input/display adapter. The adapter writes a button command and raises IRQ2; it does not calculate or write elapsed time or lap results.

**Why add a Python display adapter?**

The original monitor blocks while reading input and limits each run. The adapter lets simulated CPU execution continue while the user presses buttons. The copied assembler and CPU implementation remain unchanged; the adapter bypasses only the original interactive entry point and console presentation.

**Are these hardware interrupts?**

They are simulated device interrupts inside the S2 virtual CPU. They use the course interrupt vector, request and mask mechanism, register saving and RETI. No physical microcontroller or physical interrupt pin is involved.

**Is displayed time exactly real time?**

No. One tick is 1,000 simulated cycles, displayed as 0.01 seconds. The launcher paces execution toward real time, but host scheduling and suspension can introduce lag. Timing is suitable for demonstrating interrupt behavior.

**What happens if Lap and a timer tick arrive together?**

The course dispatcher checks IRQ0 before IRQ2. The timer handler runs first, then the lap handler captures the updated count. Interrupt nesting is disabled, so the timer handler cannot interrupt the lap handler halfway through a capture. This case is covered by a test.

**Where are laps stored, and how many?**

Cumulative timestamps occupy RAM 1200-1209; lap durations occupy 1220-1229. There are ten slots. These records last until Reset or closing the simulation; they are not saved to a file.

**Why do timer interrupts continue during pause?**

Pause changes the assembly running flag rather than disabling the timer device. The ISR keeps handling ticks but does not add them to elapsed time.

## Console fallback

If a graphical display is unavailable, run `python demo.py`. It runs a scripted sequence on the same assembled program and course CPU, printing lap capture, pause/resume, and reset results. Explain that this is a scripted demonstration instead of live button input.
