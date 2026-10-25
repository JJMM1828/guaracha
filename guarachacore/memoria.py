from __future__ import annotations
from dataclasses import dataclass, field
from .arquitectura import BYTES_PALABRA, MASCARA64

@dataclass
class Bus:
    nombre: str
    bits: int
    ultimo_valor: int = 0
    transferencias: int = 0
    def transferir(self, valor: int) -> int:
        self.ultimo_valor = valor & ((1 << self.bits) - 1); self.transferencias += 1
        return self.ultimo_valor

@dataclass
class LineaCache:
    etiqueta: int = -1
    datos: bytearray = field(default_factory=lambda: bytearray(BYTES_PALABRA))
    valida: bool = False

class MemoriaRAM:
    def __init__(self, tamano: int = 64 * 1024) -> None:
        if tamano <= 0: raise ValueError("El tamaño de RAM debe ser positivo")
        self.datos = bytearray(tamano)
    def _verificar(self, direccion: int, cantidad: int = 1) -> None:
        if direccion < 0 or cantidad < 0 or direccion + cantidad > len(self.datos):
            raise MemoryError(f"Dirección RAM fuera de rango: {direccion} (+{cantidad})")
    def leer_bytes(self, direccion: int, cantidad: int) -> bytes:
        self._verificar(direccion, cantidad); return bytes(self.datos[direccion:direccion + cantidad])
    def escribir_bytes(self, direccion: int, contenido: bytes) -> None:
        self._verificar(direccion, len(contenido)); self.datos[direccion:direccion + len(contenido)] = contenido
    def escribir_bits(self, direccion: int, bit_inicial: int, bits: str) -> None:
        if bit_inicial not in range(8) or set(bits) - {"0", "1"}: raise ValueError("se esperan bits 0/1 y posición 0..7")
        if not bits: return
        self._verificar(direccion + (bit_inicial + len(bits) - 1) // 8)
        for indice, bit in enumerate(bits):
            absoluto = bit_inicial + indice; byte, posicion = direccion + absoluto // 8, 7 - absoluto % 8
            self.datos[byte] = (self.datos[byte] | (1 << posicion)) if bit == "1" else (self.datos[byte] & ~(1 << posicion))

class MemoriaSecundaria:
    def __init__(self, tamano: int = 256 * 1024) -> None: self.datos = bytearray(tamano)
    def leer(self, direccion: int, cantidad: int) -> bytes:
        if direccion < 0 or direccion + cantidad > len(self.datos): raise MemoryError("dirección secundaria fuera de rango")
        return bytes(self.datos[direccion:direccion + cantidad])
    def guardar(self, direccion: int, contenido: bytes) -> None:
        if direccion < 0 or direccion + len(contenido) > len(self.datos): raise MemoryError("dirección secundaria fuera de rango")
        self.datos[direccion:direccion + len(contenido)] = contenido

class JerarquiaMemoria:
    def __init__(self, tamano_ram: int = 64 * 1024, lineas_cache: int = 16) -> None:
        self.ram, self.secundaria = MemoriaRAM(tamano_ram), MemoriaSecundaria()
        self.cache = [LineaCache() for _ in range(lineas_cache)]
        self.bus_datos, self.bus_direcciones = Bus("datos", 64), Bus("direcciones", 64)
        self.bus_control, self.bus_perifericos = Bus("control", 16), Bus("periféricos", 32)
        self.aciertos_cache = self.fallos_cache = 0
    def _linea(self, direccion_alineada: int) -> LineaCache:
        indice, etiqueta = (direccion_alineada // BYTES_PALABRA) % len(self.cache), direccion_alineada // BYTES_PALABRA
        linea = self.cache[indice]
        if linea.valida and linea.etiqueta == etiqueta: self.aciertos_cache += 1
        else:
            self.fallos_cache += 1; linea.etiqueta, linea.valida = etiqueta, True
            linea.datos[:] = self.ram.leer_bytes(direccion_alineada, BYTES_PALABRA)
        return linea
    def leer_byte(self, direccion: int) -> int:
        self.bus_direcciones.transferir(direccion); self.bus_control.transferir(2)
        linea = self._linea(direccion - direccion % BYTES_PALABRA)
        return self.bus_datos.transferir(linea.datos[direccion % BYTES_PALABRA])
    def leer_bytes(self, direccion: int, cantidad: int) -> bytes: return bytes(self.leer_byte(direccion + i) for i in range(cantidad))
    def escribir_byte(self, direccion: int, valor: int) -> None:
        self.bus_direcciones.transferir(direccion); self.bus_datos.transferir(valor); self.bus_control.transferir(4)
        self.ram.escribir_bytes(direccion, bytes([valor & 255])); alineada = direccion - direccion % BYTES_PALABRA
        linea = self.cache[(alineada // BYTES_PALABRA) % len(self.cache)]
        if linea.valida and linea.etiqueta == alineada // BYTES_PALABRA: linea.datos[direccion % BYTES_PALABRA] = valor & 255
    def escribir_bytes(self, direccion: int, contenido: bytes) -> None:
        for indice, valor in enumerate(contenido): self.escribir_byte(direccion + indice, valor)
    def leer_palabra(self, direccion: int) -> int:
        if direccion % BYTES_PALABRA: raise ValueError("las palabras deben alinearse a 8 bytes")
        return int.from_bytes(self.leer_bytes(direccion, BYTES_PALABRA), "little")
    def escribir_palabra(self, direccion: int, valor: int) -> None:
        if direccion % BYTES_PALABRA: raise ValueError("las palabras deben alinearse a 8 bytes")
        self.escribir_bytes(direccion, (valor & MASCARA64).to_bytes(BYTES_PALABRA, "little"))
    def invalidar_cache(self) -> None:
        for linea in self.cache: linea.valida = False
    def escribir_bits(self, direccion: int, bit_inicial: int, bits: str) -> None: self.ram.escribir_bits(direccion, bit_inicial, bits); self.invalidar_cache()
    def estadisticas(self) -> dict[str, int]: return {"aciertos": self.aciertos_cache, "fallos": self.fallos_cache, "bytes_ram": len(self.ram.datos)}
