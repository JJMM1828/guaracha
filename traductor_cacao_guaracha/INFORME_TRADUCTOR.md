# Informe técnico: traductor CacaoCore64 → Guarachacore

## 1. Propósito y alcance

El proyecto implementa un traductor fuente-a-fuente: recibe un programa en
ensamblador de **CacaoCore64** y produce un archivo `.asm` equivalente para
**Guarachacore**. No genera directamente código máquina; el resultado pasa por
el ensamblador, enlazador, cargador y procesador de Guarachacore.

El alcance implementado cubre el subconjunto entero utilizado por los tres
programas de prueba:

- secciones `.data` y `.text`;
- etiquetas y datos enteros;
- movimientos entre registros, memoria, inmediatos y direcciones;
- `LEA`, `ADD`, `SUB`, `MUL`, `DIV`, `INC`, `DEC` y `CMP`;
- `JMP`, `JZ`, `JG`, `JLE`, `HLT`, `NOP` e `INTR 0`.

No cubre todavía punto flotante, cadenas, subrutinas, interrupciones distintas
de `INTR 0`, ni el resto de la ISA completa de CacaoCore64.

## 2. Marco teórico breve

### 2.1 Traductor de lenguaje ensamblador

Un traductor toma una representación en un lenguaje origen y la transforma a
una representación con la misma intención computacional en un lenguaje
destino. En este caso ambos lenguajes son ensambladores, pero sus instrucciones,
sus banderas y su organización de memoria son diferentes. Por eso no basta con
reemplazar palabras: se deben preservar los efectos sobre registros, memoria y
flujo de control.

El proceso puede describirse así:

```text
Programa Cacao ──análisis léxico──> tokens ──traducción semántica──>
programa Guarachacore ──ensamblado y ejecución──> resultado
```

### 2.2 Análisis léxico con LEX

LEX/Flex es una herramienta que genera analizadores léxicos a partir de reglas
regulares. Un analizador léxico convierte caracteres en *tokens*, por ejemplo:

```text
MOVD R0, [a]
  │    │    └── LABEL entre corchetes
  │    └────── REGISTER
  └─────────── MNEMONIC
```

Los tokens eliminan detalles como espacios y comentarios, y permiten que la
fase siguiente interprete la estructura del programa.

### 2.3 Preservación semántica

La equivalencia se obtiene mediante reglas de mapeo. Algunas son directas,
como `ADD R1,R2 → SUMAR R1,R2`; otras necesitan varias instrucciones. Por
ejemplo, la división de Cacao deja el cociente en el primer registro y el
residuo en el segundo; Guarachacore separa ambas operaciones en `DIVIDIR` y
`MODULO`. El traductor debe expandir la instrucción para conservar ambos
resultados.

Las direcciones también deben relocalizarse: Cacao usa su zona estática desde
`0x40000`, fuera de los 64 KiB disponibles en Guarachacore. El traductor la
traslada a `0x4000`, manteniendo las distancias entre elementos del arreglo.

## 3. Archivo `cacao_guaracha.l`: especificación LEX

El archivo [cacao_guaracha.l](cacao_guaracha.l) contiene la especificación
formal del analizador léxico para Flex/LEX. Su finalidad es definir qué grupos
de caracteres constituyen unidades válidas del ensamblador CacaoCore64.

### 3.1 Cabecera y opciones

```lex
%option noyywrap nodefault yylineno
```

- `noyywrap` evita que Flex busque una función adicional al terminar la
  entrada.
- `nodefault` impide que caracteres sin regla se acepten silenciosamente.
- `yylineno` mantiene el número de línea actual; se usa para reportar errores.

El bloque entre `%{` y `%}` se copia al código C generado por Flex:

```c
#include <stdio.h>
enum token { SECTION=1, MNEMONIC, REGISTER, HEXADDRESS, NUMBER, LABEL,
             COLON, COMMA, LBRACKET, RBRACKET, NEWLINE };
```

Incluye la biblioteca de salida estándar y declara los códigos que devuelve el
scanner. Por ejemplo, una instrucción retorna `MNEMONIC`, mientras que `R4`
retorna `REGISTER`.

### 3.2 Delimitadores de reglas

Los dos separadores `%%` delimitan tres zonas de un archivo LEX:

1. declaraciones y código de apoyo;
2. reglas `expresión regular → acción`;
3. código C adicional opcional.

En este archivo, la tercera sección queda vacía porque sólo se especifica el
scanner.

### 3.3 Reglas léxicas, una por una

