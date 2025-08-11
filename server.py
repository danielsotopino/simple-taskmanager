from fastmcp import FastMCP, Context
from datetime import datetime, timezone
import json
import os
from typing import Optional, List
from pydantic import BaseModel, Field

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

# Función para crear una nueva subtarea
def create_subtask(context: str, task_id: int, title: str, description: str, tags: Optional[List[str]] = None) -> dict:
    """Crear una nueva subtarea en la tarea especificada"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    parent_task = None
    for task in tasks[context]["tasks"]:
        if task["id"] == task_id:
            parent_task = task
            break
    
    if not parent_task:
        raise ValueError(f"Task {task_id} not found in context '{context}'")
    
    # Generar ID único para la subtarea
    existing_subtask_ids = []
    
    def collect_subtask_ids(subtasks):
        for subtask in subtasks:
            existing_subtask_ids.append(subtask["id"])
            if "subtasks" in subtask and subtask["subtasks"]:
                collect_subtask_ids(subtask["subtasks"])
    
    collect_subtask_ids(parent_task.get("subtasks", []))
    new_subtask_id = max(existing_subtask_ids, default=0) + 1
    
    # Crear subtarea
    subtask = {
        "id": new_subtask_id,
        "title": title,
        "description": description,
        "status": "todo",
        "dependencies": [],
        "creationDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "tags": tags or [],
        "blockers": [],
        "notes": "",
        "subtasks": []
    }
    
    # Agregar subtarea a la tarea padre
    if "subtasks" not in parent_task:
        parent_task["subtasks"] = []
    parent_task["subtasks"].append(subtask)
    
    # Actualizar metadata del contexto
    tasks[context]["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()
    
    # Guardar cambios
    save_tasks(tasks)
    
    return subtask

# Función para obtener una subtarea por ID
def get_subtask(context: str, task_id: int, subtask_id: int) -> dict:
    """Obtener una subtarea específica por ID"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    for task in tasks[context]["tasks"]:
        if task["id"] == task_id:
            # Buscar la subtarea
            def find_subtask(subtasks, target_id):
                for subtask in subtasks:
                    if subtask["id"] == target_id:
                        return subtask
                    if "subtasks" in subtask and subtask["subtasks"]:
                        result = find_subtask(subtask["subtasks"], target_id)
                        if result:
                            return result
                return None
            
            subtask = find_subtask(task.get("subtasks", []), subtask_id)
            if subtask:
                subtask_copy = subtask.copy()
                subtask_copy["_parent_task_id"] = task_id
                subtask_copy["_context"] = context
                return subtask_copy
            
            raise ValueError(f"Subtask {subtask_id} not found in task {task_id}")
    
    raise ValueError(f"Task {task_id} not found in context '{context}'")

