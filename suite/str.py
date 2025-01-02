def test():
    if "" != "":
        return False
    if "a" != "abcd"[0]:
        return False
    if "\"" != "\"":
        return False
    if "\\" != "\\":
        return False
    return True

if test():
    print("str: OK!")
else:
    print("str: FAIL!")
