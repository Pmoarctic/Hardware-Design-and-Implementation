# s21  simulator rewrite from C,             25 Mar 2020
# extend interrupt                            1 Feb 2025
#  for mos task-switching, reti also ei #0    10 Feb 2025

#import array
import cpu
import load as ld
import iot

#from cpu import clock as clock

INTVEC = 1000                     # address of int vectors

intnum = 0
intflag = 0                        # interrupt state
cpuflag = 1
display = 0                        # turn on trace display

#import iot as io                  # iot-board devices

from load import getM as getM     # getting and setting memory
from load import setM as setM

#R = array.array('l',[0]*32)       # registers
R = [0] * 32                      # registers

PC = 0
savePC = 0
ninst = 0                         # number of executed inst
runflag = 1
MAXRUN = 4000                     # max simulation run
heap = 10000                      # start of heap mem

def signx2(x):          # sign x 22 bits
    if( x & 0x0200000 ):
        return x | 0xFFC00000
    return x

def setR(r1,d):
    R[r1] = int(d)

def setIntmask(n,i):
    cpu.intmask[n] = i

def dojump(cond,ads):
    global PC
    if( cond != 0 ):
        PC = ads
    
def docall(r1,ads):
    global PC
    R[r1] = PC
    PC = ads

def dopush(r1,r2):
    R[r1] += 1
    setM(R[r1], R[r2])
    
def dopop(r1,r2):
    R[r2] = getM(R[r1])
    R[r1] -= 1

def doreti():
    global PC, intflag, intmask
    PC = R[31]
    intflag = 1
    cpu.intmask[0] = 1   # for mos-rz2 task-switching
    
def dowfi():
    global cpuflag, intflag
    cpuflag = 0
    intflag = 1
    print("#")

def malloc(k):
    global heap
#    print("heap",heap)
    m = heap
    if( heap + k > ld.MAXMEM ):
        print("error out of memory")
    else:
        heap += k
    return m
    
def trap(r1,n):
    global runflag, heap
    
    if( n == 0 ):
        runflag = 0
        print("stop execute",ninst,"instructions")        
    elif( n == 1 ):
        print(R[r1],"",end="")
    elif( n == 2 ):
        print(chr(R[r1]),end="")
    elif( n == 3 ):               # print string
        ads = R[r1]
        c = getM(ads)
        while( c != 0 ):
            print(chr(c),end="")
            ads += 1
            c = getM(ads)
    elif( n == 4 ):               # input
        x = input()
        m = len(x)
        ads = malloc(m+1)
        for i in range(0,m):
            setM(ads+i,ord(x[i]))
        setM(ads+m,0)             # end of string
        R[28] = ads               # return ads to string
        
    elif( n == 13 ):              # settimer0
        iot.settimer(0,R[r1])
    elif( n == 14 ):              # settimer1
        iot.settimer(1,R[r1])
    elif( n == 15 ):              # pushm r1
        for i in range(0,16):     #   push r0..r15 to sp
            R[r1] += 1
            setM(R[r1],R[i])
    elif( n == 16 ):              # popm r1, r15..r0 from sp
        for i in range(15,-1,-1):
            R[i] = getM(R[r1])
            R[r1] -= 1
    elif( n == 18 ):
        R[28] = iot.readport(R[r1]) # return value in retval
    elif( n == 19 ):                # alloc
        R[28] = malloc(R[r1])


def doxop(op,r1,r2,r3):
    switcher = {
        0: lambda: setR(r1, R[r2] + R[r3]),         # add
        1: lambda: setR(r1, R[r2] - R[r3]),         # sub
        2: lambda: setR(r1, R[r2] * R[r3]),         # mul
        3: lambda: setR(r1, R[r2] / R[r3]),         # div
        4: lambda: setR(r1, R[r2] & R[r3]),         # and
        5: lambda: setR(r1, R[r2] | R[r3]),         # or
        6: lambda: setR(r1, R[r2] ^ R[r3]),         # xor
        7: lambda: setR(r1, R[r2] == R[r3]),        # eq
        8: lambda: setR(r1, R[r2] != R[r3]),        # ne
        9: lambda: setR(r1, R[r2] <  R[r3]),        # lt
        10: lambda: setR(r1, R[r2] <= R[r3]),       # le
        11: lambda: setR(r1, R[r2] >  R[r3]),       # gt
        12: lambda: setR(r1, R[r2] >= R[r3]),       # ge
        13: lambda: setR(r1, R[r2] << R[r3]),       # shl
        14: lambda: setR(r1, R[r2] >> R[r3]),       # shr
        15: lambda: setR(r1, R[r2] %  R[r3]),       # mod
        16: lambda: setR(r1, R[r2]),                # mov
        17: lambda: setR(r1, getM(R[r2]+R[r3])),    # ldx
        18: lambda: setM(R[r2]+R[r3], R[r1]),       # stx
        19: lambda: dojump(1, R[r1]),               # ret
        20: lambda: trap(r1, r2),                   # trap
        21: lambda: dopush(r1, r2),                 # push
        22: lambda: dopop(r1, r2),                  # pop
        23: lambda: setR(r1, R[r2] == 0),           # not
        # extension interrupt
        24: lambda: interrupt(r2),           # int
        25: lambda: setIntmask(r2,1),        # ei
        26: lambda: setIntmask(r2,0),        # di
        27: lambda: doreti(),                # reti
        28: lambda: dowfi()                  # wfi
    }
    doxop = switcher.get(op, lambda: print("undefined op"))
    doxop()
    
