def test():
    if str(1) != "1":
        return False
    if str(0) != "0":
        return False
    if str(123456) != "123456":
        return False
    if str([1, 2, 3]) != "[1, 2, 3]":
        return False
    if str({"a":1, "b":2, "c":3}) != "{\"a\": 1, \"b\": 2, \"c\": 3}":
        return False
    if str(None) != "None":
        return False
    return True

if test():
    print("builtin_str: OK!")
else:
    print("builtin_str: FAIL!")
