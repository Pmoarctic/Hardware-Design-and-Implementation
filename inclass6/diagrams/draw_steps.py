from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
FONT = Path('C:/Windows/Fonts')
BG = '#FFFFFF'
INK = '#17212B'
MUTED = '#465565'
LINE = '#687887'
BLUE = '#EAF2FA'
GREEN = '#EAF5EC'
ORANGE = '#FFF0E0'

def font(size, bold=False, mono=False):
    name = ('consolab.ttf' if bold else 'consola.ttf') if mono else ('arialbd.ttf' if bold else 'arial.ttf')
    return ImageFont.truetype(str(FONT / name), size)

STEPS = [
    dict(n=1, title='Writer produces 1, then waits',
         desc='The reader has not consumed 1, so the writer blocks on its next wait(empty).',
         value=1, clock=852, qq=10292, current=10148,
         reader=[461,10034,10082,0,0,1], writer=[344,10180,10239,341,10322,0],
         full=1, empty=-1, waiter='Writer', next='READER'),
    dict(n=2, title='Reader prints +1, then waits',
         desc='The reader wakes the writer, then blocks on its next wait(full).',
         value=1, clock=1327, qq=10146, current=10002,
         reader=[343,10034,10092,341,10322,0], writer=[344,10180,10239,341,10322,1],
         full=-1, empty=0, waiter='Reader', next='WRITER'),
    dict(n=3, title='Writer produces 2, then waits',
         desc='The writer wakes the reader, then blocks on its next wait(empty).',
         value=2, clock=1688, qq=10292, current=10148,
         reader=[343,10034,10092,341,10322,1], writer=[343,10180,10239,341,10322,0],
         full=0, empty=-1, waiter='Writer', next='READER'),
    dict(n=4, title='Reader prints +2, then waits',
         desc='The reader wakes the writer, then blocks on its next wait(full).',
         value=2, clock=2139, qq=10146, current=10002,
         reader=[343,10034,10092,341,10322,0], writer=[343,10180,10239,341,10322,1],
         full=-1, empty=0, waiter='Reader', next='WRITER'),
]

def render(s):
    im = Image.new('RGB', (1600, 1660), BG)
    d = ImageDraw.Draw(im)

    def text(x, y, value, size=30, bold=False, color=INK, mono=False):
        d.text((x,y), str(value), fill=color, font=font(size,bold,mono))

    def center(x, y, value, size=30, bold=False, color=INK):
        f=font(size,bold)
        width=d.textlength(value,font=f)
        d.text((x-width/2,y),value,fill=color,font=f)

    def arrow(points, fill=LINE, width=4):
        d.line(points, fill=fill, width=width, joint='curve')
        a,b=points[-2:]
        angle=math.atan2(b[1]-a[1], b[0]-a[0])
        l=17
        d.polygon([b, (b[0]-l*math.cos(angle-.45),b[1]-l*math.sin(angle-.45)),
                   (b[0]-l*math.cos(angle+.45),b[1]-l*math.sin(angle+.45))],fill=fill)

    text(70,45,f"STEP {s['n']}",26,True,color=MUTED)
    text(70,88,s['title'],48,True)
    text(70,155,s['desc'],29,color=MUTED)
    d.line((70,210,1530,210),fill='#CED6DE',width=2)
    text(70,233,f"shareVar = {s['value']}     nump = 1",32,True,mono=True)
    text(1040,239,f"Snapshot clock: {s['clock']}",27,color=MUTED)

    center(800,293,'PROCESS QUEUE: the two nodes remain linked in a circle',29,True)
    center(800,340,'Q = 10000    |    Header: head = 10146, tail = 10292',29)

    arrow([(1195,450),(1195,409),(405,409),(405,450)])
    center(800,379,'Writer next = 10146',24,color=MUTED)
    for x, name, addr, pcb, nxt in [(100,'READER',10146,10002,10292),(890,'WRITER',10292,10148,10146)]:
        d.rounded_rectangle((x,450,x+610,602),radius=12,fill=BLUE,outline=LINE,width=2)
        text(x+25,469,f'{name} NODE @{addr}',32,True)
        text(x+25,521,f'PCB pointer = {pcb}',30,mono=True)
        text(x+25,560,f'next        = {nxt}',30,mono=True)
    arrow([(710,528),(890,528)])
    center(800,487,'next',24,color=MUTED)
    arrow([(405,602),(405,668)])
    arrow([(1195,602),(1195,668)])
    center(405,621,'points to PCB',25,color=MUTED)
    center(1195,621,'points to PCB',25,color=MUTED)

    labels=['Saved PC','Saved SP','Saved FP','Return address','Return value','State']
    for x, name, addr, vals in [(100,'READER',10002,s['reader']),(890,'WRITER',10148,s['writer'])]:
        state=vals[-1]
        status='READY' if state else ('BLOCKED on full' if name=='READER' else 'BLOCKED on empty')
        fill=GREEN if state else ORANGE
        d.rounded_rectangle((x,668,x+610,1110),radius=12,fill=BG,outline=LINE,width=2)
        d.rectangle((x+2,682,x+608,750),fill=fill)
        text(x+25,693,f'{name} PCB @{addr}',32,True)
        for i,(lab,v) in enumerate(zip(labels,vals)):
            text(x+28,774+i*44,lab,30)
            vstr=str(v)
            vw=d.textlength(vstr,font=font(31,mono=True))
            text(x+578-vw,774+i*44,vstr,31,mono=True,bold=False)
        center(x+305,1051,status,31,True)

    outgoing='Writer' if s['current']==10148 else 'Reader'
    text(100,1140,f"qq = {s['qq']}  ->  {outgoing} node",29,mono=True)
    text(100,1184,f"currentp = {s['current']}  ->  outgoing {outgoing} PCB",29,mono=True)

    text(100,1252,'SEMAPHORES',29,True)
    text(525,1252,'VALUE',26,True)
    text(850,1252,'WAITING PROCESS',26,True)
    d.line((100,1295,1500,1295),fill='#CED6DE',width=2)
    for i,(name,val,wait) in enumerate([
        ('full',s['full'],'Reader PCB @10002' if s['waiter']=='Reader' else 'None'),
        ('empty',s['empty'],'Writer PCB @10148' if s['waiter']=='Writer' else 'None'),
        ('mutex',1,'None')]):
        y=1313+i*49
        text(100,y,name,30,mono=True)
        text(550,y,val,30,mono=True)
        text(850,y,wait,30)

    d.line((70,1480,1530,1480),fill='#CED6DE',width=2)
    text(70,1501,f"Next runnable process: {s['next']}",32,True)
    text(70,1554,'Paused at PC = 250, before the scheduler changes currentp.',27,color=MUTED)
    text(70,1595,'PCB state: 1 = runnable; 0 = blocked here. All values are decimal.',26,color=MUTED)
    out=OUT/f"step-{s['n']}.png"
    im.save(out, dpi=(180,180))
    return im

if __name__ == '__main__':
    images=[render(s) for s in STEPS]
    preview=Image.new('RGB',(1000,1038),BG)
    for i,im in enumerate(images):
        preview.paste(im.resize((500,519)),((i%2)*500,(i//2)*519))
    preview.save(OUT/'preview.png')
    print('\n'.join(str(OUT/f'step-{s["n"]}.png') for s in STEPS))
