"""Catálogo de permisos y roles base. Cada módulo agregará sus códigos al implementarse."""

PERMISSIONS: dict[str, str] = {
    "customers.read": "Ver clientes",
    "customers.create": "Crear clientes",
    "customers.update": "Editar clientes",
    "vehicles.read": "Ver vehículos",
    "vehicles.create": "Registrar vehículos",
    "vehicles.inspect": "Realizar inspecciones",
    "contracts.read": "Ver contratos",
    "contracts.create": "Crear contratos",
    "contracts.activate": "Activar contratos",
    "contracts.cancel": "Cancelar contratos",
    "billing.read": "Ver cobranza",
    "billing.retry": "Reintentar cobros",
    "billing.refund": "Solicitar reembolsos",
    "repairs.create": "Solicitar reparaciones",
    "repairs.diagnose": "Registrar diagnósticos",
    "repairs.quote": "Enviar presupuestos",
    "authorizations.approve_basic": "Autorizar servicios básicos",
    "authorizations.approve_major": "Autorizar motor y transmisión",
    "finance.read": "Ver finanzas",
    "finance.adjust": "Ajustes financieros",
    "finance.settle": "Liquidar a talleres",
    "organizations.read": "Ver organizaciones y sucursales",
    "organizations.manage": "Administrar organizaciones y sucursales",
    "franchises.manage": "Administrar franquicias",
    "users.manage": "Administrar usuarios y roles",
    "audit.read": "Consultar auditoría",
}

_ALL = list(PERMISSIONS)

# Los filtros "propios" / "asignados" se aplican dentro de cada módulo (nivel de registro).
ROLES: dict[str, tuple[str, list[str]]] = {
    "superadmin": ("Administrador global", _ALL),
    "corporate": (
        "Corporativo",
        [
            "customers.read", "customers.create", "customers.update",
            "vehicles.read", "vehicles.create", "vehicles.inspect",
            "contracts.read", "contracts.create", "contracts.activate", "contracts.cancel",
            "billing.read", "repairs.create", "repairs.diagnose", "repairs.quote",
            "authorizations.approve_basic", "authorizations.approve_major",
            "organizations.read", "organizations.manage", "users.manage",
        ],
    ),
    "finance": (
        "Finanzas",
        [
            "customers.read", "vehicles.read", "contracts.read",
            "billing.read", "billing.retry", "billing.refund",
            "finance.read", "finance.adjust", "finance.settle",
            "organizations.read", "audit.read",
        ],
    ),
    "workshop": (
        "Taller",
        [
            "customers.read", "vehicles.read", "vehicles.inspect", "contracts.read",
            "repairs.diagnose", "repairs.quote", "organizations.read",
        ],
    ),
    "customer": (
        "Cliente",
        ["customers.read", "vehicles.read", "contracts.read", "billing.read", "repairs.create"],
    ),
}
