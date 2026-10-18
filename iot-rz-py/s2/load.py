
# sim21 loader  rewrite from C, 25 March 2020
# version 1.0
# update       10 Feb 2025

#import array 

MAXMEM = 20000
ip = 0

# M = array.array('L',[0]*MAXMEM)     # memory size MAXMEM
M = [0] * MAXMEM            # memory

def setM(ads,v):
    M[ads] = v

def getM(ads):
    return M[ads]

def signx(x):       # sign bit 16 extend
    if( x & 0x010000 ):
        return (x | 0xFFFE0000)
    return x

def IRop(x):
    return (x & 0xF8000000) >> 27
def IRr1(x):
    return (x & 0x07C00000) >> 22
def IRr2(x):
    return (x & 0x003E0000) >> 17
def IRr3(x):
    return (x & 0x0001F000) >> 12
def IRads(x):
    return (x & 0x003FFFFF)
def IRdisp(x):
    return signx(x & 0x0001FFFF)
def IRxop(x):
    return (x & 0x00000FFF)

def loadprogram(fname):
    global ip
    f = open(fname,"r")
    fx = f.readlines()
    ip = 0
    for line in fx:
        lx = line.split()
        op = lx[0]
        arg = [int(i) for i in lx[1:]]   # convert to int
        if ( op == 'a'):
            ip = arg[0]
        elif( op == 'L'):
            M[ip] = (arg[0]<<27) | (arg[1]<<22) | (arg[2]&0x3FFFFF)
            ip += 1
        elif( op == 'D'):
            M[ip] = (arg[0]<<27) | (arg[1]<<22) | (arg[2]<<17) | (arg[3]&0x1FFFF)
            ip += 1
        elif( op == 'X'):
            M[ip] = (arg[0]<<27) | (arg[1]<<22) | (arg[2]<<17) | (arg[3]<<12) | (arg[4]&0x0FFF)
            ip += 1
        elif( op == 'w'):
            M[ip] = arg[0]
            ip += 1
        elif( op == 'e'):
            break
        else:
            print("error",lx)
    f.close()
    print("load program, last address ",ip)
 
# opcode strings indexed by opcode (with xop has +10 offset)
    
opstr = ["nop","ld","ld","st","st","mov","jmp","jal","jt","jf",
         "add","sub","mul","div","and","or","xor",
         "eq","ne","lt","le","gt","ge","shl","shr","mod",
         "mov","ld","st","ret","trap","push","pop","not",
         "int","ei","di","reti","wfi","?"]

def printop(x):
    if( x in range(0,39)):
        print(opstr[x],end="")

def disassemble(x):
    op = IRop(x)
    if( op in range(0,10) ):
        printop(op)
        if( op == 0 ):                  # nop
            print()
        if( op in [1,3]):               # ld/st ads
            print(" r",IRr1(x)," ",IRads(x),sep="")
        elif( op in [2,4] ):            # ld/st disp
            print(" r",IRr1(x)," @",IRdisp(x)," r",IRr2(x),sep="")
        elif( op == 5 ):                # mov im
            print(" r",IRr1(x)," #",IRads(x),sep="")
        elif( op == 6 ):                # jmp ads
            print(" ",IRads(x),sep="")
        elif( op in [7,8,9]):           # jal/jt/jf 
            print(" r",IRr1(x)," ",IRads(x),sep="")
    elif( op in range(10,26)):          # op r1 r2 im
        printop(op)
        print(" r",IRr1(x)," r",IRr2(x)," #",IRdisp(x),sep="")
    elif( op == 31 ):                   # xop
        xop = IRxop(x)
        printop(xop+10)
        if( xop in range(0,16)):        # op r1 r2 r3
            print(" r",IRr1(x)," r",IRr2(x)," r",IRr3(x),sep="")
        elif( xop in [16,21,22,23]):    # op r1 r2
            print(" r",IRr1(x)," r",IRr2(x),sep="")
        elif( xop in [17,18]):          # ld/st index
            print(" r",IRr1(x)," +r",IRr2(x)," r",IRr3(x),sep="")
        elif( xop == 19 ):              # ret
            print(" r",IRr1(x),sep="")
        elif( xop == 20 ):              # trap r1 n
            print(" r",IRr1(x)," #",IRr2(x),sep="")
        elif( xop in [24,25,26]):       # int/ei/di n
            print(" #",IRr2(x),sep="")
        elif( xop in [27,28]):          # reti/wfi
            print(" ")
        else:
            print("opcode undefined")
    else:
        print("opcode undefined")
    
    
def dodisassem():
    for i in range(0,ip):
        disassemble( M[i] )
        

