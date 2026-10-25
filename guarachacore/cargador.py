from .ensamblador import ModuloObjeto
from .procesador import Procesador
class ErrorEnlace(ValueError): pass
class Enlazador:
    def enlazar(self, modulos:list[ModuloObjeto], origen:int=0)->bytes:
        tabla={}; inicios=[]; cursor=origen
        for modulo in modulos:
            inicios.append(cursor)
            for nombre,desplazamiento in modulo.simbolos.items():
                if nombre in tabla: raise ErrorEnlace(f"símbolo definido dos veces: {nombre}")
                tabla[nombre]=cursor+desplazamiento
            cursor+=len(modulo.codigo)
        imagen=bytearray().join(modulo.codigo for modulo in modulos)
        for modulo,inicio in zip(modulos,inicios):
            for reubicacion in modulo.reubicaciones:
                if reubicacion.simbolo not in tabla: raise ErrorEnlace(f"símbolo no definido: {reubicacion.simbolo}")
                donde=inicio-origen+reubicacion.desplazamiento; imagen[donde:donde+4]=tabla[reubicacion.simbolo].to_bytes(4,"big")
        return bytes(imagen)
class Cargador:
    def cargar(self, procesador:Procesador, imagen:bytes, direccion:int=0, fijar_pc:bool=True)->None:
        if direccion<0 or direccion+len(imagen)>len(procesador.memoria.ram.datos): raise MemoryError("el programa no cabe en RAM")
        procesador.memoria.escribir_bytes(direccion,imagen)
        if fijar_pc: procesador.PC=direccion; procesador.detenido=False
    def cargar_archivo(self,procesador:Procesador,nombre_archivo:str,direccion:int=0)->None:
        with open(nombre_archivo,"rb") as archivo: self.cargar(procesador,archivo.read(),direccion)
