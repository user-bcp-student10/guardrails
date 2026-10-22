"""Rol backend: edita aquí sus instrucciones y entregables."""

from graph.state import WorkflowState
from graph.context import _ctx, _runs, _const_block, _ronda, _feedback_block


INSTRUCTIONS = (
    "Eres un desarrollador backend senior. Implementa los servicios y endpoints del plan "
    "segun los contratos aprobados de Arquitectura y Datos, cuando participe. "
    "Respeta rutas, metodos HTTP, formatos de peticion y respuesta y codigos de estado del contrato de API. "
    "Valida las entradas y devuelve errores coherentes con ese contrato, sin exponer detalles internos. "
    "Define el acceso a datos y los limites de las transacciones, con commit y rollback ante errores. "
    "Conserva los datos existentes. Incluye un caso valido, un caso de error, sus resultados esperados "
    "y comandos reproducibles para comprobarlos. Marca NO EJECUTADO lo no comprobado. "
    "En las siguientes rondas incorpora todas las observaciones del Chapter. "
    "Devuelve los cambios con ### ruta/archivo.ext seguido de su bloque de codigo markdown.\n"
)


def backend_node(state: WorkflowState, invoke) -> dict:
    """
    Implementa los cambios de backend del plan.
    En rondas > 1 incorpora las observaciones del chapter.
    Se salta si project_type no incluye backend.
    Escribe en: out_backend
    """
    if not _runs(state, "backend"):
        print("[backend_node] project_type no incluye backend — saltando.")
        return {}

    print(f"[backend_node] Refactorizando backend (ronda {_ronda(state)})...")

    prompt = (INSTRUCTIONS + _const_block(state, "Respeta las restricciones del proyecto y la constitución.") + "\nRepositorio: " + state["repo_name"] + "\nPlan:\n" + _ctx(state.get("out_plan", ""),2500) + "\nCódigo original:\n" + _ctx(state.get("snapshot", ""),4000) + _feedback_block(state) + '\nPara código usa ### ruta/archivo.ext seguida de un bloque markdown.')
    if state.get("include_data"):
        prompt += "\nContrato aprobado de Datos y persistencia:\n" + _ctx(state.get("out_data", ""), 6000)
        prompt += (
            "\nImplementa el acceso a datos segun este contrato; consume el esquema y las migraciones "
            "de Datos sin duplicar ni regenerar sus migraciones. Conserva los datos existentes."
        )
    else:
        prompt += (
            "\nEn el equipo de seis tambien eres responsable de la persistencia: define el esquema "
            "y las migraciones necesarias segun el plan y las convenciones existentes, conservando "
            "los datos existentes. Incluye reversion o recuperacion y comprobaciones de integridad; "
            "si no se requieren cambios de persistencia, justificalo."
        )
    return {"out_backend": invoke(prompt)}
