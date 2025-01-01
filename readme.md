# Auto-interpretador de Python

Objetivo: Interpretador de um subconjunto de
Python escrito em Python capaz de interpretar
o próprio código.

## Linguagem

O subconjunto de Python em questão é o descrito
pela gramatica PEG extendida a seguir. Que tal
subconjunto seja nomeado _spy_, vindo de **S**ubset of **Py**thon.

```ebnf
WhiteSpace: ' ' | '\r' | Comment.
Comment: '#' {ascii} nl.
nl: '\n'.

Module: Block.
Block: { =Statement NL }.
NL: nl {nl}.

Statement: While  | If    | Atrib_Expr
          | Return | Class | Func
          | Import | FromImport | Pass.

Pass: 'pass'.

Import: 'import' IdList.
FromImport: 'from' id 'import' IdList.
IdList: id {',' id} [','].

While: 'while' Expr ':' NL >Block.

If: 'if' Expr ':' NL >Block {Elif} [Else].
Elif: 'elif' Expr ':' NL >Block.
Else: 'else' ':' NL >Block.

Atrib_Expr: Expr [Assign_Op Expr].

Return: 'return' Expr.

Class: 'class' id ':' NL >Methods.
Methods: {=Func}.

Func: 'def' id Arguments ':' NL >Block.
Arguments: '(' [NL] [ArgList] ')'.
ArgList: Arg {CommaNL Arg} [CommaNL].
Arg: 'self' | id.

MultiLine_ExprList: Expr {CommaNL Expr} [CommaNL].
CommaNL: ',' [NL].

ExprList: Expr {',' Expr} [','].
Expr: And {'or' And}.
And: Comp {'and' Comp}.
Comp: Sum {compOp Sum}.
compOp: '==' | '!=' | '>' | '>=' | '<' | '<=' | 'in'.
Sum: Mult {sumOp Mult}.
sumOp: '+' | '-'.
Mult: UnaryPrefix {multOp UnaryPrefix}.
multOp: '*' | '/' | '%'.
UnaryPrefix: {Prefix} UnarySuffix.
UnarySuffix: Term {Suffix}.
Term: 'self' | 'None' | bool | num
       | str  | id     | NestedExpr
       | Dict | List.

prefix: 'not' | '-'.
Suffix: Call
       | DotAccess
       | Index.
Call: '(' [NL] [MultiLine_ExprList] ')'.
Index: '[' [NL] Expr [':' Expr] ']'.
DotAccess: '.' id.
List: '[' [NL] MultiLine_ExprList ']'.
Dict: '{' [NL] KeyValue_List '}'.

KeyValue_List: KeyValue_Expr {CommaNL KeyValue_Expr} [CommaNL].
KeyValue_Expr: Expr [':' Expr].

NestedExpr: '(' Expr ')'.

Assign_Op: '=' | '+=' | '-=' | '*=' | '/=' | '%='.

bool: 'True' | 'False'.
num: /[0-9]+/.
str: /" insideString* "/.
insideString: ascii | escapes.
escapes: '\\n' | '\\"'
id: /[a-zA-Z_][a-zA-Z0-9_]*/.
```

Nessa gramática, coisas entre `//` são expressões regulares,
coisas entre `''` são terminais, coisas entre `[]` são opcionais,
coisas entre `{}` podem ser repetidas de 0 a N vezes,
o uso de `|` representa escolhas entre produções (leia-se "ou" ou "or"),
o uso de `:` representa a definição de uma regra (production) e cada
regra é terminada com `.`.

Coisas especiais:
 - a regra `WhiteSpace` define caracteres que podem
ser ignorados, isso inclui espaço e comentários.
 - o uso de `>` representa uma indentação obrigatória,
inspirado pelo artigo [_Indentation-Sensitive Parsing for Parsec_](https://osa1.net/papers/indentation-sensitive-parsec.pdf).
 - o uso de `=` indica que a produção seguinte tem que ter o mesmo
nivel de indentação que produção atual.

O nivel de indentação de uma produção é definido
pelo primeiro token consumido por aquela produção.
Quando escrevemos:

```ebnf
Block: { =Statement NL }.
```

Queremos dizer que o nível de indentação de cada `Statement`
precisa ser necessariamente igual da produção `Block`.
A indentação de `Block` é definida pelo primeiro `Statement` do bloco,
que consome o primeiro token.

Por outro lado, quando escrevemos:

```ebnf
While: 'while' Expr ':' NL >Block.
```

Queremos dizer que o nível de indentação da produção `Block` tem que estar
estritamente maior que o nível de `While`, nesse caso, a indentação do
da produção `While` é definida pela palavra chave `'while'`.

## Ideia geral

O interpretador vai expor apenas uma função `evaluate`
que toma um dicionário de strings para strings e uma string,
ie, algo tipo `evaluate(dict:str->str, name:str)` se python tivesse tipos.

O parametro `name` tem de estar em `dict`, e `dict[name]`
vai ser o módulo pelo qual o interpretador começa a executar.
Qualquer módulo importado terá de estar em `dict`,
e será importado por nome, ie, `import lexer` requer que
`dict["lexer"]` seja uma string representando o módulo `lexer`.

Desse jeito o interpretador não tem que saber nada sobre arquivos no geral,
e pode só ser feliz executando código no mundinho dele, enquanto um script
rodando em CPython pode ler uma pasta inteira de arquivos e passar para 
o auto-interpretador.
