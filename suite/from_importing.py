from lib import The_Object, square, PI_E42

def test():
    if The_Object(3).value != 3:
        return False
    if The_Object(None).value != None:
        return False
    if square(2) != 4:
        return False
    if square(0) != 0:
        return False
    if PI_E42 != 314159265358979323846264338327950419716:
        return False
    return True

if test():
    print("from_importing: OK!")
else:
    print("from_importing: FAIL!")