def run():
    global PC, ninst,savePC
    
    savePC = PC
    IR = getM(PC)
    PC += 1
    ads = ld.IRads(IR)      # signx 17 bits
    d = ld.IRdisp(IR)
    r1 = ld.IRr1(IR)
    r2 = ld.IRr2(IR)
    r3 = ld.IRr3(IR)
    ninst += 1
    op = ld.IRop(IR)
    if( op == 31 ):
        doxop(ld.IRxop(IR),r1,r2,r3)
    else:
        switcher = {
            0: lambda: 0,                           # nop
            1: lambda: setR(r1, getM(ads)),         # ld ads
            2: lambda: setR(r1, getM(R[r2]+d)),     # ldd
            3: lambda: setM(ads, R[r1]),            # st ads
            4: lambda: setM(R[r2]+d, R[r1]),        # std
            5: lambda: setR(r1, signx2(ads)),       # mvi
            6: lambda: dojump(1,ads),               # jmp
            7: lambda: docall(r1,ads),              # jal
            8: lambda: dojump(R[r1] != 0,ads),      # jt
            9: lambda: dojump(R[r1] == 0,ads),      # jf
            10: lambda: setR(r1, R[r2] + d),        # addi
            11: lambda: setR(r1, R[r2] - d),        # subi
            12: lambda: setR(r1, R[r2] * d),        # muli
            13: lambda: setR(r1, R[r2] / d),        # divi
            14: lambda: setR(r1, R[r2] & d),        # andi
            15: lambda: setR(r1, R[r2] | d),        # ori
            16: lambda: setR(r1, R[r2] ^ d),        # xori
            17: lambda: setR(r1, R[r2] == d),       # eqi
            18: lambda: setR(r1, R[r2] != d),       # nei
            19: lambda: setR(r1, R[r2] <  d),       # lti
            20: lambda: setR(r1, R[r2] <= d),       # lei
            21: lambda: setR(r1, R[r2] >  d),       # gti
            22: lambda: setR(r1, R[r2] >= d),       # gei
            23: lambda: setR(r1, R[r2] << d),       # shli
            24: lambda: setR(r1, R[r2] >> d),       # shri
            25: lambda: setR(r1, R[r2] %  d),       # modi
        }
        doop = switcher.get(op, lambda: print("undefined op"))
        doop()

def interrupt(n):
    global PC, intnum, cpuflag, intflag
    
    if( n > 3 ):
        print("error unknown interrupt")
    print("<int",n,">")
    intnum = n
    R[31] = PC         # save PC
    PC = getM(INTVEC+n)
    cpuflag = 1        # wake up sleepy cpu
    intflag = 0        # master disable interrupt
    cpu.intrq[n] = 0   # clear int request

def checkinterrupt():
    if( intflag ):
        if ( cpu.intmask[0] and cpu.intrq[0] ):
            interrupt(0)
        elif( cpu.intmask[1] and cpu.intrq[1] ):
            interrupt(1)
        elif( cpu.intmask[2] and cpu.intrq[2] ):
            interrupt(2)
        elif( cpu.intmask[3] and cpu.intrq[3] ):
            interrupt(3)

def runoneclock():
    global clock
    
    cpu.clock += 1
    iot.simdevices()
    if( runflag and cpuflag):
        run()
        if( display ):
            show()
    checkinterrupt()

def show():  
    print("PC",savePC," ",end="")
    ld.disassemble(getM(savePC))
    print("  ",end="")
    for i in range(0,9):
        print(" r",i,":",R[i]," ",sep="",end="")
    print("\n  ",end="")
    for i in range(24,32):
        print(" r",i,":",R[i]," ",sep="",end="")
    print()
    print("clock",cpu.clock,end='')
    print(" cpuflag",cpuflag,"intflag",intflag,"timer0",cpu.timer0)

    
