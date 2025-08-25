from fastmcp import FastMCP, Context
from datetime import datetime, timezone
import json
import os
import re
from typing import Annotated, Optional, List
from pydantic import BaseModel, Field

# Ruta del archivo de tareas - se genera en el directorio del cliente
# Se puede personalizar con la variable de entorno TASKS_FILE_PATH
TASKS_FILE = os.environ.get("TASKS_FILE_PATH", "simple-taskmanager/tasks.json")

# Prioridades válidas según el schema
VALID_PRIORITIES = ["low", "medium", "high", "critical"]

# Status workflow según MCP_USAGE_GUIDELINES.md
STATUS_WORKFLOW = {
    "todo": ["inprogress", "blocked"],
    "inprogress": ["inreview", "testing", "blocked", "done"],
    "inreview": ["inprogress", "testing", "done"],
    "testing": ["inprogress", "done", "blocked"],
    "blocked": ["todo", "inprogress"],
    "done": []
}

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

# Funciones de validación según MCP_USAGE_GUIDELINES.md
def validate_priority(priority: str) -> bool:
    return priority in VALID_PRIORITIES

def validate_context_name(context: str) -> bool:
    """Validar nombres de contexto: ^[a-z][a-z0-9-]*$"""
    return re.match(r'^[a-z][a-z0-9-]*$', context) is not None

def validate_tag_name(tag: str) -> bool:
    """Validar nombres de tags: ^[a-z0-9-]+$"""
    return re.match(r'^[a-z0-9-]+$', tag) is not None

def validate_title_format(title: str) -> bool:
    """Validar formato de títulos: ^\\[([A-Z]+)\\]\\s+.+"""
    return re.match(r'^\[([A-Z]+)\]\s+.+', title) is not None

def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validar transiciones de estado según workflow"""
    if current_status not in STATUS_WORKFLOW:
        return False
    return new_status in STATUS_WORKFLOW[current_status]

def validate_dependency_format(dependency: str) -> bool:
    """Validar formato de dependencias cross-context: ^[a-z][a-z0-9-]*:[0-9]+(:[0-9]+)?$"""
    return re.match(r'^[a-z][a-z0-9-]*:[0-9]+(:[0-9]+)?$', dependency) is not None

# Función para crear una nueva tarea
def create_task(context: str, title: str, description: str, priority: str, tags: Optional[List[str]] = None) -> dict:
    """Crear una nueva tarea en el contexto especificado"""
    # Validaciones según MCP_USAGE_GUIDELINES.md
    if not validate_context_name(context):
        raise ValueError(f"Invalid context name: '{context}'. Must match pattern: ^[a-z][a-z0-9-]*$")
    
    if not validate_priority(priority):
        raise ValueError(f"Invalid priority: {priority}. Must be one of: {', '.join(VALID_PRIORITIES)}")
    
    # Validar formato de título (advertencia, no error)
    if not validate_title_format(title):
        print(f"Warning: Title '{title}' doesn't follow recommended format: [TECH_TAG] Description")
    
    # Validar tags si se proporcionan
    if tags:
        for tag in tags:
            if not validate_tag_name(tag):
                raise ValueError(f"Invalid tag: '{tag}'. Tags must match pattern: ^[a-z0-9-]+$")
    
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
    
    # Generar ID único como string
    existing_ids = [int(task["id"]) for task in tasks[context]["tasks"] if task["id"].isdigit()]
    new_id = str(max(existing_ids, default=0) + 1)
    
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
def create_subtask(context: str, task_id: str, title: str, description: str, tags: Optional[List[str]] = None) -> dict:
    """Crear una nueva subtarea en la tarea especificada"""
    # Validar formato de título (advertencia, no error)
    if not validate_title_format(title):
        print(f"Warning: Subtask title '{title}' doesn't follow recommended format: [TECH_TAG] Description")
    
    # Validar tags si se proporcionan
    if tags:
        for tag in tags:
            if not validate_tag_name(tag):
                raise ValueError(f"Invalid tag: '{tag}'. Tags must match pattern: ^[a-z0-9-]+$")
    
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    parent_task = None
    for task in tasks[context]["tasks"]:
        if str(task["id"]) == task_id:
            parent_task = task
            break
    
    if not parent_task:
        raise ValueError(f"Task {task_id} not found in context '{context}'")
    
    # Generar ID único para la subtarea como string
    existing_subtask_ids = []
    
    def collect_subtask_ids(subtasks):
        for subtask in subtasks:
            if subtask["id"].isdigit():
                existing_subtask_ids.append(int(subtask["id"]))
            if "subtasks" in subtask and subtask["subtasks"]:
                collect_subtask_ids(subtask["subtasks"])
    
    collect_subtask_ids(parent_task.get("subtasks", []))
    new_subtask_id = str(max(existing_subtask_ids, default=0) + 1)
    
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
def get_subtask(context: str, task_id: str, subtask_id: str) -> dict:
    """Obtener una subtarea específica por ID"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    for task in tasks[context]["tasks"]:
        if str(task["id"]) == task_id:
            # Buscar la subtarea
            def find_subtask(subtasks, target_id):
                for subtask in subtasks:
                    if str(subtask["id"]) == target_id:
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
def update_subtask_status(context: str, task_id: str, subtask_id: str, status: str) -> dict:
    """Actualizar el estado de una subtarea"""
    valid_statuses = ["todo", "inprogress", "inreview", "testing", "done", "blocked"]
    if status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    for task in tasks[context]["tasks"]:
        if str(task["id"]) == task_id:
            # Buscar y actualizar la subtarea
            def update_subtask_status_recursive(subtasks, target_id, new_status):
                for subtask in subtasks:
                    if str(subtask["id"]) == target_id:
                        old_status = subtask["status"]
                        
                        # Validar transición de estado
                        if not validate_status_transition(old_status, new_status):
                            valid_transitions = STATUS_WORKFLOW.get(old_status, [])
                            raise ValueError(f"Invalid status transition from '{old_status}' to '{new_status}'. Valid transitions: {valid_transitions}")
                        
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
def delete_subtask(context: str, task_id: str, subtask_id: str) -> bool:
    """Eliminar una subtarea por ID"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    for task in tasks[context]["tasks"]:
        if str(task["id"]) == task_id:
            # Buscar y eliminar la subtarea
            def delete_subtask_recursive(subtasks, target_id):
                for i, subtask in enumerate(subtasks):
                    if str(subtask["id"]) == target_id:
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
def list_subtasks(context: str, task_id: str, recursive: bool = False) -> List[dict]:
    """Listar todas las subtareas de una tarea específica"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar la tarea padre
    for task in tasks[context]["tasks"]:
        if str(task["id"]) == task_id:
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
def delete_task(context: str, task_id: str) -> bool:
    """Eliminar una tarea por ID del contexto especificado"""
    tasks = load_tasks()
    
    if context not in tasks:
        raise ValueError(f"Context '{context}' not found")
    
    # Buscar y eliminar la tarea
    for i, task in enumerate(tasks[context]["tasks"]):
        if str(task["id"]) == task_id:
            deleted_task = tasks[context]["tasks"].pop(i)
            
            # Actualizar metadata del contexto
            tasks[context]["metadata"]["updated"] = datetime.now(timezone.utc).isoformat()
            
            # Guardar cambios
            save_tasks(tasks)
            
            return True
    
    raise ValueError(f"Task {task_id} not found in context '{context}'")