# Función para actualizar el estado de una subtarea
def update_subtask_status(context: str, task_id: int, subtask_id: int, status: str) -> dict:
    """Actualizar el estado de una subtarea"""
    valid_statuses = ["todo", "inprogress", "inreview", "testing", "done", "blocked"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    for task in tasks[context]["tasks"]:
        if task["id"] == task_id:
            # Buscar y actualizar la subtarea
            def update_subtask_status_recursive(subtasks, target_id, new_status):
                for subtask in subtasks:
                    if subtask["id"] == target_id:
                        old_status = subtask["status"]
                        subtask["status"] = new_status
                        if new_status == "done":
                            subtask["completedDate"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
                        return subtask, old_status
                    if "subtasks" in subtask and subtask["subtasks"]:
                        result = update_subtask_status_recursive(subtask["subtasks"], target_id, new_status)
                        if result:
                            return result
                return None
            
            result = update_subtask_status_recursive(task.get("subtasks", []), subtask_id, status)
            if result:
                subtask, old_status = result
                
                # Actualizar metadata del contexto
                tasks[context]["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()
                save_tasks(tasks)
                
                return subtask
            
            raise ValueError(f"Subtask {subtask_id} not found in task {task_id}")
    
    raise ValueError(f"Task {task_id} not found in context '{context}'")

# Función para eliminar una subtarea
def delete_subtask(context: str, task_id: int, subtask_id: int) -> bool:
    """Eliminar una subtarea por ID"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    for task in tasks[context]["tasks"]:
        if task["id"] == task_id:
            # Buscar y eliminar la subtarea
            def delete_subtask_recursive(subtasks, target_id):
                for i, subtask in enumerate(subtasks):
                    if subtask["id"] == target_id:
                        deleted_subtask = subtasks.pop(i)
                        return deleted_subtask
                    if "subtasks" in subtask and subtask["subtasks"]:
                        result = delete_subtask_recursive(subtask["subtasks"], target_id)
                        if result:
                            return result
                return None
            
            deleted_subtask = delete_subtask_recursive(task.get("subtasks", []), subtask_id)
            if deleted_subtask:
                # Actualizar metadata del contexto
                tasks[context]["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()
                save_tasks(tasks)
                return True
            
            raise ValueError(f"Subtask {subtask_id} not found in task {task_id}")
    
    raise ValueError(f"Task {task_id} not found in context '{context}'")

# Función para listar subtareas de una tarea
def list_subtasks(context: str, task_id: int, recursive: bool = False) -> List[dict]:
    """Listar todas las subtareas de una tarea específica"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    for task in tasks[context]["tasks"]:
        if task["id"] == task_id:
            subtasks = []
            
            def collect_subtasks(task_subtasks, level=0):
                for subtask in task_subtasks:
                    subtask_copy = subtask.copy()
                    subtask_copy["_level"] = level
                    subtask_copy["_parent_task_id"] = task_id
                    subtask_copy["_context"] = context
                    subtasks.append(subtask_copy)
                    
                    if recursive and "subtasks" in subtask and subtask["subtasks"]:
                        collect_subtasks(subtask["subtasks"], level + 1)
            
            collect_subtasks(task.get("subtasks", []))
            return subtasks
    
    raise ValueError(f"Task {task_id} not found in context '{context}'")

# Función para eliminar una tarea
def delete_task(context: str, task_id: int) -> bool:
    """Eliminar una tarea por ID del contexto especificado"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar y eliminar la tarea
    for i, task in enumerate(tasks[context]["tasks"]):
        if task["id"] == task_id:
            deleted_task = tasks[context]["tasks"].pop(i)
            
            # Actualizar metadata del contexto
            tasks[context]["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()
            
            # Guardar cambios
            save_tasks(tasks)
            
            return True
    
    raise ValueError(f"Task {task_id} not found in context '{context}'")

# Inicializar el servidor FastMCP
mcp = FastMCP("Task Management")

# Crear una nueva tarea
@mcp.tool(
    name="add_task",
    description="Create a new task in the specified context"
)
async def add_task(
    context: str = Field(description="The context name"),
    title: str = Field(description="The task title"),
    description: str = Field(description="The task description"),
    priority: str = Field(description="The task priority (low, medium, high, critical)"),
    tags: Optional[List[str]] = Field(default=None, description="List of tags for the task"),
    ctx: Context = None
) -> dict:
    """
    Create a new task in the specified context.

    Args:
        context: The context in which the task is created.
        title: The title of the task.
        description: The description of the task.
        priority: The priority of the task.
        tags: List of tags of the task.
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
@mcp.tool(
    name="list_tasks",
    description="List tasks with optional filtering by context and tags"
)
async def list_tasks(
    context: Optional[str] = Field(default=None, description="The context name to filter by"),
    tag: Optional[str] = Field(default=None, description="The tag to filter by"),
    limit: int = Field(default=20, description="Maximum number of tasks to return"),
    offset: int = Field(default=0, description="Number of tasks to skip"),
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
@mcp.tool(
    name="get_task",
    description="Get a specific task by ID from a context"
)
async def get_task(
    context: str = Field(description="The context name"),
    task_id: int = Field(description="The task ID"),
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

class TaskStatusUpdateSchema(BaseModel):
    context: str = Field(description="The context name")
    task_id: int = Field(description="The task ID")
    status: str = Field(description="The new status (todo, inprogress, inreview, testing, done, blocked)")

# Actualizar estado de tarea
@mcp.tool(
    name="update_task_status",
    description="Update the status of a task"
)
async def update_task_status(
    context: str = Field(description="The context name"),
    task_id: int = Field(description="The task ID"),
    status: str = Field(description="The new status (todo, inprogress, inreview, testing, done, blocked)"),
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

# Crear una nueva subtarea
@mcp.tool(
    name="add_subtask",
    description="Create a new subtask in the specified task"
)
async def add_subtask(
    context: str = Field(description="The context in which the parent task exists"),
    task_id: int = Field(description="The ID of the parent task"),
    title: str = Field(description="The title of the subtask"),
    description: str = Field(description="The description of the subtask"),
    tags: Optional[List[str]] = Field(default=None, description="List of tags of the subtask"),
    ctx: Context = None
) -> dict:
    """
    Create a new subtask in the specified task.

    Args:
        context: The context in which the parent task exists.
        task_id: The ID of the parent task.
        title: The title of the subtask.
        description: The description of the subtask.
        tags: List of tags of the subtask.
    """
    try:
        subtask = create_subtask(context, task_id, title, description, tags)
        await ctx.info(f"Subtarea {subtask['id']} creada en tarea {task_id} del contexto '{context}'")
        return subtask
    except ValueError as e:
        await ctx.warning(f"Error de validación: {e}")
        raise
    except Exception as e:
        await ctx.warning(f"Error inesperado: {e}")
        raise

# Obtener subtarea por ID
@mcp.tool(
    name="get_subtask_by_id",
    description="Get a specific subtask by ID from a task"
)
async def get_subtask_by_id(
    context: str = Field(description="The context name"),
    task_id: int = Field(description="The parent task ID"),
    subtask_id: int = Field(description="The subtask ID"),
    ctx: Context = None
) -> dict:
    """
    Get a specific subtask by ID from a task.

    Args:
        context: The context name.
        task_id: The parent task ID.
        subtask_id: The subtask ID.
    """
    try:
        subtask = get_subtask(context, task_id, subtask_id)
        await ctx.info(f"Subtarea {subtask_id} obtenida de la tarea {task_id}")
        return subtask
    except Exception as e:
        await ctx.warning(f"Error obteniendo subtarea: {e}")
        raise

# Actualizar estado de subtarea
@mcp.tool(
    name="update_subtask_status",
    description="Update the status of a subtask"
)
async def update_subtask_status_tool(
    context: str = Field(description="The context name"),
    task_id: int = Field(description="The parent task ID"),
    subtask_id: int = Field(description="The subtask ID"),
    status: str = Field(description="The new status (todo, inprogress, inreview, testing, done, blocked)"),
    ctx: Context = None
) -> dict:
    """
    Update the status of a subtask.

    Args:
        context: The context name.
        task_id: The parent task ID.
        subtask_id: The subtask ID.
        status: The new status (todo, inprogress, inreview, testing, done, blocked).
    """
    try:
        subtask = update_subtask_status(context, task_id, subtask_id, status)
        await ctx.info(f"Subtarea {subtask_id} actualizada a estado '{status}'")
        return subtask
    except Exception as e:
        await ctx.warning(f"Error actualizando subtarea: {e}")
        raise

# Eliminar subtarea
@mcp.tool(
    name="delete_subtask",
    description="Delete a subtask by ID"
)
async def delete_subtask_tool(
    context: str = Field(description="The context name"),
    task_id: int = Field(description="The parent task ID"),
    subtask_id: int = Field(description="The subtask ID"),
    ctx: Context = None
) -> dict:
    """
    Delete a subtask by ID.

    Args:
        context: The context name.
        task_id: The parent task ID.
        subtask_id: The subtask ID.
    """
    try:
        success = delete_subtask(context, task_id, subtask_id)
        if success:
            await ctx.info(f"Subtarea {subtask_id} eliminada de la tarea {task_id}")
            return {"success": True, "message": f"Subtarea {subtask_id} eliminada exitosamente"}
        else:
            raise Exception("No se pudo eliminar la subtarea")
    except Exception as e:
        await ctx.warning(f"Error eliminando subtarea: {e}")
        raise

# Eliminar tarea
@mcp.tool(
    name="delete_task",
    description="Delete a task by ID from a context"
)
async def delete_task_tool(
    context: str = Field(description="The context name"),
    task_id: int = Field(description="The task ID to delete"),
    ctx: Context = None
) -> dict:
    """
    Delete a task by ID from a context.

    Args:
        context: The context name.
        task_id: The task ID to delete.
    """
    try:
        success = delete_task(context, task_id)
        if success:
            await ctx.info(f"Tarea {task_id} eliminada del contexto '{context}'")
            return {"success": True, "message": f"Tarea {task_id} eliminada exitosamente del contexto '{context}'"}
        else:
            raise Exception("No se pudo eliminar la tarea")
    except ValueError as e:
        await ctx.warning(f"Error de validación: {e}")
        raise
    except Exception as e:
        await ctx.warning(f"Error eliminando tarea: {e}")
        raise

# Listar subtareas
@mcp.tool(
    name="list_subtasks",
    description="List all subtasks of a specific task"
)
async def list_subtasks_tool(
    context: str = Field(description="The context name"),
    task_id: int = Field(description="The parent task ID"),
    recursive: bool = Field(default=False, description="Whether to include nested subtasks recursively"),
    ctx: Context = None
) -> dict:
    """
    List all subtasks of a specific task.

    Args:
        context: The context name.
        task_id: The parent task ID.
        recursive: Whether to include nested subtasks recursively.
    """
    try:
        subtasks = list_subtasks(context, task_id, recursive)
        await ctx.info(f"Mostrando {len(subtasks)} subtareas de la tarea {task_id}")
        return {"total": len(subtasks), "subtasks": subtasks}
    except Exception as e:
        await ctx.warning(f"Error listando subtareas: {e}")
        raise

if __name__ == "__main__":
    # Iniciar servidor MCP
    print("🤖 Iniciando servidor MCP...")
    mcp.run()
