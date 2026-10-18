"""Scripted presentation fallback, using the same object and CPU as the UI."""
from simulator import Machine, RESULTS, format_time


def main():
    machine = Machine()

    def button(command):
        machine.request(command)
        for _ in range(2000):
            machine.step(1)
            if not machine.queue and machine.active_button is None:
                event = machine.events[-1]
                print(f"INT2 -> {RESULTS[event['result']]} -> RETI (PC {event['return_pc']})")
                return
        raise RuntimeError("Button ISR did not complete")

    print("Scripted S2 assembly demonstration; time below is simulated.")
    button(1)
    machine.step(320_000)
    button(2)
    machine.step(465_000)
    button(2)
    for number, (total, duration) in enumerate(machine.snapshot()["laps"], 1):
        print(f"Lap {number}: elapsed {format_time(total)}, duration {format_time(duration)}")
    button(1)
    before = machine.snapshot()["elapsed"]
    machine.step(200_000)
    print(f"After a simulated 2-second pause: {format_time(machine.snapshot()['elapsed'])}")
    assert before == machine.snapshot()["elapsed"]
    button(1)
    machine.step(100_000)
    button(2)
    print("Laps after resume:", machine.snapshot()["laps"])
    button(3)
    state = machine.snapshot()
    assert not state["running"] and state["elapsed"] == 0 and not state["laps"]
    print("Reset verified: stopped, zero elapsed time, zero laps.")


if __name__ == "__main__":
    main()
