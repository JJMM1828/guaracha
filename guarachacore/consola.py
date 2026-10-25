import argparse
from .ensamblador import Ensamblador
from .procesador import Procesador
from .cargador import Cargador, Enlazador
from .memoria import JerarquiaMemoria
def crear_argumentos() -> argparse.ArgumentParser:
    argumentos=argparse.ArgumentParser(description="Guarachacore: computador educativo de 64 bits")
    argumentos.add_argument("fuente",nargs="*",help="uno o más archivos ensamblador, enlazados en el orden indicado")
    argumentos.add_argument("--binario",help="archivo de código máquina"); argumentos.add_argument("--direccion",type=lambda x:int(x,0),default=0)
    argumentos.add_argument("--ejecutar",action="store_true"); argumentos.add_argument("--paso",action="store_true")
    argumentos.add_argument("--bits",action="append",metavar="DIR:BIT:CADENA"); argumentos.add_argument("--memoria",type=int,default=64*1024)
    argumentos.add_argument("--red",metavar="ANFITRION:PUERTO"); return argumentos
def mostrar(procesador:Procesador)->None:
    estado=procesador.estado(); print(" ".join(f"R{i}={valor:016X}" for i,valor in enumerate(estado["R"])))
    print(" ".join(f"{clave}={estado[clave]:016X}" for clave in ("PC","IR","SP","BP","PSW","CR")))
def principal(argumentos_entrada:list[str]|None=None)->int:
    args=crear_argumentos().parse_args(argumentos_entrada); procesador=Procesador(JerarquiaMemoria(args.memoria)); cargador=Cargador()
    if args.red:
        anfitrion,puerto=args.red.rsplit(":",1); procesador.dispositivos.configurar_red(anfitrion,int(puerto))
    for edicion in args.bits or []:
        direccion,bit,cadena=edicion.split(":",2); procesador.memoria.escribir_bits(int(direccion,0),int(bit,0),cadena)
    if args.fuente:
        modulos=[Ensamblador().ensamblar_archivo(fuente) for fuente in args.fuente]
        cargador.cargar(procesador,Enlazador().enlazar(modulos,args.direccion),args.direccion)
    elif args.binario: cargador.cargar_archivo(procesador,args.binario,args.direccion)
    if args.paso:
        while not procesador.detenido:
            resultado=procesador.paso(); print(f"{resultado.pc:08X}: {resultado.instruccion} {resultado.operandos}"); mostrar(procesador)
            if not procesador.detenido: input("Enter para continuar…")
    elif args.ejecutar: print(f"Instrucciones ejecutadas: {procesador.ejecutar()}"); mostrar(procesador)
    else: crear_argumentos().print_help()
    return 0