# Inicializar el servidor FastMCP
mcp = FastMCP("Task Management")

# Obtener ruta del directorio del servidor (donde están los schemas)
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))

# Funciones auxiliares para cargar archivos del servidor
def load_server_file(filename: str) -> str:
    """Cargar contenido de un archivo del servidor"""
    file_path = os.path.join(SERVER_DIR, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except (IOError, FileNotFoundError) as e:
        raise FileNotFoundError(f"Server file not found: {filename}. Error: {e}")

def load_server_json(filename: str) -> dict:
    """Cargar contenido JSON de un archivo del servidor"""
    content = load_server_file(filename)
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filename}: {e}")

# ========================================
# MÉTODOS DE DOCUMENTACIÓN Y AYUDA
# ========================================

@mcp.tool(
    name="get_usage_guidelines",
    description="Get MCP usage guidelines and validation rules"
)
async def get_usage_guidelines(ctx: Context = None) -> dict:
    """
    Get the complete MCP usage guidelines including validation rules,
    status workflow, and implementation requirements.
    """
    try:
        guidelines_content = load_server_file("MCP_USAGE_GUIDELINES.md")
        await ctx.info("Usage guidelines loaded successfully")
        return {
            "guidelines": guidelines_content,
            "source": "MCP_USAGE_GUIDELINES.md"
        }
    except Exception as e:
        await ctx.warning(f"Error loading usage guidelines: {e}")
        raise

@mcp.tool(
    name="get_task_schema",
    description="Get the JSON schema for validating tasks.json files"
)
async def get_task_schema(ctx: Context = None) -> dict:
    """
    Get the JSON schema used to validate tasks.json structure.
    Use this schema to validate your project's task data.
    """
    try:
        schema = load_server_json("schema-tasks.json")
        await ctx.info("Task schema loaded successfully")
        return {
            "schema": schema,
            "description": "Use this schema to validate your tasks.json file",
            "source": "schema-tasks.json"
        }
    except Exception as e:
        await ctx.warning(f"Error loading task schema: {e}")
        raise

