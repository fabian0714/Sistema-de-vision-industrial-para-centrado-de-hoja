Resumen

Sistema de Visión Artificial para informar el Centrado de Hoja del vidrio, es una solución de automatización y control de calidad 
industrial diseñada para entornos de manufactura. Utilizando un arreglo de cámaras duales y procesamiento de imágenes en tiempo real 
con Python y OpenCV, el sistema detecta marcadores ArUco para estimación espacial, calcula dimensiones precisas en milímetros, 
evalúa tolerancias operativas mediante alertas acústicas y mantiene un registro histórico de auditoría en archivos estructurados (CSV).

Adquisición de Imagen: Inicialización dual de cámaras industriales MVSDK, captura de fotogramas simultáneos (Izquierda/Derecha) y lectura 
directa del marcador ArUco para fijación de la escala.

Procesamiento de Imagen: Ajuste interactivo de tolerancias mediante trackbars, conversión de espacio de color de RGB a HSV y 
segmentación de imágenes por máscaras de umbralización.

Análisis y Cálculo Dimensional: Detección de contornos máximos, extracción del rectángulo delimitador (boundingRect), cálculo de la 
separación geométrica en píxeles y conversión al Ancho Bruto en milímetros.

Control y Registro Industrial: Comprobación en tiempo real de tolerancias (detección de Ampliación / Reducción), activación de alarma 
acústica (winsound), auditoría periódica segundo a segundo en archivo base.csv y despliegue del Live Feed concatenado en la interfaz visual.
