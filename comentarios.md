# Expressões em multiplas linhas

Python permite que se escreva literais de listas, e outras coisas,
em multiplas linhas.

```python
tests = [
    ("1+2", 3), ("3*5", 15), ("1+2*5", 11),
    ("1+10/2", 6), ("3*~5", -15), ("(5*5)/5", 5),
]
```

Porém a sintaxe de Python é sensivel a espaços e novas linhas.
Para permitir literais e chamadas de função em multiplas linhas,
Python faz com que o Lexer pare de emitir tokens de nova-linha (NL)
dentro de delimitadores [1](https://docs.python.org/3/reference/lexical_analysis.html#:~:text=There%20is%20no%20NEWLINE%20token%20between%20implicit%20continuation%20lines.).
Isso é uma gambiarra. 

Na gramatica, é possível permitir que novas linhas sejam ignoradas
em certos contextos:

```ebnf
MultiLine_ExprList = Expr {CommaNL Expr} [CommaNL].
CommaNL = ',' [NL].
```

Nesse caso, sempre que houver uma virgula, uma nova-linha pode seguir e será ignorada.
Essa forma de resolver o problema é mais robusta, simples e mais formal, e é
um subconjunto próprio das strings aceitas pela gramática tradicional do Python.

# Linhas em branco

No interpretador usual de Python,
linhas em branco também não emitem tokens de nova-linha [2](https://docs.python.org/3/reference/lexical_analysis.html#:~:text=A%20logical%20line%20that%20contains%20only%20spaces%2C%20tabs%2C%20formfeeds%20and%20possibly%20a%20comment%2C%20is%20ignored%20(i.e.%2C%20no%20NEWLINE%20token%20is%20generated).),
isso é outra gambiarra. É possivel resolver isso
direto na gramática da linguagem:

```enbf
NL = nl {nl}.
nl = '\n'.
```

Leia-se: sempre que pular uma linha, podes pular outras linhas em seguida.
Em qualquer lugar que uma linha é possível (ou requerida) de ser colocada,
a gramática te permite colocar outras. Isso continua sendo um subconjunto
de Python original.

# Tabs

Por causa das complexidades de verificar as regras de identação quando
tabs estão envolvidas [3](https://docs.python.org/3/reference/lexical_analysis.html#:~:text=Indentation%20is%20rejected%20as%20inconsistent%20if%20a%20source%20file%20mixes%20tabs%20and%20spaces%20in%20a%20way%20that%20makes%20the%20meaning%20dependent%20on%20the%20worth%20of%20a%20tab%20in%20spaces),
elas são completamente proibidas no código fonte.

Se fosse permitido o uso de tabs sem levar em conta a identação própria,
a linguagem escolhida não seria um subconjunto de Python, pois alguns
programas seriam aceitos pelo auto-interpretador e negados pelo
interpretador padrão de Python.

# Sintaxe PEG original vs PEG extendida

A sintaxe padrão de Python é especificada usando uma gramática de PEG
normal, que não entende espaço semantico [4](https://docs.python.org/3/reference/lexical_analysis.html#:~:text=INDENT%20and%20DEDENT%20tokens).
Recentemente, alguns avanços na teoria de parsers dão idéias de como
extender a gramática PEG para lidar com identação.

No lexer de Python, isso também é feito usando uma gambiarra,
aqui, usamos o simbolo `>` na gramática para definir um nivel de
identação.

```ebnf
While = 'while' Expr ':' NL >Block.
```

Nesse caso, a produção `Block`, além das regras usuais,
compreende somente os tokens que estão no mesmo nivel de identação,
no parser, isso pode ser implementado simplesmente como:

```python
def block(parser):
    while (parser.same_identation()):
        # decision rules ...
```

# Retorno fora de função

Python gera um `SyntaxError` para retornos fora de funções,
isso pode ser resolvido com uma caminhada na arvore sintática,
após ela ser parseada. O importante é que o auto-interpretador
não execute nenhum código antes dessa verificação.

# Indentação correta

Não é necessário _exatamente_ 4 espaços para indentar código
em python [5](https://docs.python.org/3/reference/lexical_analysis.html#:~:text=correctly%20(though%20confusingly)%20indented).
Só é necessário que os statements em um bloco
sejam corretamente justificados (tenham a mesma indentação),
e que, quando ditado pela gramática, o primeiro statement
do bloco tenha uma indentação estritamente maior que a anterior.

# Tratamento de erros

Para tratar os erros no parser, existem varias opções.
Idealmente, em python, usariamos `Exception`, o que limparia
muito a implementação, entretanto, isso acarretaria na
necessidade de implementar `Exception`, que pode dar dor de
cabeça.

Ao invés disso, tomamos a estratégia de Go:

```python
def _while(parser):
    kw, err = parser.expect(lexkind.WHILE, "while keyword")
    if err != None:
        return None, err
```

Poderiamos, pela natureza dinamica de Python, retornar um único
valor, mas precisariamos implementar `type()` e `is`,
então deixaremos do jeito que está.

Se sobrar tempo, eu implemento uma das duas alternativas acima.

# Atribuições

O lado esquerdo de uma atribuição deve conter apenas expressões atribuíveis.
Nesse sentido, essa validação só pode ocorrer em tempo de runtime.
Para isso, uma função `get_target_object` pode olhar a expressão do lado
esquerdo e tentar achar o objeto, e ela mesmo retorna esse erro, caso ocorra.

A definição de uma **expressão atribuível** em _psy_ se dá pelo seguinte:
 - Se `<e>` é uma variável, mesmo que não declarada previamente, então `<e>` é atribuível (`a = 1`).
 - Sendo `<e>` uma expressão atribuível, uma expressão composta com indexação (`<e>[1] = 1`) é atribuivel
 - Sendo `<e>` uma expressão atribuível, uma expressão composta com acesso a uma _propriedade mutavel_ `<e>.prop = 1` é atribuível

Uma propriedade é **mutavel** se não é o nome de algum método.

Note que isso pode ser checado facilmente com um procedimento recursivo,
mesmo no caso que o lado esquerdo da atribuição tenha multiplas expressões.

# Ausência de `for` loops

Para implementar os `for` loops em python, é necessário o uso dos métodos `__iter__` e
`__next__`, e o segundo se comunica por meio de exceções. Por consequência, pro interpretador usar
os métodos `__next__` do próprio CPython, ele precisa de entender exceções
[6](https://docs.python.org/3/library/stdtypes.html#iterator.__iter__:~:text=If%20there%20are%20no%20further%20items%2C%20raise%20the%20StopIteration%20exception.)
, e elas não serão implementadas.

# String Escapes

É possivel escrever 3 tipos de escapes dentro de strings:
`\n`, `\"` e `\\`. Mas como o interpretador sabe o valor númerico ASCII
desses caras? Observe a implementação que traduz um escape pra um
caractere:

```
def _process_str(s):
    out = ""
    i = 0
    while i < len(s):
        r = s[i]
        if r == "\\":
            i += 1
            r = s[i]
            if r == "n":
                out += "\n"
            elif r == "\"":
                out += "\""
            elif r == "\\":
                out += "\\"
        else:
            out += r
        i += 1
    return out
```

Parece que `\"` é definido em termos dele mesmo! Mas isso não é verdade.
O que acontece é que o interpretador de CPython sabe o valor desses
escapes, porque C sabe o valor desses escapes. Acontece então o seguinte:

 - PSY-PSY interpreta um programa e lê `\n` de acordo com PSY
 - PSY interpreta o próprio código e define `\n` em termos de CPython
 - CPython interpreta `\n` e define em termos de C
 - C define o valor como `0xA`

# Ausência de Tuplas

Não temos tuplas em Spy por dois motivos: são redundantes e 
sua implementação não é inteiramente simples. Considere, por exemplo,
como poderiamos criar dinamicamente a tupla `(1, 2, 3)` através da lista `[1, 2, 3]`,
sem usar o construtor da classe?

Por isso, usamos listas ou objetos onde tuplas tomariam o lugar.

Com isso, também não implementamos multiplos retornos ou
detupling (sei la o nome disso em python).
