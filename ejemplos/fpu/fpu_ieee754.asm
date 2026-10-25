fpu_rechazar:
    CARGAR R0, fpu_nan
    GUARDAR R0, fpu_r
    CARGARINM R0, 1
    GUARDAR R0, fpu_estado
    RETORNAR

fpu_descomponer:
    CARGARINM R0, 0
    GUARDAR R0, fpu_estado
    CARGAR R0, fpu_a
    COMPARAR R0, R0
    CARGARINM R1, 1
    CARGARINM R2, 63
    DESP_I R1, R2
    PRUEBA R0, R1
    SALTA_NOZ fpu_da_invalido

fpu_da_cont:
    MOVER R1, R0
    CARGARINM R2, 52
    DESP_D R1, R2
    CARGARINM R3, 2047
    Y R1, R3
    GUARDAR R1, fpu_ea
    COMPARAR R1, R3
    SALTAZ fpu_da_invalido
    MOVER R4, R0
    CARGARINM R5, 0
    NO R5
    CARGARINM R6, 12
    DESP_D R5, R6
    Y R4, R5
    CARGARINM R6, 1
    CARGARINM R7, 52
    DESP_I R6, R7
    COMPARAR R1, R7
    CARGARINM R7, 0
    COMPARAR R1, R7
    SALTAZ fpu_da_cero
    O R4, R6
    GUARDAR R4, fpu_sa
    SALTAR fpu_db_inicio
fpu_da_cero:
    COMPARAR R4, R7
    SALTA_NOZ fpu_da_invalido
    GUARDAR R7, fpu_sa
    SALTAR fpu_db_inicio
fpu_da_invalido:
    CARGARINM R7, 1
    GUARDAR R7, fpu_estado

fpu_db_inicio:
    CARGAR R0, fpu_b
    CARGARINM R1, 1
    CARGARINM R2, 63
    DESP_I R1, R2
    PRUEBA R0, R1
    SALTA_NOZ fpu_db_invalido
fpu_db_cont:
    MOVER R1, R0
    CARGARINM R2, 52
    DESP_D R1, R2
    CARGARINM R3, 2047
    Y R1, R3
    GUARDAR R1, fpu_eb
    COMPARAR R1, R3
    SALTAZ fpu_db_invalido
    MOVER R4, R0
    CARGARINM R5, 0
    NO R5
    CARGARINM R6, 12
    DESP_D R5, R6
    Y R4, R5
    CARGARINM R6, 1
    CARGARINM R7, 52
    DESP_I R6, R7
    CARGARINM R7, 0
    COMPARAR R1, R7
    SALTAZ fpu_db_cero
    O R4, R6
    GUARDAR R4, fpu_sb
    RETORNAR
fpu_db_cero:
    COMPARAR R4, R7
    SALTA_NOZ fpu_db_invalido
    GUARDAR R7, fpu_sb
    RETORNAR
fpu_db_invalido:
    CARGARINM R7, 1
    GUARDAR R7, fpu_estado
    RETORNAR

fpu_desde_u64:
    CARGAR R0, fpu_a
    CARGARINM R1, 0
    COMPARAR R0, R1
    SALTAZ fpu_u64_cero
    MOVER R2, R0
    CARGARINM R1, 1
    CARGARINM R3, 0
fpu_u64_buscar:
    DESP_D R2, R1
    INCREMENTAR R3
    PRUEBA R2, R2
    SALTA_NOZ fpu_u64_buscar
    DECREMENTAR R3

    CARGARINM R4, 1
    DESP_I R4, R3
    MOVER R5, R0
    RESTAR R5, R4
    CARGARINM R6, 52
    RESTAR R6, R3
    DESP_I R5, R6
    CARGARINM R7, 1023
    SUMAR R7, R3
    CARGARINM R6, 52
    DESP_I R7, R6
    O R5, R7
    GUARDAR R5, fpu_r
    CARGARINM R0, 0
    GUARDAR R0, fpu_estado
    RETORNAR
