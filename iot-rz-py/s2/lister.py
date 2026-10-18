# lister

def pass2():
    global fout, fin
    mode = '*'
    ip = 0
    for line in fin:
        tok = line.strip().split()
        if( len(tok) < 1):
            continue
        cmd = tok[0]
        if( cmd == ";"):         # comment line
            continue
        if( cmd == ".code"):
            mode = 'C'
            ip = int(tok[1])
            fout.write(line)
            continue
        elif( cmd == ".symbol"):
            mode = 'S'
            fout.write(line)
            continue
        elif( cmd == ".data"):
            mode = 'D'
            ip = int(tok[1])
            fout.write(line)
            continue
        elif( cmd[0] == ":" ):
             # dolabel
            fout.write(line)
            continue
        elif( cmd == ".end"):
            fout.write(line)
            break
        
        if( mode == "C"):
#            print("code:",tok)
            fout.write(str(ip) + " " + line)
            ip += 1
        elif( mode == "D"):
#            print("data:",tok)
            fout.write(str(ip) + " " + line)
            for x in tok:
                if( x == ';'):
                    break
                else:
                    ip += 1

  
def makename(name):
    i = name.index('.')
    return name[:i]
         
def main():
    global fin,fout
    
    fname = input("input:").strip()
    foname = makename(fname) + '.lis'
    fin = open(fname,"r")
    fout = open(foname,'w')
    pass2()
#    dumpsym()
    fout.close()
    fin.close()

main()