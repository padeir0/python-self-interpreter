def max(a, b):
    if a >= b:
        return a
    else:
        return b

def test():
    if max(1, 2) != 2:
        return False
    elif max(-1, 5) != 5:
        return False
    elif max(0, 0) != 0:
        return False
    elif max(100, 1000) != 1000:
        return False
    return True

if test():
    print("max.py: OK!")
else:
    print("max.py: something went wrong!")