fpu_u64_cero:
    GUARDAR R1, fpu_r
    GUARDAR R1, fpu_estado
    RETORNAR

fpu_sumar:
    LLAMAR fpu_descomponer
    CARGAR R0, fpu_estado
    SALTA_NOZ fpu_sumar_error
    CARGAR R0, fpu_sa
    CARGAR R1, fpu_sb
    PRUEBA R0, R0
    SALTAZ fpu_sumar_devolver_b
    PRUEBA R1, R1
    SALTAZ fpu_sumar_devolver_a
    CARGAR R0, fpu_ea
    CARGAR R1, fpu_eb
    COMPARAR R0, R1
    SALTAZ fpu_sumar_iguales
    SALTAN fpu_sumar_b_mayor
    MOVER R2, R0
    CARGAR R3, fpu_sa
    CARGAR R4, fpu_sb
    RESTAR R0, R1
    SALTAR fpu_sumar_alinear
fpu_sumar_b_mayor:
    MOVER R2, R1
    CARGAR R3, fpu_sb
    CARGAR R4, fpu_sa
    RESTAR R1, R0
    MOVER R0, R1
    SALTAR fpu_sumar_alinear
fpu_sumar_iguales:
    MOVER R2, R0
    CARGAR R3, fpu_sa
    CARGAR R4, fpu_sb
    CARGARINM R0, 0
fpu_sumar_alinear:
    PRUEBA R0, R0
    SALTAZ fpu_sumar_unir
    CARGARINM R1, 1
    DESP_D R4, R1
    DECREMENTAR R0
    SALTAR fpu_sumar_alinear
fpu_sumar_unir:
    SUMAR R3, R4
    CARGARINM R0, 1
    CARGARINM R1, 53
    DESP_I R0, R1
    PRUEBA R3, R0
    SALTA_NOZ fpu_sumar_llevo
    SALTAR fpu_sumar_empaquetar
fpu_sumar_llevo:
    CARGARINM R1, 1
    DESP_D R3, R1
    INCREMENTAR R2
fpu_sumar_empaquetar:
    CARGARINM R0, 1
    CARGARINM R1, 52
    DESP_I R0, R1
    RESTAR R3, R0
    DESP_I R2, R1
    O R3, R2
    GUARDAR R3, fpu_r
    RETORNAR
fpu_sumar_devolver_b:
    CARGAR R0, fpu_b
    GUARDAR R0, fpu_r
    RETORNAR
fpu_sumar_devolver_a:
    CARGAR R0, fpu_a
    GUARDAR R0, fpu_r
    RETORNAR
fpu_sumar_error:
    LLAMAR fpu_rechazar
    RETORNAR

fpu_restar:
    LLAMAR fpu_descomponer
    CARGAR R0, fpu_estado
    SALTA_NOZ fpu_restar_error
    CARGAR R0, fpu_sa
    CARGAR R1, fpu_sb
    PRUEBA R0, R0
    SALTAZ fpu_restar_b_negativo
    PRUEBA R1, R1
    SALTAZ fpu_restar_devolver_a
    CARGAR R0, fpu_ea
    CARGAR R1, fpu_eb
    COMPARAR R0, R1
    SALTAZ fpu_restar_exp_igual
    SALTAN fpu_restar_b_mayor
    CARGARINM R7, 0
    MOVER R2, R0
    CARGAR R3, fpu_sa
    CARGAR R4, fpu_sb
    RESTAR R0, R1
    SALTAR fpu_restar_alinear
fpu_restar_b_mayor:
    CARGARINM R7, 1
    CARGARINM R6, 63
    DESP_I R7, R6
    MOVER R2, R1
    CARGAR R3, fpu_sb
    CARGAR R4, fpu_sa
    RESTAR R1, R0
    MOVER R0, R1
    SALTAR fpu_restar_alinear
