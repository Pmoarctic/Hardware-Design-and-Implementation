#  queue

Q = []
endQ = 0
freeQ = 2
freelist = 0

def makeQ():
    global endQ
    for i in range(0,20):
        Q.append(0)
    endQ = 18

def make3p():
    p = 2
    for i in range(0,3):
        Q[p+1] = p + 2
        p += 2
    Q[p+1] = 2     # circular
    
def make4p():
    now = getnode()
    s = now
    for i in range(0,3):
        nx = getnode()
        Q[now+1] = nx
        now = nx
    Q[now+1] = s    # circular
    return s

def printQ(p):
    s = p
    while( Q[p+1] != s ):
        print(p,':',Q[p],Q[p+1])
        p = Q[p+1]
    print(p,':',Q[p],Q[p+1])

def deletep(p):
    now = p
    nx = Q[p+1]
    while nx != now:
        p = nx
        nx = Q[p+1]
    nx = Q[now+1]
    Q[p+1] = nx
    freep(now)
    return nx

def getnode():
    global freelist, freeQ, endQ
    if( freelist == 0 ):
        m = freeQ
        freeQ += 2
        if( freeQ > endQ ):
            print("error out of Q memory")
    else:
        m = freelist
        freelist = Q[freelist+1]
    return m
        
def freep(p):
    global freelist
    Q[p+1] = freelist
    freelist = p

def printfree():
    p = freelist
    while( p != 0 ):
        print(p,'#',Q[p],Q[p+1])
        p = Q[p+1]

def appendQ(p,x):
    m = p
    nx = Q[p+1]
    while nx != m:
        p = nx
        nx = Q[p+1]
    # end Q is at p
    w = getnode()
    Q[w] = x
    Q[w+1] = m     # circular
    Q[p+1] = w     # append

makeQ()

p = make4p()
printQ(p)
print(Q)
print(p)
m = deletep(p)
print(Q)
#printQ(m)
printfree()
m = deletep(6)
printQ(m)
print(Q)
printfree()
appendQ(m,11)
printQ(m)
print(Q)
printfree()
appendQ(m,22)
printQ(m)
printfree()
appendQ(m,33)
printQ(m)
print(freeQ,endQ)
print(Q)