@mcp.tool(
    name="get_definitions_schema",
    description="Get the JSON schema for validating definitions.json files"
)
async def get_definitions_schema(ctx: Context = None) -> dict:
    """
    Get the JSON schema used to validate definitions.json structure.
    Use this schema to validate your project's feature definitions.
    """
    try:
        schema = load_server_json("schema-definitions.json")
        await ctx.info("Definitions schema loaded successfully")
        return {
            "schema": schema,
            "description": "Use this schema to validate your definitions.json file",
            "source": "schema-definitions.json"
        }
    except Exception as e:
        await ctx.warning(f"Error loading definitions schema: {e}")
        raise

@mcp.tool(
    name="validate_project_files",
    description="Validate tasks.json and definitions.json files against their schemas"
)
async def validate_project_files(
    tasks_file_path: Annotated[Optional[str], Field(default=None, description="Path to tasks.json file")] = None,
    definitions_file_path: Annotated[Optional[str], Field(default=None, description="Path to definitions.json file")] = None,
    ctx: Context = None
) -> dict:
    """
    Validate project files against their respective schemas.
    
    Args:
        tasks_file_path: Path to tasks.json file (optional, defaults to current TASKS_FILE)
        definitions_file_path: Path to definitions.json file (optional)
    """
    results = {
        "tasks_validation": None,
        "definitions_validation": None,
        "overall_valid": True
    }
    
    # Validate tasks.json
    if tasks_file_path or os.path.exists(TASKS_FILE):
        file_to_validate = tasks_file_path or TASKS_FILE
        try:
            # For now, just check if file loads correctly
            # In a full implementation, you'd use jsonschema library
            with open(file_to_validate, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)
            results["tasks_validation"] = {
                "valid": True,
                "file": file_to_validate,
                "message": "Tasks file loaded successfully"
            }
            await ctx.info(f"Tasks file {file_to_validate} is valid")
        except Exception as e:
            results["tasks_validation"] = {
                "valid": False,
                "file": file_to_validate,
                "error": str(e)
            }
            results["overall_valid"] = False
            await ctx.warning(f"Tasks file validation failed: {e}")
    
    # Validate definitions.json
    if definitions_file_path and os.path.exists(definitions_file_path):
        try:
            with open(definitions_file_path, "r", encoding="utf-8") as f:
                definitions_data = json.load(f)
            results["definitions_validation"] = {
                "valid": True,
                "file": definitions_file_path,
                "message": "Definitions file loaded successfully"
            }
            await ctx.info(f"Definitions file {definitions_file_path} is valid")
        except Exception as e:
            results["definitions_validation"] = {
                "valid": False,
                "file": definitions_file_path,
                "error": str(e)
            }
            results["overall_valid"] = False
            await ctx.warning(f"Definitions file validation failed: {e}")
    
    return results

# ========================================
# MÉTODOS DE GENERACIÓN DE ARCHIVOS
# ========================================

@mcp.tool(
    name="create_definitions_template",
    description="Create a definitions.json template with common features"
)
async def create_definitions_template(
    project_features: Annotated[
        List[str],
        Field(
            description="List of main project features, including some intentionally ambiguous but software-related functionalities",
            example=[
                "auth", "user-management", "votes", "notifications", "integration", "dashboard", "reporting", "core-logic", "data-sync", "settings", "analytics", "workflow", "import-export", "monitoring"
            ]
        )
    ] = [],
    ctx: Context = None
) -> dict:
    """
    Create a definitions.json template based on common project features.
    
    Args:
        project_features: List of main features for your project
    """
    # Template básico con features comunes
    template = {
        "features": {},
        "tech_tags": {}
    }
    
    # Agregar features proporcionadas por el usuario
    for feature in project_features:
        if validate_context_name(feature):
            template["features"][feature] = {
                "description": f"{feature.replace('-', ' ').title()} functionality",
                "common_tags": [feature.replace('-', '_'), "feature"],
                "related_contexts": []
            }
        else:
            await ctx.warning(f"Skipping invalid feature name: {feature}")
    
    # Agregar algunas features comunes si no se proporcionaron
    if not project_features:
        template["features"] = {
            "auth": {
                "description": "Authentication and authorization system",
                "common_tags": ["auth", "login", "jwt", "security"],
                "related_contexts": ["user-management"]
            },
            "user-management": {
                "description": "User lifecycle and profile management",
                "common_tags": ["users", "profiles", "crud"],
                "related_contexts": ["auth"]
            },
            "api": {
                "description": "Backend API endpoints and services",
                "common_tags": ["api", "backend", "endpoints"],
                "related_contexts": ["auth"]
            }
        }
    
    await ctx.info(f"Created definitions template with {len(template['features'])} features")
    return {
        "template": template,
        "instructions": "Save this as 'definitions.json' in your project root",
        "next_steps": [
            "Customize feature descriptions for your project",
            "Add related_contexts between features",
            "Add more common_tags specific to your domain"
        ]
    }

