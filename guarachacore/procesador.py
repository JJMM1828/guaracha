from __future__ import annotations
from dataclasses import dataclass
from .arquitectura import BYTES_PALABRA, MASCARA64, con_signo, decodificar, sin_signo
from .dispositivos import ControladorDispositivos, PUERTO_PANTALLA, PUERTO_RED, PUERTO_RTC, PUERTO_TECLADO
from .memoria import JerarquiaMemoria
Z, N, C, V, P, I = range(6)
class FalloProcesador(RuntimeError): pass
@dataclass
class ResultadoPaso:
    pc: int; instruccion: str; operandos: list[int]; detenido: bool
class Procesador:
    def __init__(self, memoria: JerarquiaMemoria | None = None, dispositivos: ControladorDispositivos | None = None) -> None:
        self.memoria, self.dispositivos = memoria or JerarquiaMemoria(), dispositivos or ControladorDispositivos()
        self.registros = [0] * 16; self.PC = self.IR = self.PSW = self.CR = self.ciclos = 0
        self.SP = self.BP = len(self.memoria.ram.datos) & ~(BYTES_PALABRA - 1); self.detenido = False
    def _bandera(self, bandera: int) -> bool: return bool(self.PSW & (1 << bandera))
    def _fijar_bandera(self, bandera: int, activa: bool) -> None: self.PSW = (self.PSW | (1 << bandera)) if activa else (self.PSW & ~(1 << bandera))
    def _actualizar_banderas(self, valor: int, acarreo: bool = False, desborde: bool = False) -> int:
        valor = sin_signo(valor); self._fijar_bandera(Z, valor == 0); self._fijar_bandera(N, bool(valor >> 63))
        self._fijar_bandera(C, acarreo); self._fijar_bandera(V, desborde); self._fijar_bandera(P, (valor & 255).bit_count() % 2 == 0); return valor
    def _escribir_registro(self, indice: int, valor: int, banderas: bool = False, acarreo: bool = False, desborde: bool = False) -> None:
        self.registros[indice] = self._actualizar_banderas(valor, acarreo, desborde) if banderas else sin_signo(valor)
    def _empujar(self, valor: int) -> None:
        if self.SP < BYTES_PALABRA: raise FalloProcesador("desbordamiento de pila")
        self.SP -= BYTES_PALABRA; self.memoria.escribir_palabra(self.SP, valor)
    def _sacar(self) -> int:
        if self.SP + BYTES_PALABRA > len(self.memoria.ram.datos): raise FalloProcesador("subdesbordamiento de pila")
        valor = self.memoria.leer_palabra(self.SP); self.SP += BYTES_PALABRA; return valor
    def _binaria(self, nombre: str, destino: int, fuente: int) -> None:
        a, b = self.registros[destino], self.registros[fuente]
        if nombre in {"SUMAR", "SUMAR_C"}:
            suma = b + (1 if nombre == "SUMAR_C" and self._bandera(C) else 0); bruto = a + suma; resultado = bruto & MASCARA64
            self._escribir_registro(destino, resultado, True, bruto > MASCARA64, (con_signo(a) >= 0 and con_signo(suma) >= 0 and con_signo(resultado) < 0) or (con_signo(a) < 0 and con_signo(suma) < 0 and con_signo(resultado) >= 0))
        elif nombre in {"RESTAR", "RESTAR_C"}:
            resta = b + (1 if nombre == "RESTAR_C" and self._bandera(C) else 0); self._escribir_registro(destino, a - resta, True, a >= resta)
        elif nombre == "MULTIPLICAR": self._escribir_registro(destino, a * b, True, a * b > MASCARA64)
        elif nombre in {"DIVIDIR", "MODULO"}:
            if not b: self.CR = 1; raise FalloProcesador("división por cero")
            self._escribir_registro(destino, a // b if nombre == "DIVIDIR" else a % b, True)
        elif nombre in {"Y", "O", "XOR"}: self._escribir_registro(destino, a & b if nombre == "Y" else a | b if nombre == "O" else a ^ b, True)
        elif nombre in {"DESP_I", "DESP_D", "ROTA_I", "ROTA_D"}:
            cantidad = b & 63
            valor = a << cantidad if nombre == "DESP_I" else a >> cantidad if nombre == "DESP_D" else ((a << cantidad) | (a >> ((64-cantidad)&63))) if nombre == "ROTA_I" else ((a >> cantidad) | (a << ((64-cantidad)&63)))
            self._escribir_registro(destino, valor, True)
        elif nombre == "COMPARAR": self._actualizar_banderas(a-b, a >= b)
        elif nombre == "PRUEBA": self._actualizar_banderas(a & b)
    def paso(self) -> ResultadoPaso:
        if self.detenido: return ResultadoPaso(self.PC, "DETENER", [], True)
        pc = self.PC
        try:
            crudo = bytes([self.memoria.leer_byte(pc)]) + self.memoria.leer_bytes(pc+1, 5); nombre, operandos, tamano = decodificar(crudo)
            self.IR = int.from_bytes(crudo[:tamano].ljust(8,b"\0"), "big"); self.PC += tamano; self._ejecutar(nombre, operandos); self.ciclos += 1
            return ResultadoPaso(pc, nombre, operandos, self.detenido)
        except (MemoryError, ValueError, FalloProcesador) as error:
            self.CR = self.CR or 2; raise FalloProcesador(f"PC={pc}: {error}") from error
    def ejecutar(self, maximo_pasos: int = 1_000_000) -> int:
        pasos = 0
        while not self.detenido:
            if pasos >= maximo_pasos: raise FalloProcesador("límite de pasos alcanzado")
            self.paso(); pasos += 1
        return pasos
    def _ejecutar(self, nombre: str, op: list[int]) -> None:
        if nombre == "NOP": return
        if nombre == "DETENER": self.detenido = True
        elif nombre == "MOVER": self._escribir_registro(op[0], self.registros[op[1]])
        elif nombre == "CARGARINM": self._escribir_registro(op[0], con_signo(op[1],32), True)
        elif nombre == "CARGAR": self._escribir_registro(op[0], self.memoria.leer_palabra(op[1]), True)
        elif nombre == "GUARDAR": self.memoria.escribir_palabra(op[1], self.registros[op[0]])
        elif nombre == "CARGAR_IND": self._escribir_registro(op[0], self.memoria.leer_palabra(self.registros[op[1]]), True)
        elif nombre == "GUARDAR_IND": self.memoria.escribir_palabra(self.registros[op[1]], self.registros[op[0]])
        elif nombre == "EMPUJAR": self._empujar(self.registros[op[0]])
        elif nombre == "SACAR": self._escribir_registro(op[0], self._sacar(), True)
        elif nombre == "INTERCAMBIAR": self.registros[op[0]], self.registros[op[1]] = self.registros[op[1]], self.registros[op[0]]
        elif nombre in {"SUMAR","SUMAR_C","RESTAR","RESTAR_C","MULTIPLICAR","DIVIDIR","MODULO","Y","O","XOR","DESP_I","DESP_D","ROTA_I","ROTA_D","COMPARAR","PRUEBA"}: self._binaria(nombre,*op)
        elif nombre == "INCREMENTAR": self._escribir_registro(op[0], self.registros[op[0]]+1, True)
        elif nombre == "DECREMENTAR": self._escribir_registro(op[0], self.registros[op[0]]-1, True)
        elif nombre == "NEGAR": self._escribir_registro(op[0], -self.registros[op[0]], True)
        elif nombre == "NO": self._escribir_registro(op[0], ~self.registros[op[0]], True)
        elif nombre in {"SALTAR","SALTAZ","SALTAN","SALTAC","SALTAV","SALTA_NOZ"}:
            tomar = nombre == "SALTAR" or (nombre == "SALTAZ" and self._bandera(Z)) or (nombre == "SALTAN" and self._bandera(N)) or (nombre == "SALTAC" and self._bandera(C)) or (nombre == "SALTAV" and self._bandera(V)) or (nombre == "SALTA_NOZ" and not self._bandera(Z))
            if tomar: self.PC = op[0]
        elif nombre == "LLAMAR": self._empujar(self.PC); self.PC = op[0]
        elif nombre == "RETORNAR": self.PC = self._sacar()
        elif nombre in {"LEER_PUERTO","LEER_TECLADO","RED_RECIBIR","LEER_RTC"}:
            puerto = {"LEER_TECLADO":PUERTO_TECLADO,"RED_RECIBIR":PUERTO_RED,"LEER_RTC":PUERTO_RTC}.get(nombre,op[1]); self._escribir_registro(op[0],self.dispositivos.leer_puerto(puerto),True)
        elif nombre in {"ESCRIBIR_PUERTO","ESCRIBIR_PANTALLA","RED_ENVIAR","ESCRIBIR_RTC"}:
            puerto = {"ESCRIBIR_PANTALLA":PUERTO_PANTALLA,"RED_ENVIAR":PUERTO_RED,"ESCRIBIR_RTC":PUERTO_RTC}.get(nombre,op[1]); self.dispositivos.escribir_puerto(puerto,self.registros[op[0]])
        elif nombre == "RED_ESTADO": self._escribir_registro(op[0],self.dispositivos.estado_red(),True)
        elif nombre == "RED_CONFIG": self.dispositivos.configurar_red("127.0.0.1",op[1]); self._escribir_registro(op[0],1,True)
        elif nombre == "RED_CERRAR": self.dispositivos.cerrar_red(); self._escribir_registro(op[0],0,True)
        elif nombre == "DMA_ENTRADA": self.memoria.escribir_bytes(op[1],self.memoria.secundaria.leer(self.registros[op[0]],BYTES_PALABRA))
        elif nombre == "DMA_SALIDA": self.memoria.secundaria.guardar(self.registros[op[0]],self.memoria.leer_bytes(op[1],BYTES_PALABRA))
        elif nombre == "CACHE_LIMPIAR": self.memoria.invalidar_cache()
    def estado(self) -> dict[str, object]: return {"R":self.registros.copy(),"PC":self.PC,"IR":self.IR,"SP":self.SP,"BP":self.BP,"PSW":self.PSW,"CR":self.CR,"detenido":self.detenido,"ciclos":self.ciclos}
