def ord(r):
    if r == "0":
        return 0
    elif r == "1":
        return 1
    elif r == "2":
        return 2
    elif r == "3":
        return 3
    elif r == "4":
        return 4
    elif r == "5":
        return 5
    elif r == "6":
        return 6
    elif r == "7":
        return 7
    elif r == "8":
        return 8
    elif r == "9":
        return 9

def test():
    if ord("0") != 0:
        return False
    if ord("1") != 1:
        return False
    if ord("2") != 2:
        return False
    if ord("3") != 3:
        return False
    if ord("4") != 4:
        return False
    if ord("5") != 5:
        return False
    if ord("6") != 6:
        return False
    if ord("7") != 7:
        return False
    if ord("8") != 8:
        return False
    if ord("9") != 9:
        return False
    return True

if test():
    print("elif_chain: OK!")
else:
    print("elif_chain: FAIL!")