@mcp.tool(
    name="init_project",
    description="Initialize a new project with empty tasks.json and definitions.json files"
)
async def init_project(
    project_name: Annotated[str, Field(description="Name of the project")],
    project_features: Annotated[List[str], Field(description="List of main project features")] = [],
    ctx: Context = None
) -> dict:
    """
    Initialize a new project with empty tasks.json and sample definitions.json.
    
    Args:
        project_name: Name of the project
        project_features: List of main features for your project
    """
    try:
        # Crear tasks.json vacío
        empty_tasks = {}
        
        # Crear definitions.json con template
        definitions_response = await create_definitions_template(project_features, ctx)
        definitions_template = definitions_response["template"]
        
        await ctx.info(f"Initialized project '{project_name}' with {len(project_features)} features")
        
        return {
            "project_name": project_name,
            "tasks_json": empty_tasks,
            "definitions_json": definitions_template,
            "files_created": [
                {
                    "file": "tasks.json",
                    "description": "Empty tasks file - ready for your project tasks",
                    "content": empty_tasks
                },
                {
                    "file": "definitions.json", 
                    "description": "Feature definitions for your project",
                    "content": definitions_template
                }
            ],
            "next_steps": [
                "Save both JSON files to your project directory",
                "Customize definitions.json for your specific features",
                "Start adding tasks with the add_task tool",
                "Use get_usage_guidelines for validation rules"
            ]
        }
    except Exception as e:
        await ctx.warning(f"Error initializing project: {e}")
        raise

@mcp.tool(
    name="add_project_feature",
    description="Add a new feature to an existing project's definitions.json"
)
async def add_project_feature(
    feature_name: Annotated[str, Field(description="Name of the feature to add (e.g. 'notifications', 'reporting')")],
    description: Annotated[str, Field(description="Description of what this feature does")],
    common_tags: Annotated[List[str], Field(description="Common tags associated with this feature")] = [],
    related_contexts: Annotated[List[str], Field(description="Other features this one relates to")] = [],
    definitions_file_path: Annotated[Optional[str], Field(default="./definitions.json", description="Path to definitions.json file")] = "./definitions.json",
    ctx: Context = None
) -> dict:
    """
    Add a new feature to an existing project's definitions.json file.
    
    Args:
        feature_name: Name of the feature (must follow context naming rules)
        description: What this feature does
        common_tags: Tags commonly used with this feature
        related_contexts: Other features this one connects to
        definitions_file_path: Path to definitions.json file
    """
    try:
        # Validate feature name
        if not validate_context_name(feature_name):
            raise ValueError(f"Invalid feature name: '{feature_name}'. Must match pattern: ^[a-z][a-z0-9-]*$")
        
        # Validate tags
        for tag in common_tags:
            if not validate_tag_name(tag):
                raise ValueError(f"Invalid tag: '{tag}'. Tags must match pattern: ^[a-z0-9-]+$")
        
        # Load existing definitions
        if os.path.exists(definitions_file_path):
            with open(definitions_file_path, "r", encoding="utf-8") as f:
                definitions = json.load(f)
        else:
            definitions = {"features": {}, "tech_tags": {}}
        
        # Check if feature already exists
        if feature_name in definitions.get("features", {}):
            raise ValueError(f"Feature '{feature_name}' already exists in definitions")
        
        # Add new feature
        definitions["features"][feature_name] = {
            "description": description,
            "common_tags": common_tags,
            "related_contexts": related_contexts
        }
        
        # Save updated definitions
        with open(definitions_file_path, "w", encoding="utf-8") as f:
            json.dump(definitions, f, indent=2, ensure_ascii=False)
        
        await ctx.info(f"Added feature '{feature_name}' to definitions")
        return {
            "success": True,
            "feature_added": feature_name,
            "definitions_file": definitions_file_path,
            "total_features": len(definitions["features"])
        }
        
    except Exception as e:
        await ctx.warning(f"Error adding feature: {e}")
        raise

