inicio_brun:
    CARGARINM R0, 0
    GUARDAR R0, brun_suma
    CARGARINM R1, 3
brun_bucle:
    CARGAR R2, brun_limite
    COMPARAR R1, R2
    SALTAN brun_probar
    SALTAZ brun_probar
    SALTAR brun_fin
brun_probar:
    GUARDAR R1, brun_n
    GUARDAR R1, brun_candidato
    LLAMAR brun_es_primo
    CARGAR R0, brun_primo
    PRUEBA R0, R0
    SALTAZ brun_siguiente
    CARGAR R3, brun_candidato
    CARGARINM R4, 2
    SUMAR R3, R4
    GUARDAR R3, brun_n
    LLAMAR brun_es_primo
    CARGAR R0, brun_primo
    PRUEBA R0, R0
    SALTAZ brun_siguiente

    CARGAR R0, brun_candidato
    GUARDAR R0, fpu_a
    LLAMAR fpu_desde_u64
    CARGAR R0, fpu_r
    GUARDAR R0, fpu_b
    CARGARINM R0, 1
    GUARDAR R0, fpu_a
    LLAMAR fpu_desde_u64
    CARGAR R0, fpu_r
    GUARDAR R0, fpu_a
    LLAMAR fpu_dividir
    CARGAR R0, fpu_r
    GUARDAR R0, brun_termino
    CARGAR R3, brun_n
    GUARDAR R3, fpu_a
    LLAMAR fpu_desde_u64
    CARGAR R0, fpu_r
    GUARDAR R0, fpu_b
    CARGARINM R0, 1
    GUARDAR R0, fpu_a
    LLAMAR fpu_desde_u64
    CARGAR R0, fpu_r
    GUARDAR R0, fpu_a
    LLAMAR fpu_dividir
    CARGAR R0, fpu_r
    GUARDAR R0, fpu_b
    CARGAR R0, brun_termino
    GUARDAR R0, fpu_a
    LLAMAR fpu_sumar
    CARGAR R0, fpu_r
    GUARDAR R0, fpu_b
    CARGAR R0, brun_suma
    GUARDAR R0, fpu_a
    LLAMAR fpu_sumar
    CARGAR R0, fpu_r
    GUARDAR R0, brun_suma
brun_siguiente:
    CARGAR R1, brun_candidato
    CARGARINM R0, 2
    SUMAR R1, R0
    SALTAR brun_bucle
brun_fin:
    CARGAR R0, brun_suma
    GUARDAR R0, brun_resultado
    DETENER


brun_es_primo:
    CARGAR R0, brun_n
    CARGARINM R1, 3
brun_divisor:
    MOVER R2, R1
    MULTIPLICAR R2, R1
    COMPARAR R2, R0
    SALTAN brun_dividir_n
    SALTAZ brun_compuesto
    CARGARINM R2, 1
    GUARDAR R2, brun_primo
    RETORNAR
brun_dividir_n:
    MOVER R2, R0
    MODULO R2, R1
    PRUEBA R2, R2
    SALTAZ brun_compuesto
    CARGARINM R2, 2
    SUMAR R1, R2
    SALTAR brun_divisor
brun_compuesto:
    CARGARINM R2, 0
    GUARDAR R2, brun_primo
    RETORNAR

.ALINEAR 8
brun_limite:    .PALABRA 1000
brun_n:         .PALABRA 0
brun_candidato: .PALABRA 0
brun_primo:     .PALABRA 0
brun_termino:   .PALABRA 0
brun_suma:      .PALABRA 0
brun_resultado: .PALABRA 0
