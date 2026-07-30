# Contribuir a mac-system-dashboard

Gracias por contribuir. Este proyecto es un dashboard local para macOS: la privacidad, la seguridad de procesos y la compatibilidad nativa son requisitos fundamentales.

## Antes de empezar

1. Crea una rama para cada cambio.
2. Mantén los cambios pequeños y explicables.
3. No incluyas credenciales, archivos `.env`, datos de procesos ni capturas con información privada.

## Desarrollo y comprobaciones

Ejecuta las pruebas y la compilación antes de abrir una propuesta:

```bash
cd frontend
npm test -- --run
npm run build
cd ..
.venv/bin/python -m py_compile backend/app.py
.venv/bin/python -m unittest discover -s backend -p 'test_*.py'
```

## Reglas del proyecto

- El backend debe seguir escuchando solo en `127.0.0.1`.
- No se permite telemetría ni envío de métricas fuera del Mac.
- Las acciones sobre procesos requieren confirmación explícita y no pueden aplicarse en lote.
- El backend de métricas permanece nativo de macOS; Docker solo cubre la interfaz.
- Conserva la compatibilidad con configuraciones regionales de macOS, incluidas comas decimales.

## Propuestas de cambio

Explica qué problema resuelves, cómo lo has probado y cualquier impacto sobre privacidad o seguridad. Las contribuciones se distribuyen bajo la GPLv3 del repositorio.
