inicio_heron:
    CARGARINM R0, 2
    GUARDAR R0, fpu_a
    LLAMAR fpu_desde_u64
    CARGAR R0, fpu_r
    GUARDAR R0, heron_x

    CARGARINM R0, 1
    GUARDAR R0, fpu_a
    LLAMAR fpu_desde_u64
    CARGAR R0, fpu_r
    GUARDAR R0, heron_y

heron_iteracion:
    ; cociente = x / y_i
    CARGAR R0, heron_x
    GUARDAR R0, fpu_a
    CARGAR R0, heron_y
    GUARDAR R0, fpu_b
    LLAMAR fpu_dividir
    CARGAR R0, fpu_r
    GUARDAR R0, heron_cociente

    ; y_(i+1) = (y_i + cociente) / 2
    CARGAR R0, heron_y
    GUARDAR R0, fpu_a
    CARGAR R0, heron_cociente
    GUARDAR R0, fpu_b
    LLAMAR fpu_sumar
    CARGAR R0, fpu_r
    GUARDAR R0, heron_suma
    CARGARINM R0, 2
    GUARDAR R0, fpu_a
    LLAMAR fpu_desde_u64
    CARGAR R0, fpu_r
    GUARDAR R0, fpu_b
    CARGAR R0, heron_suma
    GUARDAR R0, fpu_a
    LLAMAR fpu_dividir
    CARGAR R0, fpu_r
    GUARDAR R0, heron_y
    CARGAR R7, heron_iteraciones
    DECREMENTAR R7
    GUARDAR R7, heron_iteraciones
    SALTA_NOZ heron_iteracion

    CARGAR R0, heron_y
    GUARDAR R0, heron_resulto
    DETENER

.ALINEAR 8
heron_x:        .PALABRA 0
heron_y:        .PALABRA 0
heron_cociente: .PALABRA 0
heron_suma:     .PALABRA 0
heron_resulto:   .PALABRA 0
heron_iteraciones: .PALABRA 8
