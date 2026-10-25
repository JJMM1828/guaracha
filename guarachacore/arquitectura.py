from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

BITS_PALABRA = 64
BYTES_PALABRA = 8
MASCARA64 = (1 << BITS_PALABRA) - 1


class Formato(Enum):
    F1 = 1
    F2 = 2
    F3 = 4
    F4 = 5
    F5 = 6


@dataclass(frozen=True)
class EspecificacionInstruccion:
    codigo: int
    formato: Formato
    operandos: str


CODIGOS: dict[str, EspecificacionInstruccion] = {
    "NOP": EspecificacionInstruccion(0x00, Formato.F1, ""),
    "DETENER": EspecificacionInstruccion(0x01, Formato.F1, ""),
    "MOVER": EspecificacionInstruccion(0x10, Formato.F2, "rr"),
    "CARGAR": EspecificacionInstruccion(0x11, Formato.F5, "rd"),
    "GUARDAR": EspecificacionInstruccion(0x12, Formato.F5, "rd"),
    "CARGAR_IND": EspecificacionInstruccion(0x13, Formato.F2, "rr"),
    "GUARDAR_IND": EspecificacionInstruccion(0x14, Formato.F2, "rr"),
    "CARGARINM": EspecificacionInstruccion(0x19, Formato.F5, "ri"),
    "EMPUJAR": EspecificacionInstruccion(0x1A, Formato.F5, "r"),
    "SACAR": EspecificacionInstruccion(0x1B, Formato.F5, "r"),
    "INTERCAMBIAR": EspecificacionInstruccion(0x1C, Formato.F2, "rr"),
    "SUMAR": EspecificacionInstruccion(0x20, Formato.F2, "rr"),
    "SUMAR_C": EspecificacionInstruccion(0x21, Formato.F2, "rr"),
    "RESTAR": EspecificacionInstruccion(0x22, Formato.F2, "rr"),
    "RESTAR_C": EspecificacionInstruccion(0x23, Formato.F2, "rr"),
    "MULTIPLICAR": EspecificacionInstruccion(0x24, Formato.F2, "rr"),
    "DIVIDIR": EspecificacionInstruccion(0x25, Formato.F2, "rr"),
    "MODULO": EspecificacionInstruccion(0x26, Formato.F2, "rr"),
    "INCREMENTAR": EspecificacionInstruccion(0x27, Formato.F2, "r"),
    "DECREMENTAR": EspecificacionInstruccion(0x28, Formato.F2, "r"),
    "NEGAR": EspecificacionInstruccion(0x29, Formato.F2, "r"),
    "COMPARAR": EspecificacionInstruccion(0x2A, Formato.F2, "rr"),
    "PRUEBA": EspecificacionInstruccion(0x2B, Formato.F2, "rr"),
    "Y": EspecificacionInstruccion(0x30, Formato.F2, "rr"),
    "O": EspecificacionInstruccion(0x31, Formato.F2, "rr"),
    "XOR": EspecificacionInstruccion(0x32, Formato.F2, "rr"),
    "NO": EspecificacionInstruccion(0x33, Formato.F2, "r"),
    "DESP_I": EspecificacionInstruccion(0x34, Formato.F2, "rr"),
    "DESP_D": EspecificacionInstruccion(0x35, Formato.F2, "rr"),
    "ROTA_I": EspecificacionInstruccion(0x36, Formato.F2, "rr"),
    "ROTA_D": EspecificacionInstruccion(0x37, Formato.F2, "rr"),
    "SALTAR": EspecificacionInstruccion(0x40, Formato.F4, "d"),
    "SALTAZ": EspecificacionInstruccion(0x41, Formato.F4, "d"),
    "SALTAN": EspecificacionInstruccion(0x42, Formato.F4, "d"),
    "SALTAC": EspecificacionInstruccion(0x43, Formato.F4, "d"),
    "SALTAV": EspecificacionInstruccion(0x44, Formato.F4, "d"),
    "SALTA_NOZ": EspecificacionInstruccion(0x45, Formato.F4, "d"),
    "LLAMAR": EspecificacionInstruccion(0x46, Formato.F4, "d"),
    "RETORNAR": EspecificacionInstruccion(0x47, Formato.F1, ""),
    "LEER_PUERTO": EspecificacionInstruccion(0x50, Formato.F3, "rp"),
    "ESCRIBIR_PUERTO": EspecificacionInstruccion(0x51, Formato.F3, "rp"),
    "DMA_ENTRADA": EspecificacionInstruccion(0x52, Formato.F5, "rd"),
    "DMA_SALIDA": EspecificacionInstruccion(0x53, Formato.F5, "rd"),
    "LEER_TECLADO": EspecificacionInstruccion(0x54, Formato.F3, "r"),
    "ESCRIBIR_PANTALLA": EspecificacionInstruccion(0x55, Formato.F3, "r"),
    "RED_ENVIAR": EspecificacionInstruccion(0x60, Formato.F3, "r"),
    "RED_RECIBIR": EspecificacionInstruccion(0x61, Formato.F3, "r"),
    "RED_ESTADO": EspecificacionInstruccion(0x62, Formato.F3, "r"),
    "RED_CONFIG": EspecificacionInstruccion(0x63, Formato.F3, "rp"),
    "RED_CERRAR": EspecificacionInstruccion(0x64, Formato.F3, "r"),
    "CACHE_LIMPIAR": EspecificacionInstruccion(0x70, Formato.F1, ""),
    "LEER_RTC": EspecificacionInstruccion(0x74, Formato.F3, "r"),
    "ESCRIBIR_RTC": EspecificacionInstruccion(0x75, Formato.F3, "r"),
}
POR_CODIGO = {dato.codigo: (nombre, dato) for nombre, dato in CODIGOS.items()}


