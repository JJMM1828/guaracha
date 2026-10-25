from collections import deque
from datetime import datetime, timezone
import socket
from .arquitectura import MASCARA64
PUERTO_TECLADO, PUERTO_PANTALLA, PUERTO_RTC, PUERTO_RED = 1, 2, 3, 4
class ControladorDispositivos:
    def __init__(self) -> None:
        self.teclado, self.cola_red, self.pantalla = deque(), deque(), []
        self.destino_red: tuple[str, int] | None = None
    def encolar_teclado(self, texto: str) -> None: self.teclado.extend(ord(caracter) for caracter in texto)
    def leer_puerto(self, puerto: int) -> int:
        if puerto == PUERTO_TECLADO: return self.teclado.popleft() if self.teclado else 0
        if puerto == PUERTO_RTC: return int(datetime.now(timezone.utc).timestamp())
        if puerto == PUERTO_RED: return self.cola_red.popleft() if self.cola_red else 0
        return 0
    def escribir_puerto(self, puerto: int, valor: int) -> None:
        valor &= MASCARA64
        if puerto == PUERTO_PANTALLA: self.pantalla.append(chr(valor & 255))
        elif puerto == PUERTO_RED:
            self.cola_red.append(valor)
            if self.destino_red:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as canal: canal.sendto(valor.to_bytes(8, "big"), self.destino_red)
    def configurar_red(self, anfitrion: str, puerto: int) -> None: self.destino_red = (anfitrion, puerto)
    def cerrar_red(self) -> None: self.destino_red = None
    def estado_red(self) -> int: return len(self.cola_red) | (0x100 if self.destino_red else 0)
    def texto_pantalla(self) -> str: return "".join(self.pantalla)
