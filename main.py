from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import csv
from typing import List, Optional, Dict
from collections import defaultdict
import aiohttp
import io
import asyncio
import ssl
import certifi
import logging
import os
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API de Consulta RNC")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)

# Montar archivos estáticos desde el directorio actual
app.mount("/static", StaticFiles(directory="."), name="static")

# Variable global para almacenar los datos
datos_rnc = []

async def cargar_archivo_desde_url():
    global datos_rnc
    datos_rnc = []  # Limpiar datos existentes
    try:
        # Configurar el contexto SSL con certificados verificados
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        logger.info("Iniciando descarga del archivo desde kuentaerp.com...")
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get('https://kuentaerp.com/rnc/DGII_RNC.TXT') as response:
                if response.status == 200:
                    logger.info("Archivo descargado exitosamente, procesando datos...")
                    # Leer el contenido del archivo como bytes
                    contenido_bytes = await response.read()
                    
                    # Intentar diferentes codificaciones
                    codificaciones = ['latin1', 'cp1252', 'iso-8859-1', 'utf-8']
                    contenido = None
                    
                    for codificacion in codificaciones:
                        try:
                            contenido = contenido_bytes.decode(codificacion)
                            logger.info(f"Archivo decodificado exitosamente usando {codificacion}")
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if contenido is None:
                        raise Exception("No se pudo decodificar el archivo con ninguna codificación conocida")
                    
                    # Procesar el contenido como CSV
                    lector = csv.reader(io.StringIO(contenido), delimiter='|')
                    contador = 0
                    for fila in lector:
                        if len(fila) >= 11:
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
                            contador += 1
                            if contador % 10000 == 0:
                                logger.info(f"Procesados {contador} registros...")
                    
                    logger.info(f"Carga completada. Total de registros: {len(datos_rnc)}")
                    return True
                else:
                    error_msg = f"Error al descargar el archivo: {response.status}"
                    logger.error(error_msg)
                    return False
    except Exception as e:
        error_msg = f"Error al cargar el archivo: {str(e)}"
        logger.error(error_msg)
        return False

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando la aplicación...")
    success = await cargar_archivo_desde_url()
    if not success:
        logger.error("No se pudieron cargar los datos al inicio")

# Cargar el archivo HTML
def get_html_content():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error al leer index.html: {e}")
        return None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = get_html_content()
    if html_content:
        return html_content
    raise HTTPException(status_code=500, detail="Error al cargar la página")

@app.get("/index.html", response_class=HTMLResponse)
async def read_index():
    return await read_root()

@app.get("/test")
async def test():
    return {"status": "ok", "datos_cargados": len(datos_rnc)}

@app.get("/consultar-rnc/{rnc}")
async def consultar_rnc(rnc: str):
    if not datos_rnc:
        logger.error("No hay datos cargados en memoria")
        raise HTTPException(status_code=400, detail="No se pudo cargar el archivo de datos")
    
    logger.info(f"Buscando RNC: {rnc}")
    for registro in datos_rnc:
        if registro['rnc'] == rnc:
            logger.info(f"RNC encontrado: {rnc}")
            return registro
    
    logger.warning(f"RNC no encontrado: {rnc}")
    raise HTTPException(status_code=404, detail="RNC no encontrado")

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
        raise HTTPException(status_code=400, detail="No se pudo cargar el archivo de datos")
    
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
        raise HTTPException(status_code=400, detail="No se pudo cargar el archivo de datos")
    
    estados = list(set(registro['estado'] for registro in datos_rnc))
    return {"estados": estados}

@app.get("/situaciones-disponibles/")
async def situaciones_disponibles():
    if not datos_rnc:
        raise HTTPException(status_code=400, detail="No se pudo cargar el archivo de datos")
    
    situaciones = list(set(registro['situacion'] for registro in datos_rnc))
    return {"situaciones": situaciones}

@app.get("/recargar-datos")
async def recargar_datos():
    success = await cargar_archivo_desde_url()
    if success:
        return {"mensaje": "Datos recargados exitosamente", "total_registros": len(datos_rnc)}
    raise HTTPException(status_code=500, detail="Error al recargar los datos")

if __name__ == "__main__":
    import uvicorn
    # Configuración para ejecutar en localhost
    uvicorn.run(app, host="127.0.0.1", port=8000) 