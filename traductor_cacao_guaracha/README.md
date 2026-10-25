# Traductor LEX: CacaoCore64 a Guarachacore

El traductor acepta el subconjunto entero usado por los tres programas
entregados: secciones `.data/.text`, etiquetas, `MOVD/MOVH/MOVW`, `LEA`,
aritmética entera, comparaciones y saltos. La especificación formal de los
tokens está en `cacao_guaracha.l` y se puede procesar con Flex/LEX. El
ejecutable `traducir.py` materializa esas mismas reglas y no depende de
paquetes externos, de modo que es reproducible en la instalación actual.

## Diseño de la traducción

| CacaoCore64 | Guarachacore |
|---|---|
| `MOV* Rd, Rs`, inmediato o memoria | `MOVER`, `CARGARINM` o `CARGAR` |
| `MOV* [Ra], Rs` / `MOV* Rd, [Ra]` | `GUARDAR_IND` / `CARGAR_IND` |
| `LEA` | `CARGARINM` de la dirección |
| `ADD`, `SUB`, `MUL`, `INC`, `DEC`, `CMP` | Operación entera homóloga |
| `DIV Rd, Rs` | cociente en `Rd`, residuo en `Rs`, mediante `DIVIDIR` y `MODULO` |
| `JMP`, `JZ`, `JG`, `JLE` | `SALTAR`, `SALTAZ` y secuencias de saltos |
| `HLT` | `DETENER` |

Las direcciones Cacao desde `0x40000` se reubican en la ventana Guarachacore
que comienza en `0x4000`; esto conserva la aritmética de punteros del arreglo
de `search_max.asm` y la adapta a los 64 KiB de RAM de Guarachacore. Las
direcciones bajas no alineadas se multiplican por ocho, pues Cacao permite
palabras sin alineación y Guarachacore exige alineación de ocho bytes.

La traducción añade `CARGAR_IND` y `GUARDAR_IND` a Guarachacore. Son accesos
de palabra de 64 bits con dirección contenida en un registro. Son necesarios
para representar fielmente `MOVH R6, [R4]` del programa de búsqueda.

`INTR 0` queda como `NOP`: los resultados permanecen en la misma celda de RAM
que Cacao entrega a su rutina de consola. Guarachacore no tiene el protocolo
de impresión entera `R10/R11/R12` de Cacao.

## Uso

```powershell
python traductor_cacao_guaracha/traducir.py entrada.asm salida.asm
python -m guarachacore salida.asm --ejecutar
```

El registro `R15` se usa de forma temporal al materializar inmediatos en
memoria y al reproducir la semántica particular de `DIV` de Cacao. Los tres
programas de prueba no lo usan explícitamente.

## Verificación reproducible

```powershell
python traductor_cacao_guaracha/verificar.py
```

La prueba traduce, ensambla y ejecuta los archivos, comprobando `84` para
`alg_euc_res.asm`, `6` para `alg_euc_mod.asm` y `10` para `search_max.asm`.
Las emisiones verificadas también están en `ejemplos/traducidos/`.
