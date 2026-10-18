# sim

import mem
import setmem as sm

def main():
    for i in mem.MEM:
        print(i)
    
    sm.setmem(1,22)
    print(mem.MEM)
    
main()