def main():
    global PC, savePC, ninst, runflag, clock
    
    iot.initIO()
    cpu.clock = 0
    PC = 0
    savePC = 0
    ninst = 0                         # number of executed inst
    runflag = 1
    inp = input("object file:").strip().split()
    fname = inp[0]
    ld.loadprogram(fname)
#    ld.dodisassem()    
    interp()

# -------------- monitor -----------------

# mon (monitor) rewrite from C, 26 March 2020

brkp = 10000         # initial breakpoint is far

def help():
    print("g - go")
    print("t - single step")
    print("d ads n - dump memory") 
    print("r - show registers")
    print("s [rn,mn,pc] v - set [reg,mem,pc]")
    print("b ads - set breakpoint")
    print("c - clear breakpoint")
#    print("x - xray (debug)")
    print("h - this help")
    print("q - quit")

def dumpreg():
    for i in range(0,32):
        if( i%8 == 0):
            print()
        print("  r",i,":",R[i],sep="",end="")

def dumpmem(cmd):
    if( len(cmd) > 2 ):    # protect bad arguments
        ads = int(cmd[1])
        n = int(cmd[2])
        k = 0
        print(ads,":",end="")
        for i in range(ads, ads+n):
            print(getM(i)," ",end="")
            k += 1
            if( k%10 == 0 ):
                print("\n",i+1,":",end="")
    
regname = ['r0','r1','r2','r3','r4','r5','r6','r7','r8','r9',
           'r10','r11','r12','r13','r14','r15','r16','r17','r18',
           'r19','r20','r21','r22','r23','r24','r25','r26','r27',
           'r28','r29','r30','r31']

def setvalue(cmd):
    global PC

    if( len(cmd) > 2 ):    # protect bad arguments
        a = cmd[1]
        v = int(cmd[2])
        if( a in regname ):
            i = int(a[1:])
            R[i] = v
        elif( a[0] == 'm' ):
            setM(int(a[1:]),v)
        elif( a == "pc" ):
            PC = v
        else:
            print("set unknown")

def trace():
    global runflag
    
    while( (PC != brkp) and runflag ):
        if( cpu.clock > MAXRUN ):
            print("infinite loop")
            runflag = 0
        else:
            runoneclock()

# --- spying into data structure -----

def getacell(ads):
    a = getM(ads)
    b = getM(ads+1)
    return (a,b)

def printprocesslist(pl):
    for p in pl:      # print PCB
        ads = getM(p)
        spp = getM(p+1)
        fpp = getM(p+2)
        stp = getM(p+3)
        print("pcb ",p,":",ads,spp,fpp,stp)
  
# print cir list, collect process list
def printcircularlist(head):
    t = getacell(head)
    print(t,end="")
    pl = [t[0]]        # list of process
    i = 0
    while( t[1] != head and i < 10 ):     # prevent inf loop
        t = getacell(t[1])   # next cell
        pl.append(t[0])      # add to pl
        i += 1
        print(t," ",end="")
    print()
    return pl          # return process list

def printprocessqueue(ads):
    if( ads != 0 ):
        t = getacell(getM(ads))
        (qhead,qend) = t
        print("queue ",t)
        pl = printcircularlist(qhead)
        printprocesslist(pl)
        
def printsem(ads):
    sem = getM(ads)
    v = getM(sem)
    w = getM(sem+1)
    print("sem ",ads,":",v,w)
    printprocessqueue(sem+1)
    
# ------------------------------

def spy():
    printprocessqueue(1100)            # Q at 1100
    printsem(1105)
  
def interp():
    global display, brkp  # breakpoint
    
    while(1):
        cmd = input(">>").split()
 #       print(cmd)
        c = cmd[0]
        if( c == 'g'):
            trace()
        elif( c == 't'):
            display = 1
            runoneclock()
            display = 0
        elif( c == 'r'):
            dumpreg()
            print()
        elif( c == 'd'):
            dumpmem(cmd)
            print()
        elif( c == 's'):
            setvalue(cmd)
        elif( c == 'b'):
            if( len(cmd) > 0):
                brkp = int(cmd[1])
                print("breakpoint at",brkp)
        elif( c == 'c'):      # clear brkp (to very far)
            brkp = 10000

        elif( c == 'h'):
            help()
#         elif( c == 'x'):
#             spy()
        elif( c == 'q'):
            break
        else:
            print("unknown command")

# --------------------------------

main()


