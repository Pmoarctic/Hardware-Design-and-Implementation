
# as21  assembler for S2   28 March 2020
# extend interrupt         30 Jan 2025

# type op ={1,2,3,4,5} label = 10
symtab = {                  # [type,value]
    'ld': [1,1],
    'st': [1,3],
    'mov': [5,5],
    'jmp': [5,6],
    'jal': [3,7],
    'jt': [3,8],
    'jf': [3,9],
    'add': [2,0],
    'sub': [2,1],
    'mul': [2,2],
    'div': [2,3],
    'and': [2,4],
    'or': [2,5],
    'xor': [2,6],
    'eq': [2,7],
    'ne': [2,8],
    'lt': [2,9],       
    'le': [2,10],
    'gt': [2,11],
    'ge': [2,12],
    'shl': [2,13],
    'shr': [2,14],
    'mod': [2,15],
    'ret': [5,19],
    'trap': [5,20],
    'push': [4,21],
    'pop': [4,22],
    'not': [4,23],
    'int': [6,24],
    'ei': [6,25],
    'di': [6,26],
    'reti': [7,27],
    'wfi': [7,28],
    'nop': [7,0]
    }

def isnumeric(w):
    flag = True
    for c in w:
        if( not c.isdigit()):
            flag = False
    return flag

def isreg(w):
    return w[0] == 'r' and int(w[1:])  in range(0,32)

def isimm(w):
    return w[0] == '#'

# read input file and recognise three sections
def pass1():
    global fin
    mode = '*'
    linenum = 0
    ip = 0
    for line in fin:
        linenum += 1
#        print(line,end="")
        tok = line.strip().split()
        if( len(tok) < 1):
            continue
        cmd = tok[0]
        if( cmd == ";"):         # comment line
            continue
        if( cmd == ".code"):
            mode = 'C'
            ip = int(tok[1])
            continue
        elif( cmd == ".symbol"):
            mode = 'S'
            continue
        elif( cmd == ".data"):
            mode = 'D'
            ip = int(tok[1])
            continue
        elif( cmd[0] == ":" ):    # collect label
            w = cmd[1:]
            if(w in symtab):
                print("error duplicate label")
            else:
                symtab[w] = [10,ip]
            continue
        elif( cmd == ".end"):
            break
        
        if( mode == "S"):           # collect symbol
            if( cmd in symtab):
                print("error redefine symbol")
            else:
                symtab[cmd] = [11,int(tok[1])]
        elif( mode == "C" ):
            ip += 1                  # count code
        elif( mode == "D"):
            for x in tok:
                if( x == ';'):       # comment
                    break
                ip += 1              # count data

def getR(w): 
    if(w in symtab):            # symbol
        v = symtab[w][1]
        if( v in range (0,32)):
            return v
    elif( isreg(w)):            # r0..r31
        return int(w[1:])

def getA(w):
    if( isnumeric(w)):
        return int(w)
    elif( w in symtab):              # search symtab 
        return symtab[w][1]

def str2(n):        # convert to string pad with blank
    return str(n) + " "

def outL(op,a1,a2):
    s = str2(op)+str2(a1)+str2(a2)
    fout.write('L '+ s + '\n')
    
def outD(op,a1,a2,d):
    s = str2(op)+str2(a1)+str2(a2)+str2(d)
    fout.write('D '+ s + '\n')
    
def outX(op,a1,a2,a3):
    s = str2(a1)+str2(a2)+str2(a3)+str2(op)
    fout.write('X 31 '+ s + '\n')
    
def dogroup1(op,tok):       # ld/st abs,idx,disp
    a2 = tok[2]
    if( a2[0]  == '+'):
        if( op == 1):        # ld, ldx
            outX(17,getR(tok[1]),getR(a2[1:]),getR(tok[3]))
        elif( op == 3):      # st, stx
            outX(18,getR(tok[1]),getR(a2[1:]),getR(tok[3]))
    elif( a2[0] == '@'):
        outD(op+1,getR(tok[1]),getR(tok[3]),getA(a2[1:]))
    else:
        outL(op,getR(tok[1]),getA(tok[2]))
    
