# Contexto para asistentes

## Objetivo

`mac-system-dashboard` es un dashboard web local para un único Mac. Se arranca solo cuando el usuario lo solicita y muestra CPU, memoria, disco, batería y procesos. También puede solicitar el cierre de procesos tras confirmación explícita del usuario en la interfaz.

No debe enviar telemetría, métricas ni datos de procesos fuera de `localhost`.

## Arquitectura y ficheros principales

- `backend/app.py`: servicio Python estándar que recopila métricas de macOS, expone la API local y sirve la versión compilada de la interfaz.
- `frontend/src/main.tsx`: composición de la interfaz React, estado, consultas a la API, búsqueda y confirmación de acciones sobre procesos.
- `frontend/src/styles.css`: sistema visual y diseño adaptable.
- `frontend/vite.config.ts`: configuración de Vite; redirige `/api` al servicio durante el desarrollo y compila en `backend/static`.
- `frontend/package.json`: dependencias y comandos del dashboard.
- `README.md`: instrucciones de instalación, uso y API para personas usuarias.

`backend/static/` es una salida de compilación y no se versiona. `node_modules/` y `.venv/` tampoco se versionan.

## Comandos habituales

```bash
# Activar Python
source .venv/bin/activate

# Instalar dependencias del panel (solo cuando cambien)
cd frontend && npm install

# Compilar el panel para el servicio Python
cd frontend && npm run build

# Iniciar la aplicación local desde la raíz
.venv/bin/python backend/app.py

# Desarrollo del panel con recarga automática
cd frontend && npm run dev
```

## Datos de macOS

El backend usa `sysctl`, `vm_stat`, `pmset` y `ps`. Mantener estas llamadas compatibles con macOS y evitar añadir dependencias Python si no son necesarias.

La batería puede no estar disponible en equipos sin batería. Mostrar un estado claro en la interfaz en vez de inventar un valor.

## Contenedor

El contenedor cubre la interfaz React y sus pruebas. No mover `backend/app.py` al contenedor: Docker Desktop ejecuta contenedores Linux y no puede acceder de forma fiable a las métricas ni a los procesos de macOS. El contenedor usa `host.docker.internal` para conectar con el servicio Python nativo.

El acceso mediante Docker puede protegerse con autenticación básica usando `DASHBOARD_AUTH_USER` y `DASHBOARD_AUTH_PASSWORD` desde un archivo `.env` local. Nunca versionar credenciales ni registrar la contraseña en la salida de comandos.

## Seguridad de procesos

- Mantener el servicio escuchando únicamente en `127.0.0.1`.
- No ejecutar comandos con privilegios elevados ni solicitar permisos automáticamente.
- Conservar la confirmación en la interfaz antes de terminar o forzar un proceso.
- Mantener protegidos los procesos esenciales de macOS y el propio proceso del dashboard.
- No añadir funciones que cierren procesos por lotes o de forma automática sin una petición explícita del usuario.

## Comprobaciones antes de entregar cambios

```bash
cd frontend && npm run build
cd frontend && npm test
cd .. && .venv/bin/python -m py_compile backend/app.py
cd .. && .venv/bin/python -m unittest discover -s backend -p 'test_*.py'
```

Verificar también en el navegador que se muestran métricas reales, que el filtro de procesos funciona y que las acciones piden confirmación. No finalizar procesos reales durante pruebas salvo petición explícita del usuario.