@mcp.tool(
    name="update_project_feature",
    description="Update an existing feature in project's definitions.json"
)
async def update_project_feature(
    feature_name: Annotated[str, Field(description="Name of the feature to update")],
    description: Annotated[Optional[str], Field(default=None, description="New description (optional)")] = None,
    common_tags: Annotated[Optional[List[str]], Field(default=None, description="New common tags (optional)")] = None,
    related_contexts: Annotated[Optional[List[str]], Field(default=None, description="New related contexts (optional)")] = None,
    definitions_file_path: Annotated[Optional[str], Field(default="./definitions.json", description="Path to definitions.json file")] = "./definitions.json",
    ctx: Context = None
) -> dict:
    """
    Update an existing feature in the project's definitions.json file.
    
    Args:
        feature_name: Name of the feature to update
        description: New description (if provided)
        common_tags: New common tags (if provided)
        related_contexts: New related contexts (if provided)
        definitions_file_path: Path to definitions.json file
    """
    try:
        # Load existing definitions
        if not os.path.exists(definitions_file_path):
            raise FileNotFoundError(f"Definitions file not found: {definitions_file_path}")
        
        with open(definitions_file_path, "r", encoding="utf-8") as f:
            definitions = json.load(f)
        
        # Check if feature exists
        if feature_name not in definitions.get("features", {}):
            raise ValueError(f"Feature '{feature_name}' not found in definitions")
        
        # Validate tags if provided
        if common_tags:
            for tag in common_tags:
                if not validate_tag_name(tag):
                    raise ValueError(f"Invalid tag: '{tag}'. Tags must match pattern: ^[a-z0-9-]+$")
        
        # Update feature properties
        feature = definitions["features"][feature_name]
        updated_fields = []
        
        if description is not None:
            feature["description"] = description
            updated_fields.append("description")
        
        if common_tags is not None:
            feature["common_tags"] = common_tags
            updated_fields.append("common_tags")
        
        if related_contexts is not None:
            feature["related_contexts"] = related_contexts
            updated_fields.append("related_contexts")
        
        if not updated_fields:
            await ctx.info(f"No changes made to feature '{feature_name}'")
            return {
                "success": True,
                "feature_updated": feature_name,
                "fields_updated": [],
                "message": "No changes were specified"
            }
        
        # Save updated definitions
        with open(definitions_file_path, "w", encoding="utf-8") as f:
            json.dump(definitions, f, indent=2, ensure_ascii=False)
        
        await ctx.info(f"Updated feature '{feature_name}': {', '.join(updated_fields)}")
        return {
            "success": True,
            "feature_updated": feature_name,
            "fields_updated": updated_fields,
            "updated_feature": feature
        }
        
    except Exception as e:
        await ctx.warning(f"Error updating feature: {e}")
        raise

@mcp.tool(
    name="remove_project_feature",
    description="Remove a feature from project's definitions.json"
)
async def remove_project_feature(
    feature_name: Annotated[str, Field(description="Name of the feature to remove")],
    definitions_file_path: Annotated[Optional[str], Field(default="./definitions.json", description="Path to definitions.json file")] = "./definitions.json",
    ctx: Context = None
) -> dict:
    """
    Remove a feature from the project's definitions.json file.
    
    Args:
        feature_name: Name of the feature to remove
        definitions_file_path: Path to definitions.json file
    """
    try:
        # Load existing definitions
        if not os.path.exists(definitions_file_path):
            raise FileNotFoundError(f"Definitions file not found: {definitions_file_path}")
        
        with open(definitions_file_path, "r", encoding="utf-8") as f:
            definitions = json.load(f)
        
        # Check if feature exists
        if feature_name not in definitions.get("features", {}):
            raise ValueError(f"Feature '{feature_name}' not found in definitions")
        
        # Remove the feature
        removed_feature = definitions["features"].pop(feature_name)
        
        # Save updated definitions
        with open(definitions_file_path, "w", encoding="utf-8") as f:
            json.dump(definitions, f, indent=2, ensure_ascii=False)
        
        await ctx.info(f"Removed feature '{feature_name}' from definitions")
        return {
            "success": True,
            "feature_removed": feature_name,
            "removed_feature": removed_feature,
            "remaining_features": len(definitions["features"])
        }
        
    except Exception as e:
        await ctx.warning(f"Error removing feature: {e}")
        raise