def dogroup2(op,tok):       #  op r r r, op r r i, add/sub...
    if( isreg(tok[3])):
        outX(op,getR(tok[1]),getR(tok[2]),getR(tok[3]))
    elif( isimm(tok[3])):
        outD(op+10,getR(tok[1]),getR(tok[2]),getA(tok[3][1:]))
 
def dogroup3(op,tok):       # jt/jf/jal r ads
    outL(op,getR(tok[1]),getA(tok[2]))
    
def dogroup4(op,tok):       # op r1 r2, push/pop/not
    outX(op,getR(tok[1]),getR(tok[2]),0)

def dogroup5(ops,tok):      # op string, mov, jmp, trap, ret
    if( ops == 'mov'):
        if( isimm(tok[2])):
            outL(5,getR(tok[1]),getA(tok[2][1:]))
        else:
            outX(16,getR(tok[1]),getR(tok[2]),0)
    elif( ops == 'jmp'):
        outL(6,0,getA(tok[1]))
    elif( ops == 'trap'):
        outX(20,getR(tok[1]),getA(tok[2][1:]),0)
    elif( ops == 'ret'):
        outX(19,getR(tok[1]),0,0)
        
def dogroup6(op,tok):         # int #, ei #, di #
    if( isimm(tok[1])):
        outX(op,0,getA(tok[1][1:]),0)

def pass2():
    global fin
    mode = '*'
    linenum = 0
    for line in fin:
        linenum += 1
        print(linenum,line,end="")
        tok = line.strip().split()
        if( len(tok) < 1):
            continue
        cmd = tok[0]
        if( cmd == ";"):         # comment line
            continue
        if( cmd == ".code"):
            mode = 'C'
            fout.write('a '+ tok[1] + '\n')
            continue
        elif( cmd == ".symbol"):
            mode = 'S'
            continue
        elif( cmd == ".data"):
            mode = 'D'
            fout.write('a ' + tok[1] + '\n')
            continue
        elif( cmd[0] == ":" ):
             # dolabel
            continue
        elif( cmd == ".end"):
            break
        
        if( mode == "C"):
#            print("code:",tok)
            op = tok[0]
            optype = symtab[op][0]
            opcode = symtab[op][1]
            if( optype == 1):           # ld, st
                dogroup1(opcode,tok)
            elif( optype == 2):         # op 3r, op r r # 
                dogroup2(opcode,tok)
            elif( optype == 3):         # jt jf jal r ads
                dogroup3(opcode,tok)
            elif( optype == 4):         # push, pop, not r r
                dogroup4(opcode,tok)
            elif( optype == 5):         # mov, jmp, ret, trap
                dogroup5(op,tok)
            elif( optype == 6):         # int, ei, di #
                dogroup6(opcode,tok)
            elif( optype == 7):
                if( opcode == 0):       # nop
                    outL(opcode,0,0)
                else:
                    outX(opcode,0,0,0)  # reti, wfi
                
        elif( mode == "D"):
#            print("data:",tok)
            for x in tok:
                if( x == ';'):
                    break
                fout.write('w ' + x +'\n')
    fout.write('e\n')

def dumpsym():
    for key in symtab:
        v = symtab[key]
        if( v[0] == 10 or v[0] == 11):    # label, symbol
#            print(key,v)
            fout.write(key + ' ' + str(v[1]) +'\n')
  
def makename(name):
    i = name.index('.')
    return name[:i]
         
def main():
    global fin,fout
    
#    fname = input("input:").strip()
#    foname = makename(fname) + '.obj'
    fin = open(ffname,"r")
    pass1()
    fin.seek(0)    # rewind
    print("start pass 2")
    fout = open(foname,'w')
    pass2()
    dumpsym()
    fout.close()
    fin.close()

def fixobj():
    global fname,foname,ffname
    
    fname = input("input:").strip()
    foname = makename(fname) + '.obj'
    ffname = makename(fname) + '-f.txt'
    fin = open(fname,'r')
    fout = open(ffname,'w')
    cnt = 0
    for line in fin:
        cnt += 1
#        print(line,end='')
        tok = line.split()
#        print(cnt,tok)
        if( len(tok) < 1 ):
            continue
        if( tok[0] == 'swi' ):
            fout.write('wfi\n')
        else:
            fout.write(line)
    fout.close()
    fin.close()

fixobj()
main()


