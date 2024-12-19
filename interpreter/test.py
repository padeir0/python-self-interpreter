import lexkind
from lexer import Lexer
from parser import parse
from evaluator import evaluate

def test(str, result):
    n, err = parse(str, False)
    if err != None:
        print(err)
        return
    print(n)
    return evaluate(n) == result

def arith_tests():
    tests = [
        ("1+2", 3), ("3*5", 15), ("1+2*5", 11),
        ("1+10/2", 6), ("3*-5", -15), ("(5*5)/5", 5),
    ]
    
    for t in tests:
        ok = test(t[0], t[1])
        if ok:
            print(t[0], "OK!")
        else:
            print(t[0], "FAIL!")

def lexy():
    tests = [
        "def max(a, b):",
        "\"stringy\" is nice ok: (1 >= 2 == 3 += 4)"
    ]
    for s in tests:
        l = Lexer(s)
        for tk in l.all_tokens():
            print(tk)


if __name__ == "__main__":
    arith_tests()
    lexy()

