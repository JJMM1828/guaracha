"""Traduce y verifica los tres programas CacaoCore64 suministrados."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_PRUEBAS = Path(__file__).resolve().parent
CARPETA_SALIDA = RAIZ / "ejemplos" / "traducidos"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from guarachacore import Cargador, Enlazador, Ensamblador, Procesador
from traducir import Traductor


def ejecutar(archivo: Path, etiqueta: str | None, direccion: int | None) -> tuple[int, int]:
    modulo = Ensamblador().ensamblar_archivo(str(archivo))
    cpu = Procesador()
    Cargador().cargar(cpu, Enlazador().enlazar([modulo]))
    pasos = cpu.ejecutar(1_000_000)
    return pasos, cpu.memoria.leer_palabra(modulo.simbolos[etiqueta] if etiqueta else direccion)


def main() -> int:
    """Usa los tres fuentes Cacao incluidos en esta misma carpeta."""
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    casos = (
        ("alg_euc_res.asm", "alg_euc_res_guaracha.asm", "temp", None, 84),
        ("alg_euc_mod.asm", "alg_euc_mod_guaracha.asm", "temp", None, 6),
        ("search_max.asm", "search_max_guaracha.asm", None, 0x4030, 10),
    )
    for entrada, salida, etiqueta, direccion, esperado in casos:
        destino = CARPETA_SALIDA / salida
        fuente = CARPETA_PRUEBAS / entrada
        destino.write_text(Traductor().traducir(fuente.read_text(encoding="utf-8")), encoding="utf-8")
        pasos, obtenido = ejecutar(destino, etiqueta, direccion)
        if obtenido != esperado:
            raise AssertionError(f"{entrada}: se obtuvo {obtenido}, se esperaba {esperado}")
        print(f"OK {entrada}: {obtenido} ({pasos} instrucciones)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