fpu_restar_exp_igual:
    CARGAR R3, fpu_sa
    CARGAR R4, fpu_sb
    COMPARAR R3, R4
    SALTAN fpu_restar_intercambiar
    CARGARINM R7, 0
    MOVER R2, R0
    CARGARINM R0, 0
    SALTAR fpu_restar_alinear
fpu_restar_intercambiar:
    CARGARINM R7, 1
    CARGARINM R6, 63
    DESP_I R7, R6
    INTERCAMBIAR R3, R4
    MOVER R2, R0
    CARGARINM R0, 0
fpu_restar_alinear:
    PRUEBA R0, R0
    SALTAZ fpu_restar_hacer
    CARGARINM R1, 1
    DESP_D R4, R1
    DECREMENTAR R0
    SALTAR fpu_restar_alinear
fpu_restar_hacer:
    RESTAR R3, R4
    CARGARINM R0, 0
    COMPARAR R3, R0
    SALTAZ fpu_restar_cero
    CARGARINM R1, 1
    CARGARINM R4, 52
    DESP_I R1, R4
fpu_restar_normalizar:
    PRUEBA R3, R1
    SALTA_NOZ fpu_restar_empacar
    DESP_I R3, R0
    ; R0 es cero aquí: cargar el desplazamiento uno.
    CARGARINM R0, 1
    DESP_I R3, R0
    DECREMENTAR R2
    CARGARINM R0, 0
    SALTAR fpu_restar_normalizar
fpu_restar_empacar:
    RESTAR R3, R1
    DESP_I R2, R4
    O R3, R2
    O R3, R7
    GUARDAR R3, fpu_r
    RETORNAR
fpu_restar_cero:
    CARGARINM R0, 0
    GUARDAR R0, fpu_r
    RETORNAR
fpu_restar_b_negativo:
    CARGAR R0, fpu_b
    CARGARINM R1, 1
    CARGARINM R2, 63
    DESP_I R1, R2
    O R0, R1
    GUARDAR R0, fpu_r
    RETORNAR
fpu_restar_devolver_a:
    CARGAR R0, fpu_a
    GUARDAR R0, fpu_r
    RETORNAR
fpu_restar_error:
    LLAMAR fpu_rechazar
    RETORNAR

fpu_multiplicar:
    LLAMAR fpu_descomponer
    CARGAR R0, fpu_estado
    SALTA_NOZ fpu_mul_error
    CARGAR R0, fpu_sa
    CARGAR R1, fpu_sb
    PRUEBA R0, R0
    SALTAZ fpu_mul_cero
    PRUEBA R1, R1
    SALTAZ fpu_mul_cero
    CARGAR R2, fpu_ea
    CARGAR R5, fpu_eb
    SUMAR R2, R5
    CARGARINM R5, 1023
    RESTAR R2, R5
    CARGARINM R3, 0
    CARGARINM R4, 0
    CARGARINM R5, 0
    MOVER R7, R5
    CARGARINM R5, 53
    GUARDAR R5, fpu_cuenta
fpu_mul_bucle:
    CARGARINM R6, 1
    PRUEBA R0, R6
    SALTAZ fpu_mul_no_sumar
    SUMAR R3, R1
    SUMAR_C R4, R7
fpu_mul_no_sumar:
    DESP_D R0, R6
    MOVER R6, R1
    CARGARINM R5, 63
    DESP_D R6, R5
    CARGARINM R5, 1
    DESP_I R7, R5
    O R7, R6
    DESP_I R1, R5
    CARGAR R5, fpu_cuenta
    DECREMENTAR R5
    GUARDAR R5, fpu_cuenta
    SALTA_NOZ fpu_mul_bucle
    MOVER R0, R4
    CARGARINM R1, 41
    DESP_D R0, R1
    CARGARINM R1, 1
    PRUEBA R0, R1
    SALTAZ fpu_mul_menos_dos
    CARGARINM R0, 11
    DESP_I R4, R0
    CARGARINM R1, 53
    DESP_D R3, R1
    O R4, R3
    INCREMENTAR R2
    SALTAR fpu_mul_empacar
