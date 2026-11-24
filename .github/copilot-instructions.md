# Instrucciones para GitHub Copilot Chat

Antes de escribir código, sigue esta escalera para evitar sobreconstruir:

1. ¿Esto necesita existir? Si no, no lo escribas (YAGNI).
2. ¿Ya existe en el proyecto? Reutilízalo, no lo reescribas.
3. ¿Lo hace el runtime o la biblioteca estándar? Úsalos.
4. ¿Lo hace la plataforma? Aprovecha esa funcionalidad.
5. ¿Ya hay una dependencia instalada que lo haga? Úsala.
6. ¿Una línea basta? Escribe una línea.
7. Solo entonces implementa el mínimo que funcione.

La simplicidad nunca justifica saltarse validación de entradas, manejo correcto
de datos, seguridad ni accesibilidad. Mantén comentarios, nombres y textos de
usuario en español. Para detalles del monorepo (`backend/` FastAPI, `frontend/`
Flutter Web), reglas de negocio (`NUMERIC(14,2)`, `service.py`, RBAC) y
comandos de verificación (`pytest -q`, `flutter analyze`, `flutter test`),
consulta `AGENTS.md`.
