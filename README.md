# mac-system-dashboard

Dashboard web local para consultar el estado de este Mac bajo demanda. Muestra métricas reales de CPU, memoria, disco, batería y procesos, sin enviar información a servicios externos.

## Qué incluye

- Tarjetas de estado para CPU, memoria, disco y batería.
- Gráficas de uso reciente de CPU y memoria, actualizadas automáticamente.
- Tabla de procesos ordenada por consumo, con búsqueda por nombre.
- Finalización normal o forzada de procesos, siempre con confirmación.
- Protección frente a procesos esenciales de macOS y frente al propio servicio.
- Interfaz adaptada a pantallas de escritorio y móvil.

## Requisitos

- macOS.
- Python 3.10 o posterior.
- Node.js 20 o posterior y npm.

No requiere una base de datos ni un servicio en la nube.

## Instalación inicial

Desde la carpeta raíz del proyecto, crea o activa el entorno virtual de Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

El servicio no usa dependencias externas de Python. Instala las dependencias del dashboard una sola vez:

```bash
cd frontend
npm install
```

## Arranque bajo demanda

Primero compila el dashboard para que el servicio Python pueda entregarlo:

```bash
cd frontend
npm run build
```

Después, desde la raíz del proyecto, inicia el servicio:

```bash
.venv/bin/python backend/app.py
```

Abre la dirección local que muestra la terminal. El servicio solo escucha en el propio Mac; para detenerlo basta con pulsar `Control + C` en esa terminal.

## Desarrollo de la interfaz

Para trabajar en React con recarga automática, inicia el servicio Python y, en otra terminal:

```bash
cd frontend
npm run dev
```

El servidor de desarrollo redirige las solicitudes de métricas y procesos al servicio local.

## Arquitectura

```text
frontend/        React + TypeScript + Vite
  src/           Componentes, gráficas y estilos del dashboard
backend/         Servicio local de Python
  app.py         Métricas de macOS, API y control seguro de procesos
backend/static/  Dashboard compilado; se genera al ejecutar npm run build
```

El servicio usa herramientas disponibles en macOS, como `vm_stat`, `sysctl`, `pmset` y `ps`, para recopilar datos. Conserva las muestras recientes solo en memoria mientras está abierto.

## API local

Estas rutas solo están disponibles desde el propio ordenador:

| Ruta | Uso |
| --- | --- |
| `GET /api/overview` | Estado actual de CPU, memoria, disco y batería. |
| `GET /api/history` | Muestras recientes para las gráficas. |
| `GET /api/processes` | Lista de procesos ordenada por consumo. |
| `POST /api/processes/:pid/terminate` | Solicita el cierre normal de un proceso. |
| `POST /api/processes/:pid/force` | Solicita el cierre forzado de un proceso. |

## Seguridad al gestionar procesos

Finalizar un proceso puede cerrar una aplicación y causar pérdida de trabajo no guardado. Por ello, la interfaz siempre solicita confirmación y el servicio impide actuar sobre procesos críticos conocidos de macOS, el proceso principal del sistema y el propio dashboard.

Algunos procesos pueden requerir permisos adicionales de macOS. En ese caso, el dashboard informa de que no tiene autorización suficiente y no intenta elevar privilegios automáticamente.

## Verificación

Antes de publicar cambios, ejecuta:

```bash
cd frontend
npm run build
cd ..
.venv/bin/python -m py_compile backend/app.py
```

## Git

El proyecto incluye reglas para no versionar el entorno virtual de Python, dependencias de Node, archivos de compilación ni artefactos temporales. Mantén los cambios de código y documentación bajo control de versiones con Git.