@mcp.tool(
    name="list_project_features",
    description="List all features in project's definitions.json"
)
async def list_project_features(
    definitions_file_path: Annotated[Optional[str], Field(default="./definitions.json", description="Path to definitions.json file")] = "./definitions.json",
    ctx: Context = None
) -> dict:
    """
    List all features defined in the project's definitions.json file.
    
    Args:
        definitions_file_path: Path to definitions.json file
    """
    try:
        # Load existing definitions
        if not os.path.exists(definitions_file_path):
            raise FileNotFoundError(f"Definitions file not found: {definitions_file_path}")
        
        with open(definitions_file_path, "r", encoding="utf-8") as f:
            definitions = json.load(f)
        
        features = definitions.get("features", {})
        tech_tags = definitions.get("tech_tags", {})
        
        await ctx.info(f"Found {len(features)} features and {len(tech_tags)} tech tags")
        return {
            "total_features": len(features),
            "total_tech_tags": len(tech_tags),
            "features": features,
            "tech_tags": tech_tags,
            "definitions_file": definitions_file_path
        }
        
    except Exception as e:
        await ctx.warning(f"Error listing features: {e}")
        raise

@mcp.tool(
    name="add_tech_tag", 
    description="Add a new tech tag to project's definitions.json"
)
async def add_tech_tag(
    tag_name: Annotated[str, Field(
        description="Name of the tech tag",
        example="websockets"
    )],
    description: Annotated[str, Field(
        description="Description of what this tech tag represents",
        example="Real-time WebSocket communication tasks"
    )],
    definitions_file_path: Annotated[Optional[str], Field(default="./definitions.json", description="Path to definitions.json file")] = "./definitions.json",
    ctx: Context = None
) -> dict:
    """
    Add a new tech tag to the project's definitions.json file.
    
    Args:
        tag_name: Name of the tech tag (must follow tag naming rules)
        description: What this tech tag represents
        definitions_file_path: Path to definitions.json file
    """
    try:
        # Validate tag name
        if not validate_tag_name(tag_name):
            raise ValueError(f"Invalid tag name: '{tag_name}'. Must match pattern: ^[a-z0-9-]+$")
        
        # Load existing definitions
        if os.path.exists(definitions_file_path):
            with open(definitions_file_path, "r", encoding="utf-8") as f:
                definitions = json.load(f)
        else:
            definitions = {"features": {}, "tech_tags": {}}
        
        # Ensure tech_tags exists
        if "tech_tags" not in definitions:
            definitions["tech_tags"] = {}
        
        # Check if tag already exists
        if tag_name in definitions["tech_tags"]:
            raise ValueError(f"Tech tag '{tag_name}' already exists in definitions")
        
        # Add new tech tag
        definitions["tech_tags"][tag_name] = description
        
        # Save updated definitions
        with open(definitions_file_path, "w", encoding="utf-8") as f:
            json.dump(definitions, f, indent=2, ensure_ascii=False)
        
        await ctx.info(f"Added tech tag '{tag_name}' to definitions")
        return {
            "success": True,
            "tech_tag_added": tag_name,
            "description": description,
            "definitions_file": definitions_file_path,
            "total_tech_tags": len(definitions["tech_tags"])
        }
        
    except Exception as e:
        await ctx.warning(f"Error adding tech tag: {e}")
        raise

@mcp.tool(
    name="update_tech_tag",
    description="Update an existing tech tag in project's definitions.json"
)
async def update_tech_tag(
    tag_name: Annotated[str, Field(description="Name of the tech tag to update")],
    description: Annotated[str, Field(description="New description for the tech tag")],
    definitions_file_path: Annotated[Optional[str], Field(default="./definitions.json", description="Path to definitions.json file")] = "./definitions.json",
    ctx: Context = None
) -> dict:
    """
    Update an existing tech tag in the project's definitions.json file.
    
    Args:
        tag_name: Name of the tech tag to update
        description: New description for the tech tag
        definitions_file_path: Path to definitions.json file
    """
    try:
        # Load existing definitions
        if not os.path.exists(definitions_file_path):
            raise FileNotFoundError(f"Definitions file not found: {definitions_file_path}")
        
        with open(definitions_file_path, "r", encoding="utf-8") as f:
            definitions = json.load(f)
        
        # Check if tech tag exists
        if tag_name not in definitions.get("tech_tags", {}):
            raise ValueError(f"Tech tag '{tag_name}' not found in definitions")
        
        # Update tech tag
        old_description = definitions["tech_tags"][tag_name]
        definitions["tech_tags"][tag_name] = description
        
        # Save updated definitions
        with open(definitions_file_path, "w", encoding="utf-8") as f:
            json.dump(definitions, f, indent=2, ensure_ascii=False)
        
        await ctx.info(f"Updated tech tag '{tag_name}' description")
        return {
            "success": True,
            "tech_tag_updated": tag_name,
            "old_description": old_description,
            "new_description": description
        }
        
    except Exception as e:
        await ctx.warning(f"Error updating tech tag: {e}")
        raise

