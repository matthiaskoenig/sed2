"""Web interface for building SED2 workflow JSON visually.

Run with:
    uv pip install 'sed2[web]'
    uv run streamlit run src/sed2/webapp.py
"""
import streamlit as st

import sed2.registry as registry
from sed2.core import (
    AnyTask,
    Data,
    DataRead,
    ExplicitODESimulation,
    ModelImport,
    Report,
    TaskParameter,
    Workflow,
)

_TYPE_MAP: dict[str, type[AnyTask]] = {
    "modelImport": ModelImport,
    "explicitODESimulation": ExplicitODESimulation,
    "report": Report,
    "dataRead": DataRead,
}


def _build_task(
    task_type: str,
    task_id: str,
    inputs: dict[str, str],
    params: dict[str, str],
) -> AnyTask:
    td = registry.get(task_type)
    cls = _TYPE_MAP[task_type]
    return cls(
        id=task_id,
        inputs={k: Data(value=v) for k, v in inputs.items() if v} or None,
        taskParameters={k: TaskParameter(value=v) for k, v in params.items() if v} or None,
        outputs={port: Data() for port in td.outputs},
    )


def _task_form(task_type: str) -> None:
    """Render dynamic input/parameter fields for the selected task type."""
    td = registry.get(task_type)

    if td.inputs:
        st.markdown("**Inputs**")
        for port, schema in td.inputs.items():
            label = f"`{port}`" + (" \\*" if schema.required else "")
            st.text_input(
                label,
                key=f"inp_{port}",
                help=schema.description or "",
                placeholder="#taskId.portName  or a literal value",
            )

    if td.parameters:
        st.markdown("**Parameters**")
        for param, schema in td.parameters.items():
            label = f"`{param}`" + (" \\*" if schema.required else "")
            st.text_input(
                label,
                key=f"prm_{param}",
                help=schema.description or "",
            )


def main() -> None:
    st.set_page_config(page_title="SED2 Workflow Builder", layout="wide")
    st.title("SED2 Workflow Builder")

    if "tasks" not in st.session_state:
        st.session_state.tasks: dict[str, AnyTask] = {}

    left, right = st.columns(2)

    # ── Left column: form ─────────────────────────────────────────────────────
    with left:
        workflow_id = st.text_input("Workflow ID", value="workflow1")

        st.divider()
        st.subheader("Add task")

        all_types = [td.type for td in registry.all_definitions()]
        task_type = st.selectbox("Task type", all_types)

        td = registry.get(task_type)
        if td.description:
            st.caption(td.description)

        task_id = st.text_input("Task ID", value=f"{task_type}1", key="new_task_id")

        _task_form(task_type)

        if st.button("Add task", type="primary"):
            td = registry.get(task_type)
            inputs = {port: st.session_state.get(f"inp_{port}", "") for port in td.inputs}
            params = {p: st.session_state.get(f"prm_{p}", "") for p in td.parameters}
            try:
                task = _build_task(task_type, task_id, inputs, params)
                st.session_state.tasks[task_id] = task
                st.success(f"Added **{task_id}** ({task_type})")
            except Exception as exc:
                st.error(str(exc))

        # ── Task list ──────────────────────────────────────────────────────────
        if st.session_state.tasks:
            st.divider()
            st.subheader("Tasks in workflow")
            for tid in list(st.session_state.tasks):
                col_label, col_btn = st.columns([5, 1])
                col_label.markdown(f"**{tid}** &nbsp; `{st.session_state.tasks[tid].type}`")
                if col_btn.button("✕", key=f"rm_{tid}", help=f"Remove {tid}"):
                    del st.session_state.tasks[tid]
                    st.rerun()

    # ── Right column: JSON preview ────────────────────────────────────────────
    with right:
        st.subheader("Generated JSON")
        if not st.session_state.tasks:
            st.info("Add tasks on the left to preview the workflow JSON here.")
        else:
            try:
                workflow = Workflow(id=workflow_id, tasks=st.session_state.tasks)
                json_str = workflow.model_dump_json(indent=2)
                st.code(json_str, language="json")
                st.download_button(
                    "Download workflow.json",
                    data=json_str,
                    file_name="workflow.json",
                    mime="application/json",
                )
            except Exception as exc:
                st.error(f"Workflow validation error: {exc}")


if __name__ == "__main__":
    main()
