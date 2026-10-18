gv = 0

def double(x):
    a = x + x
    return a

def main():
    global gv
    gv = 10
    b = double(gv)
    print(b)

main()