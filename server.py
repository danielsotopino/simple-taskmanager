from fastmcp import FastMCP, Context
from datetime import datetime, timezone
import json
import os
from typing import Optional, List

# Ruta del archivo de tareas - se genera en el directorio del cliente
# Se puede personalizar con la variable de entorno TASKS_FILE_PATH
TASKS_FILE = os.environ.get("TASKS_FILE_PATH", "simple-taskmanager/tasks.json")

# Prioridades válidas según el schema
VALID_PRIORITIES = ["low", "medium", "high", "critical"]

# Cargar tareas desde el archivo
def load_tasks():
    try:
        if not os.path.exists(TASKS_FILE):
            return {}
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading tasks: {e}")
        return {}

# Guardar tareas en el archivo
def save_tasks(data):
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving tasks: {e}")
        raise

# Validar prioridad
def validate_priority(priority: str) -> bool:
    return priority in VALID_PRIORITIES

# Función para crear una nueva tarea
def create_task(context: str, title: str, description: str, priority: str, tags: Optional[List[str]] = None) -> dict:
    """Crear una nueva tarea en el contexto especificado"""
    if not validate_priority(priority):
        raise ValueError(f"Invalid priority: {priority}. Must be one of: {', '.join(VALID_PRIORITIES)}")
    
    tasks = load_tasks()
    
    # Crear contexto si no existe
    if context not in tasks:
        tasks[context] = {
            "tasks": [],
            "metadata": {
                "created": datetime.now(timezone.utc).isoformat(),
                "updated": datetime.now(timezone.utc).isoformat(),
                "description": f"Context for {context}",
                "version": "1.0.0"
            }
        }
    
    # Generar ID único
    existing_ids = [task["id"] for task in tasks[context]["tasks"]]
    new_id = max(existing_ids, default=0) + 1
    
    # Crear tarea
    task = {
        "id": new_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "todo",
        "dependencies": [],
        "creationDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "tags": tags or [],
        "blockers": [],
        "notes": "",
        "subtasks": []
    }
    
    # Agregar tarea al contexto
    tasks[context]["tasks"].append(task)
    tasks[context]["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()
    
    # Guardar cambios
    save_tasks(tasks)
    
    return task

# Inicializar el servidor FastMCP
mcp = FastMCP("Task Management")

# Crear una nueva tarea
@mcp.tool()
async def add_task(
    context: str,
    title: str,
    description: str,
    priority: str,
    tags: Optional[List[str]] = None,
    ctx: Context = None
) -> dict:
    """
    Create a new task in the specified context.

    Args:
        context: The context in which the task is created.
        title: The title of the task.
        description: The description of the task.
        priority: The priority of the task.
        tags: The tags of the task.
    """
    try:
        task = create_task(context, title, description, priority, tags)
        await ctx.info(f"Tarea {task['id']} creada en contexto '{context}'")
        return task
    except ValueError as e:
        await ctx.warning(f"Error de validación: {e}")
        raise
    except Exception as e:
        await ctx.warning(f"Error inesperado: {e}")
        raise

# Listar tareas con filtros y paginación
@mcp.tool()
async def list_tasks(
    context: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    ctx: Context = None
) -> dict:
    """
    List tasks with filters by context and tag, and pagination.

    Args:
        context: The context to filter by.
        tag: The tag to filter by.
        limit: The number of tasks to return.
        offset: The offset of the tasks to return.
    """
    try:
        tasks = load_tasks()
        filtered_tasks = []
        
        for ctx_name, ctx_data in tasks.items():
            if context and ctx_name != context:
                continue
            for task in ctx_data["tasks"]:
                if tag and tag not in task.get("tags", []):
                    continue
                task_copy = task.copy()
                task_copy["_context"] = ctx_name
                filtered_tasks.append(task_copy)
        
        total = len(filtered_tasks)
        paged_tasks = filtered_tasks[offset:offset + limit]
        
        await ctx.info(f"Mostrando {len(paged_tasks)} de {total} tareas")
        return {"total": total, "tasks": paged_tasks}
    except Exception as e:
        await ctx.warning(f"Error listando tareas: {e}")
        raise

# Obtener tarea por ID
@mcp.tool()
async def get_task(
    context: str,
    task_id: int,
    ctx: Context = None
) -> dict:
    """
    Get a specific task by ID from a context.

    Args:
        context: The context name.
        task_id: The task ID.
    """
    try:
        tasks = load_tasks()
        if context not in tasks:
            raise ValueError(f"Context '{context}' not found")
        
        for task in tasks[context]["tasks"]:
            if task["id"] == task_id:
                task_copy = task.copy()
                task_copy["_context"] = context
                return task_copy
        
        raise ValueError(f"Task {task_id} not found in context '{context}'")
    except Exception as e:
        await ctx.warning(f"Error obteniendo tarea: {e}")
        raise

# Actualizar estado de tarea
@mcp.tool()
async def update_task_status(
    context: str,
    task_id: int,
    status: str,
    ctx: Context = None
) -> dict:
    """
    Update the status of a task.

    Args:
        context: The context name.
        task_id: The task ID.
        status: The new status (todo, inprogress, inreview, testing, done, blocked).
    """
    valid_statuses = ["todo", "inprogress", "inreview", "testing", "done", "blocked"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    try:
        tasks = load_tasks()
        if context not in tasks:
            raise ValueError(f"Context '{context}' not found")
        
        for task in tasks[context]["tasks"]:
            if task["id"] == task_id:
                old_status = task["status"]
                task["status"] = status
                if status == "done":
                    task["completedDate"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
                
                tasks[context]["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()
                save_tasks(tasks)
                
                await ctx.info(f"Tarea {task_id} actualizada de '{old_status}' a '{status}'")
                return task
        
        raise ValueError(f"Task {task_id} not found in context '{context}'")
    except Exception as e:
        await ctx.warning(f"Error actualizando tarea: {e}")
        raise

if __name__ == "__main__":
    # Iniciar servidor MCP
    print("🤖 Iniciando servidor MCP...")
    mcp.run()
