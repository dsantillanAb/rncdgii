from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import csv
from typing import List, Optional, Dict
from collections import defaultdict

app = FastAPI(title="API de Consulta RNC")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las origenes
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)

# Variable global para almacenar los datos
datos_rnc = []

def cargar_archivo_dgii():
    global datos_rnc
    try:
        with open('DGII_RNC.TXT', 'r', encoding='latin1') as archivo:
            lector = csv.reader(archivo, delimiter='|')
            for fila in lector:
                if len(fila) >= 11:  # Asegurarse de que la fila tenga suficientes columnas
                    registro = {
                        'rnc': fila[0].strip(),
                        'razon_social': fila[1].strip(),
                        'nombre_comercial': fila[2].strip(),
                        'actividad_economica': fila[3].strip(),
                        'direccion': fila[4].strip(),
                        'numero': fila[5].strip(),
                        'urbanizacion': fila[6].strip(),
                        'telefono': fila[7].strip(),
                        'fecha_registro': fila[8].strip(),
                        'estado': fila[9].strip(),
                        'situacion': fila[10].strip()
                    }
                    datos_rnc.append(registro)
        return True
    except Exception as e:
        print(f"Error al cargar el archivo: {str(e)}")
        return False

@app.on_event("startup")
async def startup_event():
    cargar_archivo_dgii()

@app.get("/consultar-rnc/{rnc}")
async def consultar_rnc(rnc: str):
    if not datos_rnc:
        return JSONResponse(
            status_code=400,
            content={"error": "No se pudo cargar el archivo de datos"}
        )
    
    for registro in datos_rnc:
        if registro['rnc'] == rnc:
            return registro
    
    return JSONResponse(
        status_code=404,
        content={"error": "RNC no encontrado"}
    )

@app.get("/consultar-razon-social/{razon_social}")
async def consultar_razon_social(razon_social: str):
    if not datos_rnc:
        return JSONResponse(
            status_code=400,
            content={"error": "No se pudo cargar el archivo de datos"}
        )
    
    # Buscar coincidencias parciales en razón social
    resultados = []
    razon_social = razon_social.upper()
    for registro in datos_rnc:
        if razon_social in registro['razon_social'].upper():
            resultados.append(registro)
    
    if not resultados:
        return JSONResponse(
            status_code=404,
            content={"error": "No se encontraron empresas con esa razón social"}
        )
    
    return resultados

@app.get("/listar-empresas/")
async def listar_empresas(
    estado: Optional[str] = None,
    situacion: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    if not datos_rnc:
        return JSONResponse(
            status_code=400,
            content={"error": "No se pudo cargar el archivo de datos"}
        )
    
    # Filtrar por estado y situación si se proporcionan
    resultado = datos_rnc
    if estado:
        resultado = [r for r in resultado if r['estado'].upper() == estado.upper()]
    if situacion:
        resultado = [r for r in resultado if r['situacion'].upper() == situacion.upper()]
    
    # Aplicar paginación
    total = len(resultado)
    resultado = resultado[skip:skip + limit]
    
    return {
        "total": total,
        "mostrando": len(resultado),
        "datos": resultado
    }

@app.get("/estados-disponibles/")
async def estados_disponibles():
    if not datos_rnc:
        return JSONResponse(
            status_code=400,
            content={"error": "No se pudo cargar el archivo de datos"}
        )
    
    estados = list(set(registro['estado'] for registro in datos_rnc))
    return {"estados": estados}

@app.get("/situaciones-disponibles/")
async def situaciones_disponibles():
    if not datos_rnc:
        return JSONResponse(
            status_code=400,
            content={"error": "No se pudo cargar el archivo de datos"}
        )
    
    situaciones = list(set(registro['situacion'] for registro in datos_rnc))
    return {"situaciones": situaciones}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 