| Regla LEX | Acción | Significado |
|---|---|---|
| `[ \t\r]+` | `;` | Descarta espacios, tabuladores y retorno de carro. |
| `[\#\;][^\n]*` | `;` | Descarta comentarios iniciados con `#` o `;`. |
| `".data"|".DATA"` | `return SECTION` | Reconoce inicio de datos. |
| `".text"|".TEXT"` | `return SECTION` | Reconoce inicio de código. |
| `[Rr](1[0-5]|[0-9])` | `return REGISTER` | Acepta registros `R0` a `R15`, en ambos casos. |
| `0[xX][0-9a-fA-F]+` | `return HEXADDRESS` | Reconoce números hexadecimales, típicamente direcciones. |
| `[+-]?[0-9]+` | `return NUMBER` | Reconoce enteros decimales con signo opcional. |
| `"["`, `"]"`, `":"`, `","` | token puntual | Reconoce corchetes, etiqueta y separación de operandos. |
| lista `MOVB|...|NOP` | `return MNEMONIC` | Reserva las instrucciones Cacao admitidas por el traductor. |
| `[A-Za-z_][A-Za-z0-9_@]*` | `return LABEL` | Reconoce etiquetas y nombres de variables. |
| `\n` | `return NEWLINE` | Conserva el fin de línea para diagnosticar y separar sentencias. |
| `.` | mensaje de error | Reporta cualquier carácter no contemplado e indica la línea. |

El orden es importante. Por ejemplo, la regla hexadecimal aparece antes de la
regla decimal: así `0x40000` se toma como una sola dirección hexadecimal y no
como un `0` seguido de caracteres inválidos.

### 3.4 Relación real entre LEX y el ejecutable

El archivo `.l` puede ser procesado por Flex para generar un scanner en C.
En la entrega actual no se exige instalar Flex en el equipo: el ejecutable
`traducir.py` reproduce las mismas clases de tokens con expresiones regulares
Python. Por ello el archivo LEX funciona como la especificación léxica formal
del proyecto y `traducir.py` es la implementación autónoma que se ejecuta.

## 4. Archivo `traducir.py`: funcionamiento detallado

`traducir.py` es el componente principal. Lee un `.asm` de Cacao, lo analiza
línea por línea, emite instrucciones Guarachacore y guarda el resultado en un
archivo de salida.

### 4.1 Expresiones regulares y funciones auxiliares

Al inicio se definen patrones para clasificar texto:

```python
REGISTRO       # R0 a R15
HEXADECIMAL    # 0x...
DECIMAL        # entero con signo opcional
IDENTIFICADOR  # etiquetas y variables
```

Las funciones `sin_comentario`, `separar_operandos`, `es_registro`,
`es_hexadecimal`, `es_numero`, `numero` y `corchetes` implementan operaciones
pequeñas sobre esos tokens. Por ejemplo, `corchetes("[R4]")` devuelve `R4`;
esto permite distinguir memoria indirecta de un operando ordinario.

### 4.2 Estado del objeto `Traductor`

La clase `Traductor` usa `@dataclass` para mantener el estado de una
traducción:

| Campo | Función |
|---|---|
| `salida` | Lista ordenada de líneas Guarachacore emitidas. |
| `datos` | Variables encontradas en `.data`, para declararlas al final. |
| `seccion` | Indica si se está leyendo `.data` o `.text`. |
| `saltos_generados` | Evita colisiones entre etiquetas auxiliares de `JG`. |
| `usa_temporal` | Indica que se debe reservar `__tr_tmp` para salvar `R15`. |

### 4.3 Relocalización de direcciones: `direccion`

```python
RANGO_DATOS_CACAO = 0x40000
BASE_DATOS_GUARACHA = 0x4000
```

El método `direccion` aplica dos reglas:

1. Una dirección Cacao `A ≥ 0x40000` se convierte en
   `0x4000 + (A - 0x40000)`. Así, `0x40000 → 0x4000` y
   `0x40030 → 0x4030`.
2. Una dirección baja no alineada se multiplica por ocho. Guarachacore exige
   palabras alineadas a 8 bytes, mientras Cacao admite posiciones como
   `0x177`. Por ejemplo, `0x177 → 0xBB8`.

Esta segunda regla es segura para los tres ejemplos porque esas direcciones
bajas no se usan para calcular punteros.

### 4.4 Traducción de movimientos: `mover`

El método `mover` resuelve las variantes de `MOVB`, `MOVH`, `MOVW` y `MOVD`.
En el subconjunto tratado, las cuatro se convierten en operaciones de palabra
de 64 bits, ya que los ejemplos almacenan elementos a intervalos de ocho bytes.

| Cacao | Guarachacore emitido |
|---|---|
| `MOVD R0, R1` | `MOVER R0, R1` |
| `MOVD R0, 10` | `CARGARINM R0, 10` |
| `MOVD R0, [a]` | `CARGAR R0, a` |
| `MOVH R6, [R4]` | `CARGAR_IND R6, R4` |
| `MOVW [temp], R1` | `GUARDAR R1, temp` |
| `MOVH [R4], R6` | `GUARDAR_IND R6, R4` |

