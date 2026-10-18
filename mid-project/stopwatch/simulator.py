"""Button/display adapter around the UNCHANGED course CPU implementation.

Only the interactive main() call is removed when loading sim21.py. Its
instruction decoder, timer devices, interrupt dispatch and RETI run unchanged.
The adapter writes only the button mailbox and interrupt request, never time,
running state, lap count, lap values or result values.
"""
import ast
from collections import deque
import importlib.util
import io
from pathlib import Path
import sys
import types

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "tools"
ELAPSED, RUNNING, COUNT, PREVIOUS, COMMAND, RESULT, READY, MAIN = range(1100, 1108)
LAPS, DURATIONS = 1200, 1220
CYCLES_PER_SECOND = 100_000
TICKS_PER_SECOND = 100
RESULTS = {
    1: "Started / resumed", 2: "Paused", 3: "Lap saved; timer keeps running",
    4: "Memory full: 10 laps; timer continues. Reset to clear laps.",
    5: "Lap ignored: start the stopwatch first", 6: "Reset: stopped, laps cleared",
    7: "Unknown button command",
}


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Machine:
    def __init__(self, object_path=None, trace_buttons=False, trace_registers=False):
        self.trace_buttons = trace_buttons or trace_registers
        self.trace_registers = trace_registers
        self.instructions = {}
        self.register_trace = deque(maxlen=2000)
        self.cpu = load_module("cpu")
        self.memory = load_module("load")
        self.iot = load_module("iot")
        self.memory.print = lambda *a, **k: None
        path = TOOLS / "sim21.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        last = tree.body[-1]
        if not (isinstance(last, ast.Expr) and isinstance(last.value, ast.Call)
                and isinstance(last.value.func, ast.Name) and last.value.func.id == "main"):
            raise RuntimeError("Course simulator entry point changed; review adapter.")
        tree.body.pop()
        self.engine = types.ModuleType("stopwatch_course_cpu")
        self.engine.print = lambda *a, **k: None
        exec(compile(tree, str(path), "exec"), self.engine.__dict__)
        self.iot.initIO()
        self.memory.loadprogram(str(object_path or HERE / "stopwatch.obj"))
        self.queue = deque()
        self.events = deque(maxlen=500)
        self.interrupt_counts = [0, 0, 0, 0]
        self.active_button = None
        # Observe the exact CPU operations, including RETI followed by another
        # interrupt in the same cycle. The course implementation stays intact.
        original_interrupt = self.engine.interrupt
        original_reti = self.engine.doreti
        original_run = self.engine.run

        def interrupt(number):
            return_pc = self.engine.PC
            old_r31 = self.engine.R[31]
            before = self.engine.R.copy() if number == 2 and self.trace_registers else None
            original_interrupt(number)
            self.interrupt_counts[number] += 1
            if number == 2:
                self.trace_button(
                    f"ENTER INT2: PC {return_pc} -> {self.engine.PC}; "
                    f"r31 {old_r31} -> {self.engine.R[31]}; INT_ENABLE 1 -> 0")
                if self.trace_registers:
                    self.record_registers("ENTER INT2", return_pc, before)
                    self.trace_button("CONTEXT BEFORE SAVE: " + " ".join(
                        f"r{i}={self.engine.R[i]}" for i in range(16))
                        + f"; r29(SP)={self.engine.R[29]}")

        def reti():
            number = self.engine.intnum
            original_reti()
            if number == 2 and self.active_button is not None:
                self.events.append({
                    "cycle": self.cpu.clock, "command": self.active_button,
                    "result": self.get(RESULT), "elapsed": self.get(ELAPSED),
                    "count": self.get(COUNT), "return_pc": self.engine.PC,
                })
                self.trace_button(
                    f"RETI INT2: {RESULTS.get(self.get(RESULT), 'Unknown result')}; "
                    f"return PC={self.engine.PC}; elapsed={format_time(self.get(ELAPSED))}; "
                    f"laps={self.get(COUNT)}; INT_ENABLE 0 -> 1")
                self.active_button = None

        def run():
            if not (self.trace_registers and self.engine.intnum == 2
                    and not self.engine.intflag):
                original_run()
                return
            pc = self.engine.PC
            registers = self.engine.R.copy()
            addresses = list(range(ELAPSED, MAIN + 1)) + list(range(LAPS, LAPS + 10)) + list(range(DURATIONS, DURATIONS + 10))
            memory = {address: self.get(address) for address in addresses}
            instruction = self.instruction_at(pc)
            original_run()
            self.record_registers(instruction, pc, registers)
            changes = [f"r{i}: {old} -> {self.engine.R[i]}"
                       for i, old in enumerate(registers) if old != self.engine.R[i]]
            changes += [f"RAM[{address}]: {old} -> {self.get(address)}"
                        for address, old in memory.items() if old != self.get(address)]
            if instruction == "trap r29 #15":
                changes.append("SAVE r0-r15 to stack RAM[3001..3016]")
            elif instruction == "trap r29 #16":
                changes.append("RESTORE r0-r15 from stack")
            self.trace_button(f"STEP PC={pc} {instruction} | "
                              + ("; ".join(changes) or "no register/data change")
                              + f" | next PC={self.engine.PC}")

        self.engine.interrupt = interrupt
        self.engine.doreti = reti
        self.engine.run = run
        for _ in range(1000):
            self.step(1)
            if self.get(READY) and self.engine.intflag and not self.engine.cpuflag:
                break
        else:
            raise RuntimeError("Assembly did not initialize and reach WFI.")

    def get(self, address):
        return self.memory.getM(address)

    def trace_button(self, message):
        if self.trace_buttons:
            print(f"[cycle {self.cpu.clock:>9}] {message}", flush=True)

    def instruction_at(self, pc):
        word = self.get(pc)
        if word not in self.instructions:
            output = io.StringIO()
            previous_print = self.memory.print
            try:
                self.memory.print = lambda *a, **kw: print(*a, file=output, **kw)
                self.memory.disassemble(word)
            finally:
                self.memory.print = previous_print
            self.instructions[word] = output.getvalue().strip()
        return self.instructions[word]

    def record_registers(self, instruction, pc, before):
        self.register_trace.append({
            "cycle": self.cpu.clock, "instruction": instruction, "pc": pc,
            "next_pc": self.engine.PC, "before": before,
            "registers": self.engine.R.copy(), "interrupt_enabled": bool(self.engine.intflag),
            "memory": {str(a): self.get(a) for a in
                       list(range(ELAPSED, MAIN + 1)) + list(range(LAPS, LAPS + 10))
                       + list(range(DURATIONS, DURATIONS + 10)) + list(range(3001, 3017))},
        })

    def request(self, command):
        if len(self.queue) >= 32:
            return False
        self.queue.append(command)
        return True

    def step(self, cycles):
        for _ in range(cycles):
            # Serialize button edges until the previous ISR returns.
            if self.queue and self.active_button is None and self.get(READY):
                self.active_button = self.queue.popleft()
                self.memory.setM(COMMAND, self.active_button)
                self.cpu.intrq[2] = 1
                self.trace_button(
                    f"REQUEST INT2: command={self.active_button} -> mailbox[1104]; IRQ2 raised")
            self.engine.runoneclock()

    def snapshot(self):
        count = self.get(COUNT)
        return {
            "elapsed": self.get(ELAPSED), "running": bool(self.get(RUNNING)),
            "laps": [(self.get(LAPS + i), self.get(DURATIONS + i)) for i in range(count)],
            "cycle": self.cpu.clock, "main_passes": self.get(MAIN),
        }


