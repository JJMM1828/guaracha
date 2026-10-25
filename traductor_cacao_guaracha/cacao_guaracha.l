/* Especificación LEX/Flex del análisis léxico CacaoCore64.
 * El programa traducir.py implementa las acciones semánticas de esta misma
 * clasificación para que la práctica se ejecute aun sin flex instalado. */
%option noyywrap nodefault yylineno
%{
#include <stdio.h>
enum token { SECTION=1, MNEMONIC, REGISTER, HEXADDRESS, NUMBER, LABEL,
             COLON, COMMA, LBRACKET, RBRACKET, NEWLINE };
%}
%%
[ \t\r]+                 ;
[\#\;][^\n]*             ;
".data"|".DATA"          return SECTION;
".text"|".TEXT"          return SECTION;
[Rr](1[0-5]|[0-9])       return REGISTER;
0[xX][0-9a-fA-F]+        return HEXADDRESS;
[+-]?[0-9]+              return NUMBER;
"["                     return LBRACKET;
"]"                     return RBRACKET;
":"                     return COLON;
","                     return COMMA;
(MOVB|MOVH|MOVW|MOVD|LEA|ADD|SUB|MUL|DIV|INC|DEC|CMP|JMP|JZ|JG|JLE|HLT|INTR|NOP) return MNEMONIC;
[A-Za-z_][A-Za-z0-9_@]*  return LABEL;
\n                      return NEWLINE;
.                       { fprintf(stderr, "token inválido '%s', línea %d\n", yytext, yylineno); }
%%
