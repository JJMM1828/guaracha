"""Traductor CacaoCore64 -> Guarachacore para el subconjunto entero.

La especificación léxica equivalente para flex/LEX está en cacao_guaracha.l.
Este ejecutable autónomo mantiene las mismas clases léxicas para poder usar el
traductor sin instalar flex en el computador anfitrión.
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path


class ErrorTraduccion(ValueError):
    pass


REGISTRO = re.compile(r"R(?:1[0-5]|[0-9])$", re.IGNORECASE)
HEXADECIMAL = re.compile(r"0x[0-9a-f]+$", re.IGNORECASE)
DECIMAL = re.compile(r"[+-]?\d+$")
IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_@]*$")
RANGO_DATOS_CACAO = 0x40000
BASE_DATOS_GUARACHA = 0x4000


def sin_comentario(linea: str) -> str:
    return re.split(r"[;#]", linea, maxsplit=1)[0].strip()


def separar_operandos(texto: str) -> list[str]:
    return [parte.strip() for parte in texto.split(",") if parte.strip()]


def es_registro(texto: str) -> bool:
    return bool(REGISTRO.fullmatch(texto))


def es_hexadecimal(texto: str) -> bool:
    return bool(HEXADECIMAL.fullmatch(texto))


def es_numero(texto: str) -> bool:
    return bool(DECIMAL.fullmatch(texto) or es_hexadecimal(texto))


def numero(texto: str) -> int:
    return int(texto, 0)


def corchetes(texto: str) -> str | None:
    if texto.startswith("[") and texto.endswith("]"):
        return texto[1:-1].strip()
    return None


@dataclass
class Traductor:
    """Estado semántico construido a partir de los tokens LEX de cada línea."""

    salida: list[str] = field(default_factory=list)
    datos: list[tuple[str, str]] = field(default_factory=list)
    seccion: str | None = None
    saltos_generados: int = 0
    usa_temporal: bool = False

    def direccion(self, operando: str) -> str:
        """Relocaliza la ventana de datos estáticos de Cacao dentro de 64 KiB."""
        if es_hexadecimal(operando):
            valor = numero(operando)
            if valor >= RANGO_DATOS_CACAO:
                return hex(BASE_DATOS_GUARACHA + valor - RANGO_DATOS_CACAO)
            # Cacao permite palabras en cualquier byte; Guarachacore exige
            # alineación a ocho. Las direcciones bajas no participan en la
            # aritmética de punteros de los ejemplos, así que se embeben de
            # forma inyectiva en posiciones alineadas.
            if valor % 8:
                return hex(valor * 8)
        return operando

    def emitir(self, *lineas: str) -> None:
        self.salida.extend(lineas)

    def temporal(self, instruccion: str, destino: str, fuente: str) -> None:
        """Materializa un inmediato sin alterar un registro fuente del programa."""
        self.usa_temporal = True
        self.emitir(
            "GUARDAR R15, __tr_tmp",
            f"CARGARINM R15, {fuente}",
            f"{instruccion} {destino}, R15",
            "CARGAR R15, __tr_tmp",
        )

    def mover(self, destino: str, fuente: str, linea: int) -> None:
        referencia = corchetes(fuente)
        if es_registro(destino):
            if referencia is not None:
                if es_registro(referencia):
                    self.emitir(f"CARGAR_IND {destino}, {referencia}")
                else:
                    self.emitir(f"CARGAR {destino}, {self.direccion(referencia)}")
            elif es_registro(fuente):
                self.emitir(f"MOVER {destino}, {fuente}")
            elif es_hexadecimal(fuente):
                # En Cacao un literal hexadecimal en MOV* es una dirección.
                self.emitir(f"CARGAR {destino}, {self.direccion(fuente)}")
            elif DECIMAL.fullmatch(fuente):
                self.emitir(f"CARGARINM {destino}, {fuente}")
            elif IDENTIFICADOR.fullmatch(fuente):
                self.emitir(f"CARGAR {destino}, {fuente}")
            else:
                raise ErrorTraduccion(f"línea {linea}: operando MOV no válido: {fuente}")
            return

        referencia_destino = corchetes(destino)
        direccion = referencia_destino if referencia_destino is not None else destino
        if es_registro(direccion):
            if not es_registro(fuente):
                self.usa_temporal = True
                self.emitir("GUARDAR R15, __tr_tmp", f"CARGARINM R15, {fuente}", f"GUARDAR_IND R15, {direccion}", "CARGAR R15, __tr_tmp")
            else:
                self.emitir(f"GUARDAR_IND {fuente}, {direccion}")
        elif es_registro(fuente):
            self.emitir(f"GUARDAR {fuente}, {self.direccion(direccion)}")
        elif es_numero(fuente):
            self.usa_temporal = True
            self.emitir(
                "GUARDAR R15, __tr_tmp",
                f"CARGARINM R15, {fuente}",
                f"GUARDAR R15, {self.direccion(direccion)}",
                "CARGAR R15, __tr_tmp",
            )
        else:
            raise ErrorTraduccion(f"línea {linea}: fuente MOV no válida: {fuente}")

    def aritmetica(self, nombre: str, destino: str, fuente: str, linea: int) -> None:
        instrucciones = {"ADD": "SUMAR", "SUB": "RESTAR", "MUL": "MULTIPLICAR"}
        if nombre == "DIV":
            if not es_registro(fuente):
                raise ErrorTraduccion(f"línea {linea}: DIV sólo admite registro en esta traducción")
            # Cacao deja el cociente en destino y el residuo en fuente.
            self.usa_temporal = True
            self.emitir(
                "GUARDAR R15, __tr_tmp",
                f"MOVER R15, {destino}",
                f"DIVIDIR {destino}, {fuente}",
                f"MODULO R15, {fuente}",
                f"MOVER {fuente}, R15",
                "CARGAR R15, __tr_tmp",
            )
            return
        instruccion = instrucciones[nombre]
        if es_registro(fuente):
            self.emitir(f"{instruccion} {destino}, {fuente}")
        elif DECIMAL.fullmatch(fuente):
            self.temporal(instruccion, destino, fuente)
        else:
            raise ErrorTraduccion(f"línea {linea}: {nombre} no admite {fuente}")

    def salto_mayor(self, destino: str) -> None:
        etiqueta = f"__tr_no_jg_{self.saltos_generados}"
        self.saltos_generados += 1
        self.emitir(f"SALTAN {etiqueta}", f"SALTAZ {etiqueta}", f"SALTAR {destino}", f"{etiqueta}:")

    def traducir_instruccion(self, texto: str, linea: int) -> None:
        partes = texto.split(None, 1)
        instruccion = partes[0].upper()
        operandos = separar_operandos(partes[1]) if len(partes) == 2 else []
        if instruccion in {"MOVB", "MOVH", "MOVW", "MOVD"}:
            if len(operandos) != 2:
                raise ErrorTraduccion(f"línea {linea}: {instruccion} requiere dos operandos")
            self.mover(operandos[0], operandos[1], linea)
        elif instruccion == "LEA":
            if len(operandos) != 2 or not es_registro(operandos[0]):
                raise ErrorTraduccion(f"línea {linea}: LEA inválido")
            referencia = corchetes(operandos[1]) or operandos[1]
            self.emitir(f"CARGARINM {operandos[0]}, {self.direccion(referencia)}")
        elif instruccion in {"ADD", "SUB", "MUL", "DIV"}:
            if len(operandos) != 2:
                raise ErrorTraduccion(f"línea {linea}: {instruccion} requiere dos operandos")
            self.aritmetica(instruccion, operandos[0], operandos[1], linea)
        elif instruccion == "INC" and len(operandos) == 1:
            self.emitir(f"INCREMENTAR {operandos[0]}")
        elif instruccion == "DEC" and len(operandos) == 1:
            self.emitir(f"DECREMENTAR {operandos[0]}")
        elif instruccion == "CMP" and len(operandos) == 2:
            if es_registro(operandos[1]):
                self.emitir(f"COMPARAR {operandos[0]}, {operandos[1]}")
            elif DECIMAL.fullmatch(operandos[1]):
                # La bandera de CMP debe sobrevivir hasta el salto siguiente;
                # por ello no se restaura R15 después de la comparación.
                self.emitir(f"CARGARINM R15, {operandos[1]}", f"COMPARAR {operandos[0]}, R15")
            else:
                raise ErrorTraduccion(f"línea {linea}: CMP no admite {operandos[1]}")
        elif instruccion == "JMP" and len(operandos) == 1:
            self.emitir(f"SALTAR {operandos[0]}")
        elif instruccion == "JZ" and len(operandos) == 1:
            self.emitir(f"SALTAZ {operandos[0]}")
        elif instruccion == "JG" and len(operandos) == 1:
            self.salto_mayor(operandos[0])
        elif instruccion == "JLE" and len(operandos) == 1:
            self.emitir(f"SALTAN {operandos[0]}", f"SALTAZ {operandos[0]}")
        elif instruccion == "HLT":
            self.emitir("DETENER")
        elif instruccion == "INTR" and operandos == ["0"]:
            self.emitir("NOP ; INTR 0 de Cacao: resultado disponible en RAM")
        elif instruccion == "NOP":
            self.emitir("NOP")
        else:
            raise ErrorTraduccion(f"línea {linea}: instrucción Cacao no soportada: {texto}")

    def traducir(self, fuente: str) -> str:
        for numero_linea, original in enumerate(fuente.splitlines(), 1):
            texto = sin_comentario(original)
            if not texto:
                continue
            if texto.lower() in {".data", ".text"}:
                self.seccion = texto.lower()
                continue
            coincidencia = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_@]*):\s*(.*)", texto)
            if coincidencia:
                nombre, resto = coincidencia.groups()
                if self.seccion == ".data" and resto:
                    if not es_numero(resto):
                        raise ErrorTraduccion(f"línea {numero_linea}: dato no entero: {resto}")
                    self.datos.append((nombre, resto))
                elif resto:
                    self.emitir(f"{nombre}:")
                    self.traducir_instruccion(resto, numero_linea)
                else:
                    self.emitir(f"{nombre}:")
                continue
            self.traducir_instruccion(texto, numero_linea)

        if self.datos or self.usa_temporal:
            self.emitir("", ".ALINEAR 8")
            for nombre, valor in self.datos:
                self.emitir(f"{nombre}: .PALABRA {valor}")
            if self.usa_temporal:
                self.emitir("__tr_tmp: .PALABRA 0")
        return "\n".join(self.salida) + "\n"


def main() -> int:
    argumentos = argparse.ArgumentParser(description="Traductor LEX CacaoCore64 -> Guarachacore")
    argumentos.add_argument("entrada", type=Path, help="archivo .asm de CacaoCore64")
    argumentos.add_argument("salida", type=Path, help="archivo .asm de Guarachacore")
    args = argumentos.parse_args()
    try:
        resultado = Traductor().traducir(args.entrada.read_text(encoding="utf-8"))
        args.salida.write_text(resultado, encoding="utf-8")
    except (OSError, ErrorTraduccion) as error:
        argumentos.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
