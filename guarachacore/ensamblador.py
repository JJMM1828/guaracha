from __future__ import annotations
from dataclasses import dataclass, field
import re
from .arquitectura import CODIGOS, Formato, codificar
@dataclass
class Reubicacion: desplazamiento: int; simbolo: str
@dataclass
class ModuloObjeto:
    codigo: bytearray; simbolos: dict[str,int]; reubicaciones: list[Reubicacion] = field(default_factory=list)
class ErrorEnsamblado(ValueError): pass
class Ensamblador:
    def ensamblar_archivo(self, nombre_archivo: str) -> ModuloObjeto:
        with open(nombre_archivo,encoding="utf-8") as archivo: return self.ensamblar(archivo.read())
    def ensamblar(self, fuente: str) -> ModuloObjeto:
        sentencias=[]; simbolos={}; posicion=0
        for numero, original in enumerate(fuente.splitlines(),1):
            linea=original.split(";",1)[0].split("#",1)[0].strip()
            if not linea: continue
            if ":" in linea:
                etiqueta,linea=linea.split(":",1); etiqueta=etiqueta.strip()
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",etiqueta) or etiqueta in simbolos: raise ErrorEnsamblado(f"línea {numero}: etiqueta inválida")
                simbolos[etiqueta]=posicion; linea=linea.strip()
                if not linea: continue
            partes=re.split(r"\s+",linea,maxsplit=1); instruccion=partes[0].upper(); argumentos=[x.strip() for x in partes[1].split(",")] if len(partes)==2 else []
            if instruccion==".BYTE": tamano=len(argumentos)
            elif instruccion==".PALABRA": tamano=8*len(argumentos)
            elif instruccion==".ALINEAR":
                if len(argumentos) != 1: raise ErrorEnsamblado(f"línea {numero}: .ALINEAR requiere un múltiplo")
                multiplo = self._numero(argumentos[0])
                if multiplo <= 0: raise ErrorEnsamblado(f"línea {numero}: el múltiplo debe ser positivo")
                tamano = (-posicion) % multiplo
            elif instruccion in CODIGOS: tamano=CODIGOS[instruccion].formato.value
            else: raise ErrorEnsamblado(f"línea {numero}: instrucción desconocida: {instruccion}")
            sentencias.append((numero,instruccion,argumentos)); posicion+=tamano
        codigo=bytearray(); reubicaciones=[]
        for numero,instruccion,args in sentencias:
            try:
                if instruccion==".BYTE": codigo.extend(self._numero(x)&255 for x in args); continue
                if instruccion==".PALABRA":
                    for x in args: codigo.extend((self._numero(x)&((1<<64)-1)).to_bytes(8,"little"))
                    continue
                if instruccion==".ALINEAR":
                    multiplo = self._numero(args[0])
                    codigo.extend(b"\0" * ((-len(codigo)) % multiplo))
                    continue
                dato=CODIGOS[instruccion]; operandos,simbolo=self._operandos(instruccion,dato.formato,args); inicio=len(codigo); codigo.extend(codificar(instruccion,operandos))
                if simbolo: reubicaciones.append(Reubicacion(inicio+(1 if dato.formato is Formato.F4 else 2),simbolo))
            except ValueError as error: raise ErrorEnsamblado(f"línea {numero}: {error}") from error
        return ModuloObjeto(codigo,simbolos,reubicaciones)
    def _operandos(self,nombre:str,formato:Formato,args:list[str])->tuple[list[int],str|None]:
        if formato is Formato.F1:
            if args: raise ValueError(f"{nombre} no recibe operandos")
            return [],None
        if formato is Formato.F2:
            if len(args) not in (1,2): raise ValueError(f"{nombre} requiere uno o dos registros")
            return [self._registro(args[0]),self._registro(args[1]) if len(args)==2 else 0],None
        if formato is Formato.F3:
            if len(args) not in (1,2): raise ValueError(f"{nombre} requiere registro y puerto")
            return [self._registro(args[0]),self._numero(args[1]) if len(args)==2 else 0],None
        if formato is Formato.F4:
            if len(args)!=1: raise ValueError(f"{nombre} requiere una dirección")
            valor,simbolo=self._valor_simbolo(args[0]); return [valor],simbolo
        if nombre in {"EMPUJAR","SACAR"} and len(args)==1: return [self._registro(args[0]),0],None
        if len(args)!=2: raise ValueError(f"{nombre} requiere registro y valor/dirección")
        valor,simbolo=self._valor_simbolo(args[1].strip("[]")); return [self._registro(args[0]),valor],simbolo
    @staticmethod
    def _registro(texto:str)->int:
        coincidencia=re.fullmatch(r"R(1[0-5]|[0-9])",texto.upper())
        if not coincidencia: raise ValueError(f"registro inválido: {texto}")
        return int(coincidencia.group(1))
    @staticmethod
    def _numero(texto:str)->int: return int(texto.strip(),0)
    def _valor_simbolo(self,texto:str)->tuple[int,str|None]:
        try: return self._numero(texto),None
        except ValueError:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",texto): raise ValueError(f"valor o etiqueta inválido: {texto}")
            return 0,texto