def sin_signo(valor: int) -> int:
    return valor & MASCARA64


def con_signo(valor: int, bits: int = 64) -> int:
    valor &= (1 << bits) - 1
    return valor - (1 << bits) if valor & (1 << (bits - 1)) else valor


def codificar(nombre: str, operandos: list[int]) -> bytes:
    """Codifica una instrucción en bytes según su formato."""
    dato = CODIGOS[nombre]
    inicio = bytes([dato.codigo])
    if dato.formato is Formato.F1:
        return inicio
    if dato.formato is Formato.F2:
        destino, fuente = operandos[0], operandos[1] if len(operandos) > 1 else 0
        return inicio + bytes([(destino << 4) | fuente])
    if dato.formato is Formato.F3:
        registro, puerto = operandos
        return inicio + bytes([registro << 4]) + puerto.to_bytes(2, "big")
    if dato.formato is Formato.F4:
        return inicio + (operandos[0] & 0xFFFFFFFF).to_bytes(4, "big")
    registro, valor = operandos
    return inicio + bytes([registro << 4]) + (valor & 0xFFFFFFFF).to_bytes(4, "big")


def decodificar(datos: bytes) -> tuple[str, list[int], int]:
    if not datos or datos[0] not in POR_CODIGO:
        raise ValueError(f"código de operación inválido: 0x{datos[0] if datos else 0:02X}")
    nombre, dato = POR_CODIGO[datos[0]]
    if len(datos) < dato.formato.value:
        raise ValueError("instrucción incompleta en RAM")
    if dato.formato is Formato.F1:
        operandos = []
    elif dato.formato is Formato.F2:
        operandos = [datos[1] >> 4, datos[1] & 15]
    elif dato.formato is Formato.F3:
        operandos = [datos[1] >> 4, int.from_bytes(datos[2:4], "big")]
    elif dato.formato is Formato.F4:
        operandos = [int.from_bytes(datos[1:5], "big")]
    else:
        operandos = [datos[1] >> 4, int.from_bytes(datos[2:6], "big")]
    return nombre, operandos, dato.formato.value