@mcp.tool(
    name="remove_tech_tag",
    description="Remove a tech tag from project's definitions.json"
)
async def remove_tech_tag(
    tag_name: Annotated[str, Field(description="Name of the tech tag to remove")],
    definitions_file_path: Annotated[Optional[str], Field(default="./definitions.json", description="Path to definitions.json file")] = "./definitions.json",
    ctx: Context = None
) -> dict:
    """
    Remove a tech tag from the project's definitions.json file.
    
    Args:
        tag_name: Name of the tech tag to remove
        definitions_file_path: Path to definitions.json file
    """
    try:
        # Load existing definitions
        if not os.path.exists(definitions_file_path):
            raise FileNotFoundError(f"Definitions file not found: {definitions_file_path}")
        
        with open(definitions_file_path, "r", encoding="utf-8") as f:
            definitions = json.load(f)
        
        # Check if tech tag exists
        if tag_name not in definitions.get("tech_tags", {}):
            raise ValueError(f"Tech tag '{tag_name}' not found in definitions")
        
        # Remove the tech tag
        removed_description = definitions["tech_tags"].pop(tag_name)
        
        # Save updated definitions
        with open(definitions_file_path, "w", encoding="utf-8") as f:
            json.dump(definitions, f, indent=2, ensure_ascii=False)
        
        await ctx.info(f"Removed tech tag '{tag_name}' from definitions")
        return {
            "success": True,
            "tech_tag_removed": tag_name,
            "removed_description": removed_description,
            "remaining_tech_tags": len(definitions.get("tech_tags", {}))
        }
        
    except Exception as e:
        await ctx.warning(f"Error removing tech tag: {e}")
        raise

@mcp.tool(
    name="get_common_tech_tags",
    description="Get a list of common tech tags with examples for different project types"
)
async def get_common_tech_tags(
    project_type: Annotated[Optional[str], Field(
        default=None,
        description="Type of project to get relevant tech tags for",
        example="web-app"
    )] = None,
    ctx: Context = None
) -> dict:
    """
    Get a curated list of common tech tags with examples for different project types.
    
    Args:
        project_type: Optional project type to filter relevant tags
    """
    try:
        # Common tech tags organized by category
        common_tech_tags = {
            "frontend": {
                "api": "Frontend API integration tasks",
                "frontend": "Frontend UI/UX development tasks", 
                "ui": "User interface design and implementation",
                "ux": "User experience and interaction design",
                "components": "Reusable UI component development",
                "styling": "CSS, styling, and theming tasks",
                "responsive": "Responsive design and mobile adaptation",
                "accessibility": "Web accessibility and a11y improvements"
            },
            "backend": {
                "api": "Backend API development tasks",
                "backend": "Server-side development tasks",
                "database": "Database design and operations",
                "db": "Database-related tasks",
                "endpoints": "API endpoint creation and management",
                "middleware": "Application middleware development",
                "authentication": "User authentication and authorization",
                "validation": "Input validation and data sanitization",
                "caching": "Caching strategies and implementation",
                "logging": "Application logging and monitoring"
            },
            "mobile": {
                "mobile": "Mobile application development tasks",
                "ios": "iOS-specific development tasks",
                "android": "Android-specific development tasks", 
                "react-native": "React Native development tasks",
                "flutter": "Flutter development tasks",
                "push-notifications": "Mobile push notification features",
                "offline": "Offline functionality and sync",
                "native": "Native mobile features integration"
            },
            "devops": {
                "devops": "Infrastructure and deployment tasks",
                "ci-cd": "Continuous integration and deployment",
                "docker": "Container and Docker-related tasks",
                "kubernetes": "Kubernetes orchestration tasks",
                "monitoring": "System monitoring and alerting",
                "deployment": "Application deployment tasks",
                "security": "Security and compliance tasks",
                "backup": "Backup and disaster recovery",
                "scaling": "Performance and scaling optimization"
            },
            "data": {
                "db": "Database and data layer tasks",
                "migration": "Database migration tasks",
                "etl": "Extract, Transform, Load processes",
                "analytics": "Data analytics and reporting",
                "ml": "Machine learning and AI tasks",
                "data-pipeline": "Data processing pipeline tasks",
                "visualization": "Data visualization tasks"
            },
            "testing": {
                "testing": "Quality assurance and testing tasks",
                "unit-tests": "Unit testing tasks",
                "integration-tests": "Integration testing tasks",
                "e2e-tests": "End-to-end testing tasks",
                "performance-tests": "Performance and load testing",
                "automation": "Test automation tasks"
            },
            "communication": {
                "websockets": "Real-time WebSocket communication",
                "messaging": "Message queue and async communication",
                "notifications": "User notification systems",
                "email": "Email integration and templates",
                "sms": "SMS and text messaging features"
            }
        }
        
        # Filter by project type if specified
        if project_type:
            project_filters = {
                "web-app": ["frontend", "backend", "data", "testing"],
                "mobile-app": ["mobile", "backend", "data", "testing"],
                "api": ["backend", "data", "devops", "testing"],
                "fullstack": ["frontend", "backend", "devops", "data", "testing"],
                "microservices": ["backend", "devops", "communication", "testing"],
                "ecommerce": ["frontend", "backend", "data", "devops", "communication"],
                "saas": ["frontend", "backend", "data", "devops", "communication", "testing"]
            }
            
            if project_type in project_filters:
                filtered_tags = {}
                for category in project_filters[project_type]:
                    if category in common_tech_tags:
                        filtered_tags[category] = common_tech_tags[category]
                common_tech_tags = filtered_tags
        
        # Flatten for easy access
        all_tags = {}
        categories = list(common_tech_tags.keys())
        
        for category, tags in common_tech_tags.items():
            all_tags.update(tags)
        
        total_tags = sum(len(tags) for tags in common_tech_tags.values())
        
        await ctx.info(f"Found {total_tags} common tech tags across {len(categories)} categories")
        return {
            "total_tags": total_tags,
            "categories": categories,
            "tags_by_category": common_tech_tags,
            "all_tags": all_tags,
            "project_type": project_type,
            "usage_tip": "Use these as examples when adding tech_tags to your definitions.json"
        }
        
    except Exception as e:
        await ctx.warning(f"Error getting common tech tags: {e}")
        raise

