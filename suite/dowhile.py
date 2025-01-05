def test():
    i = 0

    do:
        i += 1
    while i < 10

    if i != 10:
        return False
    return True

if test():
    print("dowhile: OK!")
else:
    print("dowhile: FAIL!")