Cuando Cacao escribe un inmediato directamente en memoria, Guarachacore no
puede hacerlo con una sola instrucción. El traductor guarda `R15` en
`__tr_tmp`, coloca el inmediato en `R15`, realiza `GUARDAR` y recupera `R15`.

### 4.5 Traducción aritmética y el caso especial de `DIV`

`ADD`, `SUB` y `MUL` se mapean respectivamente a `SUMAR`, `RESTAR` y
`MULTIPLICAR`. Si el segundo operando es inmediato, se materializa primero en
`R15`.

La división requiere una expansión porque en Cacao:

```text
DIV Rd, Rs  →  Rd = cociente; Rs = residuo
```

En Guarachacore, `DIVIDIR` deja el cociente en su primer registro y `MODULO`
deja el residuo en su primer registro. Por eso el traductor emite:

```asm
GUARDAR R15, __tr_tmp
MOVER R15, Rd
DIVIDIR Rd, Rs
MODULO R15, Rs
MOVER Rs, R15
CARGAR R15, __tr_tmp
```

El resultado conserva el contrato de Cacao: cociente en `Rd` y residuo en
`Rs`.

### 4.6 Comparaciones y saltos

Las reglas principales son:

| Cacao | Emisión Guarachacore |
|---|---|
| `CMP Ra,Rb` | `COMPARAR Ra,Rb` |
| `JMP etiqueta` | `SALTAR etiqueta` |
| `JZ etiqueta` | `SALTAZ etiqueta` |
| `JLE etiqueta` | `SALTAN etiqueta` seguido de `SALTAZ etiqueta` |

Guarachacore no tiene un salto estricto «mayor que». Por ello `JG destino` se
convierte en una pequeña secuencia:

```asm
SALTAN __tr_no_jg_0
SALTAZ __tr_no_jg_0
SALTAR destino
__tr_no_jg_0:
```

Si la comparación fue negativa o cero, se evita el salto; sólo salta cuando
el primer operando es estrictamente mayor. Los tres ejemplos trabajan con
enteros positivos, que es el dominio donde la comparación firmada de Cacao y
la usada por estas secuencias coincide.

### 4.7 Lectura de secciones y generación final

El método `traducir` recorre las líneas de entrada. Ignora comentarios, guarda
los datos de `.data`, conserva las etiquetas de `.text` y envía cada
instrucción a `traducir_instruccion`. Al final agrega:

```asm
.ALINEAR 8
variable: .PALABRA valor
__tr_tmp: .PALABRA 0
```

La alineación asegura que cada palabra pueda cargarse o guardarse correctamente
en Guarachacore.

### 4.8 Punto de entrada

La función `main` recibe dos parámetros:

```text
python traducir.py <entrada.asm> <salida.asm>
```

Lee el archivo origen, invoca `Traductor().traducir(...)` y escribe el
ensamblador Guarachacore producido. Si encuentra una instrucción u operando no
soportado, muestra un error de traducción en lugar de producir una salida
incompleta.

## 5. Archivo `verificar.py`: descripción general

`verificar.py` automatiza la validación. No requiere argumentos: usa los tres
archivos Cacao que están en la carpeta `traductor_cacao_guaracha/`, llama al
traductor, guarda las salidas en `ejemplos/traducidos/`, las ensambla y las
ejecuta mediante el emulador Guarachacore.

Finalmente consulta la palabra de memoria que contiene el resultado de cada
algoritmo y la compara con el valor esperado. Si hay una diferencia, genera un
error; si todo funciona, imprime una línea `OK` por caso. Este archivo no
participa en la traducción misma: es una prueba automática de integración.

## 6. Análisis de los tres casos de prueba

### 6.1 `alg_euc_res.asm`: máximo común divisor por restas

**Algoritmo CacaoCore64.** Inicializa dos valores, `756` y `924`, en memoria.
Luego los compara: si son iguales termina; si el primero es mayor lo reduce
restándole el segundo y, si no, reduce el segundo restándole el primero. Este
es el algoritmo de Euclides por restas repetidas. Al finalizar ambos valores
son iguales al máximo común divisor:

```text
mcd(756, 924) = 84
```

**Traducción Guarachacore.** Los `MOVD` que inicializan ubicaciones como
`0x177` se convierten en carga de inmediato y `GUARDAR`, usando una dirección
alineada. `CMP`, `JZ`, `JG`, `SUB` y `JMP` se convierten en `COMPARAR`,
saltos Guarachacore, `RESTAR` y `SALTAR`. El valor final se copia a `temp`.

