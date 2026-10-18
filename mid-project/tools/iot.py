# iot-board  devices
# iot.py
#                         1 Feb 2025

import cpu
import array
import math
import random

SINLEN = 1000       # sin period
SINAMP = 50.0       # sin amplitude
SINMUL = 2          # 10x period multiplier
DIGLEN = 1000       # dig period
DIGAMP = 5          # dig amplitude
DIGMUL = 1          # 2x period multiplier

timer0range = 100
timer1range = 250

sinbuf = array.array('l',[0]*SINLEN)     # sine wave buffer
digbuf = array.array('l',[0]*DIGLEN)     # digital wave buffer

def gensin():
    z = 0.0
    for i in range(0,SINLEN):
        x = math.sin(z)                    # in radian
        z += 0.00628318
        x *= SINAMP
        sinbuf[i] = int(x)

def showsin():
    for i in range(0,SINLEN):
        print(sinbuf[i]," ", end="")

def readsinport():
    idx = int(cpu.clock / SINMUL) % SINLEN
    x = sinbuf[idx]
    return x

def gendig():
    m = int(DIGLEN / 2)
    for i in range(0,m):
        digbuf[i] = DIGAMP
    for i in range(m,DIGLEN):
        digbuf[i] = 0

def readdigport():
    idx = int(cpu.clock / DIGMUL) % DIGLEN
    x = digbuf[idx]
    return x

def simdevices():
    cpu.timer0 += 1
    cpu.timer0 %= timer0range
    if( cpu.timer0 == 0 ):
        cpu.intrq[0] = 1
    cpu.timer1 += 1
    cpu.timer1 %= timer1range
    if( cpu.timer1 == 0 ):
        cpu.intrq[1] = 1

def settimer(i,k):
    global timer0range, timer1range
    if(i == 0):
        timer0range = k
    elif(i == 1):
        timer1range = k

def initIO():
    gensin()
    gendig()
    cpu.timer0 = 0
    cpu.timer1 = 0
    random.seed()     # use system time as seed

def readport(n):
    if(n == 10):
        return readsinport()
    elif(n == 11):
        return readdigport()
    elif(n == 12):
        return random.randint(0,2147483648)
    elif(n == 13):
        return cpu.clock
    else:
        print("error unknown port")
    return 0
