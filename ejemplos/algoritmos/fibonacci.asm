
CARGARINM R1, 0      
CARGARINM R2, 1      
CARGARINM R3, 10     

bucle_fibonacci:
MOVER R4, R1         
SUMAR R4, R2         
MOVER R1, R2         
MOVER R2, R4         
DECREMENTAR R3       
SALTA_NOZ bucle_fibonacci

DETENER