fpu_mul_menos_dos:
    CARGARINM R0, 12
    DESP_I R4, R0
    CARGARINM R1, 52
    DESP_D R3, R1
    O R4, R3
fpu_mul_empacar:
    CARGARINM R0, 1
    CARGARINM R1, 52
    DESP_I R0, R1
    RESTAR R4, R0
    DESP_I R2, R1
    O R4, R2
    GUARDAR R4, fpu_r
    RETORNAR
fpu_mul_cero:
    CARGARINM R0, 0
    GUARDAR R0, fpu_r
    RETORNAR
fpu_mul_error:
    LLAMAR fpu_rechazar
    RETORNAR

fpu_dividir:
    LLAMAR fpu_descomponer
    CARGAR R0, fpu_estado
    SALTA_NOZ fpu_div_error
    CARGAR R0, fpu_sb
    PRUEBA R0, R0
    SALTAZ fpu_div_error
    CARGAR R0, fpu_sa
    PRUEBA R0, R0
    SALTAZ fpu_div_cero
    CARGAR R2, fpu_ea
    CARGAR R3, fpu_eb
    RESTAR R2, R3
    CARGARINM R3, 1023
    SUMAR R2, R3
    CARGAR R0, fpu_sa
    CARGAR R1, fpu_sb
    COMPARAR R0, R1
    SALTAN fpu_div_menor
    RESTAR R0, R1
    CARGARINM R3, 1
    CARGARINM R4, 52
    DESP_I R3, R4
    CARGARINM R5, 52
    MOVER R6, R3
    CARGARINM R7, 1
    DESP_D R6, R7
    SALTAR fpu_div_bucle
fpu_div_menor:
    DECREMENTAR R2
    CARGARINM R3, 0
    CARGARINM R4, 52
    CARGARINM R5, 53
    CARGARINM R6, 1
    DESP_I R6, R4
fpu_div_bucle:
    CARGARINM R7, 1
    DESP_I R0, R7
    COMPARAR R0, R1
    SALTAN fpu_div_sin_bit
    RESTAR R0, R1
    O R3, R6
fpu_div_sin_bit:
    DESP_D R6, R7
    DECREMENTAR R5
    SALTA_NOZ fpu_div_bucle
    DESP_I R0, R7
    COMPARAR R0, R1
    SALTAN fpu_div_empacar
    SALTAZ fpu_div_empate
    INCREMENTAR R3
    SALTAR fpu_div_revisar_llevo
fpu_div_empate:
    CARGARINM R4, 1
    PRUEBA R3, R4
    SALTAZ fpu_div_empacar
    INCREMENTAR R3
fpu_div_revisar_llevo:
    CARGARINM R4, 1
    CARGARINM R5, 53
    DESP_I R4, R5
    PRUEBA R3, R4
    SALTAZ fpu_div_empacar
    CARGARINM R4, 1
    DESP_D R3, R4
    INCREMENTAR R2
fpu_div_empacar:
    CARGARINM R4, 1
    CARGARINM R5, 52
    DESP_I R4, R5
    RESTAR R3, R4
    DESP_I R2, R5
    O R3, R2
    GUARDAR R3, fpu_r
    CARGARINM R0, 0
    GUARDAR R0, fpu_estado
    RETORNAR
fpu_div_cero:
    CARGARINM R0, 0
    GUARDAR R0, fpu_r
    GUARDAR R0, fpu_estado
    RETORNAR
fpu_div_error:
    LLAMAR fpu_rechazar
    RETORNAR

.ALINEAR 8
fpu_a:       .PALABRA 0
fpu_b:       .PALABRA 0
fpu_r:       .PALABRA 0
fpu_ea:      .PALABRA 0
fpu_eb:      .PALABRA 0
fpu_sa:      .PALABRA 0
fpu_sb:      .PALABRA 0
fpu_estado:  .PALABRA 0
fpu_cuenta:  .PALABRA 0
fpu_nan:     .PALABRA 0x7ff8000000000000
