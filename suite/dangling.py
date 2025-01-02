def a():
    if False:
        if True:
            return False
        else:
            return False
    else:
        return True
    return False

if a():
    print("dangling: OK!")
else:
    print("dangling: FAIL!")