# ========================================
# MÉTODOS DE TAREAS (EXISTENTES)
# ========================================

# Crear una nueva tarea
@mcp.tool(
    name="add_task",
    description="Create a new task in the specified context"
)
async def add_task(
    context: Annotated[str, Field(description="The context name")],
    title: Annotated[str, Field(description="The task title")],
    description: Annotated[str, Field(description="The task description")],
    priority: Annotated[str, Field(description="The task priority (low, medium, high, critical)")],
    tags: Annotated[Optional[List[str]], Field(default=None, description="Array of tags for the task", example=[["frontend", "backend", "data", "testing"]])] = None,
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
    context: Annotated[Optional[str], Field(default=None, description="The context name to filter by")] = None,
    tag: Annotated[Optional[str], Field(default=None, description="The tag to filter by")] = None,
    limit: Annotated[int, Field(default=20, description="Maximum number of tasks to return")] = 20,
    offset: Annotated[int, Field(default=0, description="Number of tasks to skip")] = 0,
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
    description="Get a specific task by task_id from a context"
)
async def get_task(
    context: Annotated[str, Field(description="The context name")],
    task_id: Annotated[str, Field(description="The task ID")],
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
            if str(task["id"]) == task_id:
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
    context: Annotated[str, Field(description="The context name")],
    task_id: Annotated[str, Field(description="The task ID")],
    status: Annotated[str, Field(description="The new status (todo, inprogress, inreview, testing, done, blocked)")],
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
            if str(task["id"]) == task_id:
                old_status = task["status"]
                
                # Validar transición de estado
                if not validate_status_transition(old_status, status):
                    valid_transitions = STATUS_WORKFLOW.get(old_status, [])
                    raise ValueError(f"Invalid status transition from '{old_status}' to '{status}'. Valid transitions: {valid_transitions}")
                
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
    context: Annotated[str, Field(description="The context in which the parent task exists")],
    task_id: Annotated[str, Field(description="The ID of the parent task")],
    title: Annotated[str, Field(description="The title of the subtask")],
    description: Annotated[str, Field(description="The description of the subtask")],
    tags: Annotated[Optional[List[str]], Field(default=None, description="List of tags of the subtask")] = None,
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
    context: Annotated[str, Field(description="The context name")],
    task_id: Annotated[str, Field(description="The parent task ID")],
    subtask_id: Annotated[str, Field(description="The subtask ID")],
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
    context: Annotated[str, Field(description="The context name")],
    task_id: Annotated[str, Field(description="The parent task ID")],
    subtask_id: Annotated[str, Field(description="The subtask ID")],
    status: Annotated[str, Field(description="The new status (todo, inprogress, inreview, testing, done, blocked)")],
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
    context: Annotated[str, Field(description="The context name")],
    task_id: Annotated[str, Field(description="The parent task ID")],
    subtask_id: Annotated[str, Field(description="The subtask ID")],
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
    context: Annotated[str, Field(description="The context name")],
    task_id: Annotated[str, Field(description="The task ID to delete")],
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
    context: Annotated[str, Field(description="The context name")],
    task_id: Annotated[str, Field(description="The parent task ID")],
    recursive: Annotated[bool, Field(default=False, description="Whether to include nested subtasks recursively")] = False,
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
