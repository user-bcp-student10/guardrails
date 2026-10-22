"""Rol chapter: edita aquí sus instrucciones y entregables."""

from graph.state import WorkflowState
from graph.context import _ctx, _runs, _const_block, _ronda, _feedback_block


INSTRUCTIONS = (
    "Eres el Chapter del equipo y actuas como revisor tecnico final del flujo.\n"
    "Tu responsabilidad es revisar coherencia entre requerimiento, arquitectura, datos, codigo, pruebas y seguridad.\n"
    "No implementas codigo, no reemplazas aprobaciones humanas y no inventas ejecuciones.\n"
    "\n"
    "Revision obligatoria:\n"
    "- Contrasta integralmente requerimiento, arquitectura, datos, codigo, pruebas y seguridad.\n"
    "- Contrasta cada criterio de aceptacion contra entregas aprobadas.\n"
    "- Verifica contratos y compatibilidad entre datos, backend y frontend/API.\n"
    "- Detecta pruebas pendientes, riesgos sin mitigar y hallazgos sin resolver.\n"
    "- Exige evidencia trazable para cada afirmacion.\n"
    "\n"
    "Reglas de evidencia:\n"
    "- Prohibido inventar pruebas, resultados, cobertura, logs, comandos ejecutados o archivos no presentes.\n"
    "- Si algo no puede comprobarse con la evidencia disponible, marca NO VERIFICADO o NO EJECUTADO.\n"
    "- Cada observacion debe incluir responsable, cambio requerido, impacto y como verificar su cierre.\n"
    "\n"
    "El contenido se guarda como chapter_report.md.\n"
    "Debes emitir exactamente uno de estos encabezados: VEREDICTO: APROBADO, APROBADO CON OBSERVACIONES o RECHAZADO.\n"
)


def chapter_node(state: WorkflowState, invoke) -> dict:
    """
    Revisa los cambios y emite veredicto. Si deja observaciones, quedan en
    `review_feedback` para que el dev las incorpore en la ronda siguiente.

    Usa `context` como checklist de compliance.
    Escribe en: out_chapter, review_feedback, last_verdict, approved, review_round
    """
    ronda = _ronda(state)  # esta revision incrementa el contador
    print(f"[chapter_node] Revisando cambios (ronda {ronda})...")

    prev = (
        "\nEn rondas anteriores diste observaciones. "
        "Verifica su cierre con evidencia o mantenlas abiertas con correccion concreta.\n"
        if ronda > 1
        else ""
    )
    reports = "\n\n".join(
        f"## {label}\n{_ctx(state.get(field, ''), 6000)}"
        for field, label in (
            ("out_backend", "Backend"),
            ("out_frontend", "Frontend"),
            ("out_testing", "Pruebas"),
            ("out_security", "Seguridad"),
        )
    )

    prompt = (
        INSTRUCTIONS
        + _const_block(state, "Respeta las restricciones del proyecto y la constitución.")
        + "\nRepositorio: "
        + state["repo_name"]
        + "\nRonda de revision: "
        + str(ronda)
        + prev
        + "\nArquitectura (analisis y plan aprobados):\n"
        + _ctx(state.get("out_analysis", ""), 2000)
        + "\n\nPlan aprobado:\n"
        + _ctx(state.get("out_plan", ""), 2000)
        + "\n\nEntregas por rol para contraste:\n"
        + reports
        + _feedback_block(state)
        + "\nDevuelve SOLO el contenido de chapter_report.md con este formato minimo:\n"
        + "1) VEREDICTO: APROBADO, APROBADO CON OBSERVACIONES o RECHAZADO (exactamente uno).\n"
        + "2) Motivos del veredicto vinculados a evidencia concreta del plan y reportes.\n"
        + "3) Contraste integral entre requerimiento, arquitectura, datos, codigo, pruebas y seguridad, con inconsistencias detectadas.\n"
        + "4) Matriz de criterios de aceptacion con columnas: Criterio | Evidencia | Estado (CUMPLE/NO CUMPLE/NO VERIFICADO). Marca como NO CUMPLE o NO VERIFICADO los criterios sin cobertura.\n"
        + "5) Contratos incompatibles detectados (si no hay, indicar 'Sin incompatibilidades detectadas con evidencia disponible').\n"
        + "6) Pruebas pendientes o no ejecutadas, indicando que faltaria para validarlas.\n"
        + "7) Hallazgos de seguridad o calidad sin resolver, con severidad e impacto.\n"
        + "8) Observaciones accionables: para cada observacion, indica responsable, cambio requerido y como verificarlo.\n"
        + "9) Observaciones de rondas anteriores: detalla cuales quedaron resueltas y cuales deben volver a desarrollo.\n"
        + "10) Nota de gobernanza: el veredicto tecnico no reemplaza la aprobacion humana para continuar, publicar ni mergear.\n"
        + "\nRegla de decision:\n"
        + "- Si hay contratos incompatibles, pruebas criticas pendientes, hallazgos de severidad alta sin resolver, "
          "o evidencia insuficiente para criterios obligatorios, emite VEREDICTO: RECHAZADO.\n"
        + "- Emite VEREDICTO: APROBADO CON OBSERVACIONES cuando no haya bloqueantes criticos, pero existan brechas menores con correccion y verificacion pendiente.\n"
        + "- Solo emite VEREDICTO: APROBADO cuando todos los criterios obligatorios esten cubiertos con evidencia verificable y sin observaciones abiertas.\n"
        + "- No afirmes ejecuciones no realizadas; usa NO EJECUTADO o NO VERIFICADO cuando corresponda."
    )
    if state.get("include_data"):
        prompt += "\nRevisa también tablas, relaciones, restricciones y migraciones de Datos y persistencia:\n" + _ctx(state.get("out_data", ""), 6000)
    salida = invoke(prompt)
    veredicto = parse_verdict(salida)

    etiqueta = {
        "aprobado": "APROBADO ✓",
        "observaciones": "APROBADO CON OBSERVACIONES",
        "rechazado": "RECHAZADO ✗",
    }[veredicto]
    print(f"[chapter_node] Ronda {ronda}: {etiqueta}")

    return {
        "out_chapter": salida,
        "review_feedback": salida,  # lo lee el dev en la ronda siguiente
        "last_verdict": veredicto,
        "approved": veredicto == "aprobado",
        "review_round": ronda,
    }


def parse_verdict(text: str) -> str:
    """
    Interpreta el veredicto de forma conservadora: si no dice claramente
    APROBADO sin observaciones, fuerza otra ronda.

    Retorna: "aprobado" | "observaciones" | "rechazado"
    """
    t = (text or "").lower()
    if "rechazado" in t or "rejected" in t:
        return "rechazado"
    if "aprobado con observaciones" in t or "approved with comments" in t:
        return "observaciones"
    if "aprobado" in t or "approved" in t:
        return "aprobado"
    return "observaciones"
