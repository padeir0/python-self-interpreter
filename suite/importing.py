import lib

def test():
    if lib.The_Object(3).value != 3:
        return False
    if lib.The_Object(None).value != None:
        return False
    if lib.square(2) != 4:
        return False
    if lib.square(0) != 0:
        return False
    if lib.PI_E42 != 314159265358979323846264338327950419716:
        return False
    return True

if test():
    print("importing: OK!")
else:
    print("importing: FAIL!")
