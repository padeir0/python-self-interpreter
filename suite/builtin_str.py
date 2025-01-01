def test():
    if str(1) != "1":
        return False
    if str(0) != "0":
        return False
    if str(123456) != "123456":
        return False
    return True

if test():
    print("builtin_str: OK!")
else:
    print("builtin_str: FAIL!")