**Comprobación.** El programa traducido ejecuta 57 instrucciones y deja `84`
en `temp`.

### 6.2 `alg_euc_mod.asm`: máximo común divisor por residuos

**Algoritmo CacaoCore64.** Declara `a = 987654` y `b = 123456`. Antes del
bucle intercambia los valores si es necesario. En cada iteración calcula el
residuo de dividir el mayor por el menor, desplaza los valores y repite hasta
que el residuo sea cero. Es la versión clásica y más eficiente del algoritmo
de Euclides:

```text
mcd(a, b) = mcd(b, a mod b)
mcd(987654, 123456) = 6
```

**Traducción Guarachacore.** Las variables pasan a ser `.PALABRA`; las cargas
`MOVD R0,[a]` y `MOVD R1,[b]` se vuelven `CARGAR`. La instrucción crucial
`DIV R3,R2` se expande a una división para el cociente y una operación módulo
para dejar el residuo en `R2`, como exige la semántica Cacao. El `CMP R2,0`
crea un cero temporal en `R15` y luego usa `COMPARAR R2,R15`.

**Comprobación.** El programa traducido ejecuta 48 instrucciones y deja `6`
en `temp`.

### 6.3 `search_max.asm`: búsqueda del máximo de un arreglo

**Algoritmo CacaoCore64.** Inicializa el arreglo:

```text
[1, 8, 4, 2, 10]
```

en direcciones desde `0x40000` y guarda su tamaño, `5`, después del arreglo.
Toma el primer elemento como máximo inicial, recorre las posiciones restantes,
calcula cada dirección como `base + índice × 8`, carga el elemento y reemplaza
el máximo cuando encuentra uno mayor. El resultado esperado es `10`.

**Traducción Guarachacore.** La ventana se reubica de `0x40000` a `0x4000`:

| Dirección Cacao | Dirección Guarachacore | Contenido |
|---:|---:|---:|
| `0x40000` | `0x4000` | primer elemento (`1`) |
| `0x40020` | `0x4020` | último elemento (`10`) |
| `0x40028` | `0x4028` | tamaño (`5`) |
| `0x40030` | `0x4030` | resultado |

El acceso `MOVH R6,[R4]` es esencial porque `R4` se calcula en tiempo de
ejecución. Se traduce a `CARGAR_IND R6,R4`. Para hacerlo posible se incorporó
la instrucción `CARGAR_IND` al procesador Guarachacore; análogamente,
`GUARDAR_IND` permite las escrituras indirectas.

**Comprobación.** El programa traducido ejecuta 100 instrucciones y deja `10`
en la dirección `0x4030`.

## 7. Manual de uso

### 7.1 Traducir un programa individual

Ubíquese en la raíz del proyecto y ejecute:

```powershell
python traductor_cacao_guaracha/traducir.py origen_cacao.asm salida_guaracha.asm
```

Ejemplo:

```powershell
python traductor_cacao_guaracha/traducir.py `
  traductor_cacao_guaracha/alg_euc_res.asm `
  ejemplos/traducidos/mi_euclides.asm
```

El segundo argumento es el archivo que se crea. Es texto ensamblador válido
para Guarachacore, por lo que puede abrirse, revisarse o editarse.

### 7.2 Ejecutar el programa traducido

```powershell
python -m guarachacore ejemplos/traducidos/mi_euclides.asm --ejecutar
```

El resultado queda en la posición de memoria indicada por el programa
traducido. Los ejemplos usan `temp` o la dirección `0x4030`.

### 7.3 Ejecutar todas las verificaciones

Los tres archivos de entrada ya están dentro de la carpeta del traductor.
Por tanto, la verificación completa no requiere parámetros:

```powershell
python traductor_cacao_guaracha/verificar.py
```

La salida esperada es:

```text
OK alg_euc_res.asm: 84 (57 instrucciones)
OK alg_euc_mod.asm: 6 (48 instrucciones)
OK search_max.asm: 10 (100 instrucciones)
```

## 8. Limitaciones conocidas

- Sólo se implementa el subconjunto de instrucciones necesario para los tres
  programas de prueba.
- `INTR 0` se traduce a `NOP`. El cálculo y su resultado en RAM se preservan,
  pero Guarachacore no reproduce el protocolo de consola de Cacao basado en
  `R10`, `R11` y `R12`.
- `R15` es temporal en expansiones de inmediatos y división. Los casos de
  prueba no emplean este registro de forma explícita.
- Las comparaciones traducidas se validaron con enteros positivos. Ampliar la
  traducción a todos los casos de signo requeriría una política completa de
  banderas y saltos firmados.
- El archivo LEX define el contrato léxico; `traducir.py` es actualmente la
  versión ejecutable autónoma que implementa dicho contrato sin depender de
  Flex instalado.
