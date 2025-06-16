# API de Consulta RNC

Esta API permite consultar información de empresas a partir del archivo DGII_RNC.TXT.

## Requisitos

- Python 3.7+
- Dependencias listadas en `requirements.txt`
- Archivo DGII_RNC.TXT en el directorio raíz

## Instalación

1. Crear un entorno virtual (opcional pero recomendado):
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

1. Asegúrate de que el archivo `DGII_RNC.TXT` esté en el directorio raíz del proyecto
2. Iniciar el servidor:
```bash
python main.py
```

3. La API estará disponible en `http://localhost:8000`

## Endpoints

### 1. Consultar por RNC
- **GET** `/consultar-rnc/{rnc}`
- Consulta la información de una empresa por su RNC

### 2. Listar Empresas
- **GET** `/listar-empresas/`
- Parámetros opcionales:
  - `estado`: Filtrar por estado
  - `situacion`: Filtrar por situación
  - `skip`: Número de registros a saltar (paginación)
  - `limit`: Número máximo de registros a mostrar

### 3. Estados Disponibles
- **GET** `/estados-disponibles/`
- Lista todos los estados disponibles en el sistema

### 4. Situaciones Disponibles
- **GET** `/situaciones-disponibles/`
- Lista todas las situaciones disponibles en el sistema

## Documentación

La documentación interactiva de la API está disponible en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 