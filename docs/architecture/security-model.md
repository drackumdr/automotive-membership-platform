# Modelo de seguridad (TASK-002)

## Autenticación
- Contraseñas: Argon2id (argon2-cffi), mínimo 10 caracteres.
- Acceso: JWT HS256 de 15 min (algoritmo fijo en código; claims `sub`, `sid`, `jti`, `exp`).
- Renovación: token opaco aleatorio, solo se guarda su SHA-256. **Rotación** en cada uso; si se reutiliza uno ya rotado se revocan todas las sesiones del usuario (`refresh_reuse_detected`).
- Cada petición valida que la sesión (`sid`) siga vigente: logout, cambio de contraseña, desactivación o cambio de roles tienen efecto inmediato.
- Bloqueo temporal tras 5 intentos fallidos (15 min). Mensaje de error idéntico para usuario inexistente, clave errónea, cuenta bloqueada o desactivada.
- `JWT_SECRET` es obligatorio (≥ 32 caracteres) y nunca está en el repositorio.

## Autorización (RBAC con alcance)
- Permisos como códigos (`customers.read`, `users.manage`, …) agrupados en roles: superadmin, corporate, finance, workshop, customer.
- Un rol se asigna a un usuario **en una organización** (`user_roles.organization_id`); el alcance incluye las organizaciones descendientes. `NULL` = global (solo superadmin).
- Recursos fuera de alcance responden **404** (no se revela su existencia); falta de permiso responde **403** y queda auditado (`access_denied`).
- Sin escalamiento: nadie puede asignar un rol con permisos que no posee en ese alcance.
- Las reglas de fila ("clientes propios", "reparaciones asignadas") se implementan en cada módulo al crearlo.

## Auditoría
Tabla `audit_logs`: login correcto/fallido/bloqueado, logout, reutilización de token, cambio de contraseña, altas y cambios de usuarios, roles y organizaciones, accesos denegados.

## Pendiente
- Envío real del correo de recuperación (integrations/email).
- Límite de peticiones por IP en Nginx/aplicación.
- Separación de funciones en liquidaciones (quien aprueba no liquida) → Sprint 5/6.