def format_time(ticks):
    seconds, centiseconds = divmod(ticks, TICKS_PER_SECOND)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def main():
    import argparse
    import time
    import tkinter as tk
    from tkinter import ttk

    parser = argparse.ArgumentParser(description="S2 stopwatch GUI with terminal interrupt trace")
    parser.add_argument("--trace-registers", action="store_true",
                        help="show each button ISR instruction, register changes and stopwatch RAM changes")
    args = parser.parse_args()
    if not (HERE / "stopwatch.obj").exists():
        raise SystemExit("Run python build.py first.")
    if (HERE / "stopwatch.txt").stat().st_mtime > (HERE / "stopwatch.obj").stat().st_mtime:
        raise SystemExit("Assembly source changed. Run python build.py again.")
    machine = Machine(trace_buttons=True, trace_registers=args.trace_registers)
    print("Button interrupt trace: click Start/Pause, Save lap, or Reset in the GUI.\n"
          "Command 1 = start/pause, 2 = lap, 3 = reset.\n"
          "REQUEST = IRQ raised; ENTER = CPU entered ISR; RETI = ISR returned.\n"
          "Timer INT0 continues in the background; its count is shown in the GUI.", flush=True)
    root = tk.Tk()
    root.title("S2 Assembly Stopwatch | Interrupt demonstration")
    root.geometry("880x760")
    root.minsize(800, 680)
    body = ttk.Frame(root, padding=24)
    body.pack(fill="both", expand=True)
    ttk.Label(body, text="ASSEMBLY STOPWATCH", font=("Segoe UI", 20, "bold")).pack()
    ttk.Label(body, text="S2 assembly state • course CPU simulator • 10 lap slots").pack(pady=4)
    clock_label = ttk.Label(body, text="00:00.00", font=("Consolas", 48, "bold"))
    clock_label.pack(pady=12)
    state_label = ttk.Label(body, text="PAUSED")
    state_label.pack()
    buttons = ttk.Frame(body)
    buttons.pack(pady=16)
    message = tk.StringVar(value="Press S to start. Press L to save a lap at any moment while running.")

    def send(command):
        if not machine.request(command):
            message.set("Button queue full; please wait briefly.")

    for title, command in (("Start / Pause [S]", 1), ("Save lap [L]", 2), ("Reset [R]", 3)):
        ttk.Button(buttons, text=title, command=lambda c=command: send(c)).pack(side="left", padx=6)
    ttk.Label(body, textvariable=message, wraplength=790).pack(pady=4)
    table = ttk.Treeview(body, columns=("lap", "total", "duration"), show="headings", height=10)
    for name, title in (("lap", "Lap"), ("total", "Elapsed at capture"), ("duration", "Lap duration")):
        table.heading(name, text=title)
        table.column(name, width=200, anchor="center")
    table.pack(fill="x", pady=12)
    diagnostics = tk.StringVar()
    ttk.Label(body, textvariable=diagnostics, font=("Consolas", 10)).pack()
    ttk.Label(body, text="INT2 / button event log (after assembly RETI)").pack(anchor="w", pady=(12, 4))
    log = tk.Text(body, height=5, font=("Consolas", 10), state="disabled")
    log.pack(fill="both", expand=True)
    ttk.Label(body, text="Time is simulated: 1 tick = 1,000 CPU cycles = displayed 0.01 s.\n"
              "Pacing targets real time but is not a precision clock. Q closes the simulator.",
              justify="center").pack(pady=(12, 0))

    held = set()
    def key_down(event):
        key = event.keysym.lower()
        if key in held:
            return
        held.add(key)
        if key in {"s": 1, "l": 2, "r": 3}:
            send({"s": 1, "l": 2, "r": 3}[key])
        elif key == "q":
            root.destroy()
    root.bind("<KeyPress>", key_down)
    root.bind("<KeyRelease>", lambda e: held.discard(e.keysym.lower()))
    root.bind("<FocusOut>", lambda e: held.clear())
    last_time = time.perf_counter()
    fractional_cycles = 0.0
    last_laps = None

    def refresh():
        nonlocal last_time, fractional_cycles, last_laps
        now = time.perf_counter()
        # Bound catch-up work so the window remains responsive after suspension.
        fractional_cycles += min(now - last_time, 0.1) * CYCLES_PER_SECOND
        last_time = now
        cycles = int(fractional_cycles)
        fractional_cycles -= cycles
        machine.step(cycles)
        state = machine.snapshot()
        clock_label.config(text=format_time(state["elapsed"]))
        state_label.config(text=("RUNNING" if state["running"] else "PAUSED")
                           + f"  |  {len(state['laps'])}/10 laps")
        if state["laps"] != last_laps:
            for item in table.get_children():
                table.delete(item)
            for index, (total, duration) in enumerate(state["laps"], 1):
                table.insert("", "end", values=(index, format_time(total), format_time(duration)))
            last_laps = state["laps"]
        diagnostics.set(f"INT0 timer: {machine.interrupt_counts[0]}   "
                        f"INT2 buttons: {machine.interrupt_counts[2]}   "
                        f"Main-loop passes: {state['main_passes']}   CPU cycles: {state['cycle']}")
        while machine.events:
            event = machine.events.popleft()
            description = RESULTS[event["result"]]
            message.set(description)
            log.config(state="normal")
            log.insert("end", f"cycle {event['cycle']:>9}: INT2 -> {description}; "
                       f"RETI -> PC {event['return_pc']}\n")
            if int(log.index("end-1c").split(".")[0]) > 100:
                log.delete("1.0", "2.0")
            log.see("end")
            log.config(state="disabled")
        root.after(20, refresh)

    root.after(20, refresh)
    root.mainloop()


if __name__ == "__main__":
    main()
