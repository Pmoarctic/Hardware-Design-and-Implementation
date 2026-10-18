"""Behavior checks against assembled instructions on the course CPU."""
import unittest
from contextlib import redirect_stdout
import io

from simulator import (Machine, ELAPSED, RUNNING, COUNT, PREVIOUS, LAPS,
                       DURATIONS, COMMAND, RESULTS)


class StopwatchTests(unittest.TestCase):
    def setUp(self):
        self.machine = Machine()

    def button(self, command):
        m = self.machine
        m.request(command)
        for _ in range(2000):
            m.step(1)
            if m.active_button is None and not m.queue:
                return m.events[-1]
        self.fail("Button interrupt did not return")

    def test_initial_state_and_lap_while_paused(self):
        self.assertEqual(self.machine.snapshot()["laps"], [])
        self.assertFalse(self.machine.get(RUNNING))
        self.assertEqual(self.button(2)["result"], 5)
        self.machine.step(5000)
        self.assertEqual(self.machine.get(ELAPSED), 0)

    def test_timer_laps_pause_and_resume(self):
        m = self.machine
        self.assertEqual(self.button(1)["result"], 1)
        before = m.get(ELAPSED)
        m.step(10000)
        self.assertEqual(m.get(ELAPSED) - before, 10)
        first = self.button(2)
        m.step(7000)
        second = self.button(2)
        self.assertEqual(m.snapshot()["laps"], [
            (first["elapsed"], first["elapsed"]),
            (second["elapsed"], second["elapsed"] - first["elapsed"]),
        ])
        self.assertEqual(m.get(RUNNING), 1)
        self.assertEqual(self.button(1)["result"], 2)
        paused = m.get(ELAPSED)
        m.step(10000)
        self.assertEqual(m.get(ELAPSED), paused)
        self.button(1)
        m.step(10000)
        self.assertGreater(m.get(ELAPSED), paused)

    def test_capacity_preserves_existing_laps_and_adjacent_memory(self):
        m = self.machine
        self.button(1)
        m.memory.setM(LAPS + 10, 9876)
        m.memory.setM(DURATIONS + 10, 6789)
        for _ in range(10):
            m.step(2000)
            self.assertEqual(self.button(2)["result"], 3)
        saved = m.snapshot()["laps"]
        self.assertEqual(self.button(2)["result"], 4)
        self.assertEqual(m.snapshot()["laps"], saved)
        self.assertEqual(m.get(LAPS + 10), 9876)
        self.assertEqual(m.get(DURATIONS + 10), 6789)
        self.assertTrue(m.get(RUNNING))

    def test_reset_while_running_clears_and_stops(self):
        m = self.machine
        self.button(1)
        m.step(5000)
        self.button(2)
        self.assertEqual(self.button(3)["result"], 6)
        for address in (ELAPSED, RUNNING, COUNT, PREVIOUS, COMMAND):
            self.assertEqual(m.get(address), 0)
        self.assertEqual([m.get(LAPS + i) for i in range(10)], [0] * 10)
        self.assertEqual([m.get(DURATIONS + i) for i in range(10)], [0] * 10)
        m.step(5000)
        self.assertEqual(m.get(ELAPSED), 0)
        self.button(1)
        m.step(5000)
        self.assertGreater(m.get(ELAPSED), 0)

    def test_simultaneous_timer_and_button_requests(self):
        m = self.machine
        self.button(1)
        m.step(1000)
        # Align both requests at a timer boundary while CPU is sleeping.
        while m.cpu.timer0 != 999 or m.engine.cpuflag:
            m.step(1)
        before = m.get(ELAPSED)
        saved = self.button(2)
        self.assertEqual(saved["elapsed"], before + 1)
        self.assertEqual(m.get(COUNT), 1)
        self.assertEqual(m.get(LAPS), before + 1)

    def test_interrupt_restores_registers_stack_and_returns_to_main(self):
        m = self.machine
        values = [100 + i for i in range(16)]
        m.engine.R[:16] = values
        passes = m.snapshot()["main_passes"]
        self.button(2)
        self.assertEqual(m.engine.R[:16], values)
        self.assertEqual(m.engine.R[29], 3000)
        m.step(2000)
        self.assertGreater(m.snapshot()["main_passes"], passes)
        self.assertEqual(m.engine.R[29], 3000)

    def test_queued_buttons_are_not_lost(self):
        m = self.machine
        for command in (1, 2, 2, 1, 2, 3):
            self.assertTrue(m.request(command))
        m.step(3000)
        self.assertEqual([e["result"] for e in m.events], [1, 3, 3, 2, 5, 6])
        self.assertEqual(m.snapshot()["laps"], [])
        self.assertEqual(m.get(ELAPSED), 0)

    def test_register_trace_matches_execution_and_restores_context(self):
        with redirect_stdout(io.StringIO()):
            m = Machine(trace_registers=True)
            self.machine = m
            self.button(1)
            m.step(320_000)
            m.register_trace.clear()
            event = self.button(2)
        trace = list(m.register_trace)
        self.assertEqual(trace[0]["instruction"], "ENTER INT2")
        self.assertEqual(trace[-1]["instruction"], "reti")
        subtraction = next(s for s in trace if s["instruction"] == "sub r4 r1 r3")
        self.assertEqual(subtraction["registers"][4], event["elapsed"])
        saved = next(s for s in trace if s["instruction"] == "trap r29 #15")
        self.assertEqual(saved["registers"][29], 3016)
        self.assertEqual([saved["memory"][str(3001+i)] for i in range(16)], trace[0]["registers"][:16])
        self.assertEqual(trace[-1]["registers"][:16], trace[0]["registers"][:16])
        self.assertEqual(trace[-1]["registers"][29], 3000)
        self.assertEqual(trace[-1]["next_pc"], trace[0]["registers"][31])

    def test_button_completion_recorded_when_timer_pending_at_reti(self):
        m = self.machine
        m.request(1)
        for _ in range(2000):
            word = m.get(m.engine.PC)
            if (m.active_button is not None and m.engine.intnum == 2
                    and not m.engine.intflag and m.memory.IRop(word) == 31
                    and m.memory.IRxop(word) == 27):
                break
            m.step(1)
        else:
            self.fail("Button ISR did not reach RETI")
        m.cpu.intrq[0] = 1
        m.step(1)
        self.assertIsNone(m.active_button)
        self.assertEqual(m.events[-1]["result"], 1)
        self.assertEqual(m.engine.intnum, 0)
        self.assertFalse(m.engine.intflag)


if __name__ == "__main__":
    unittest.main(verbosity=2)
