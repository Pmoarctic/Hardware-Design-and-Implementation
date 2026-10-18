"""Refresh the standalone Thai HTML guide with traces from the real CPU engine."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re

from simulator import Machine


def build():
    cases = [
        ("Start · เริ่มจับเวลา", 1, 0, "เริ่มจากสถานะหยุด: Assembly เปลี่ยน running จาก 0 เป็น 1"),
        ("Lap 1 · บันทึกรอบแรก", 2, 320_000, "หลังจำลองเวลาประมาณ 3.20 วินาที: เก็บเวลาสะสมและระยะรอบแรก"),
        ("Lap 2 · คำนวณผลต่าง", 2, 465_000, "หลังจำลองเวลาเพิ่มประมาณ 4.65 วินาที: ดู sub r4 r1 r3 คำนวณระยะรอบ"),
        ("Pause · หยุดชั่วคราว", 1, 0, "คำสั่ง 1 เหมือน Start แต่ running เดิมเป็น 1 จึงเปลี่ยนเป็น 0"),
        ("Resume · ทำงานต่อ", 1, 200_000, "ผ่านช่วงหยุดจำลอง 2 วินาที: elapsed ไม่เพิ่ม แล้วคำสั่ง 1 เปลี่ยน running กลับเป็น 1"),
        ("Reset · ล้างเวลาและรอบ", 3, 100_000, "หลังทำงานต่อประมาณ 1 วินาที: หยุดจับเวลาและล้าง RAM ของเวลาและรอบทั้งหมด"),
        ("Lap ขณะหยุด · ปฏิเสธคำสั่ง", 2, 0, "ยังเกิด Interrupt แต่ result = 5 เพราะ running เป็น 0"),
    ]
    traces = []
    with redirect_stdout(io.StringIO()):
        machine = Machine(trace_registers=True)
        for label, command, cycles, note in cases:
            machine.step(cycles)
            machine.register_trace.clear()
            machine.request(command)
            for _ in range(2000):
                machine.step(1)
                if machine.active_button is None and not machine.queue:
                    break
            else:
                raise RuntimeError("Button ISR failed to return")
            steps = list(machine.register_trace)
            assert steps[0]["instruction"] == "ENTER INT2"
            assert steps[-1]["instruction"] == "reti"
            assert steps[-1]["registers"][:16] == steps[0]["registers"][:16]
            assert steps[-1]["registers"][29] == 3000
            traces.append({"label": label, "note": note, "steps": steps})
    target = Path(__file__).with_name("explanation-th.html")
    html = target.read_text(encoding="utf-8")
    data = json.dumps(traces, ensure_ascii=False, separators=(",", ":"))
    html, count = re.subn(r'(<script id="trace-data" type="application/json">).*?(</script>)',
                         lambda match: match[1] + data + match[2], html, flags=re.S)
    assert count == 1
    target.write_text(html, encoding="utf-8")
    print(f"Updated {target.name}: {len(traces)} scenarios, {sum(len(t['steps']) for t in traces)} CPU steps.")


if __name__ == "__main__":
    build()
