# 🚀 Feature-Based Task Manager - MCP

Un sistema de gestión de tareas **feature-oriented** basado en **Model Context Protocol (MCP)** y **FastMCP**, diseñado para organizar tareas por funcionalidades de negocio en lugar de capas técnicas.

## 🎯 **Nueva Arquitectura Feature-Based**

### **Antes (Tech-Oriented)** ❌
```
Context: "frontend" 
├── Login task
├── User registration  
├── Dashboard
├── Payment form
```

### **Después (Feature-Oriented)** ✅
```
Context: "auth"
├── [API] JWT authentication
├── [Frontend] Login form
├── [API] User registration endpoint

Context: "payments"
├── [API] Stripe integration
├── [Frontend] Payment form
├── [Mobile] Payment screen
```

## 📋 Características Principales

- **🎯 Gestión Feature-Based**: Contextos = Funcionalidades de negocio completas
- **🏗️ Arquitectura Validada**: Schemas JSON que refuerzan buenas prácticas
- **📚 Auto-Documentación**: MCP server completamente auto-documentado
- **🛠️ Auto-Generación**: Crea automáticamente archivos de proyecto
- **⚡ Validaciones Automáticas**: Refuerza patrones y workflows
- **🔄 Status Workflow**: Transiciones de estado validadas
- **📝 Formato Estandarizado**: Títulos con formato `[TECH_TAG] Descripción`
- **🏷️ Sistema de Tags**: Capas técnicas como tags, no contextos

## 🏗️ Arquitectura

### **Archivos del MCP Server**
```
simple-taskmanager/
├── server.py                  # MCP server con validaciones
├── schema-tasks.json          # Schema para tasks.json
├── schema-definitions.json    # Schema para definitions.json  
├── MCP_USAGE_GUIDELINES.md   # Reglas de implementación
└── README.md                 # Esta documentación
```

### **Archivos del Proyecto Consumidor**
```
mi-proyecto/
├── tasks.json        # Tareas del proyecto (validado por schema-tasks.json)
└── definitions.json  # Features del proyecto (validado por schema-definitions.json)
```

## 🚀 Instalación

### Prerrequisitos
- Python 3.10+
- uv (gestor de paquetes Python)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd simple-taskmanager
   ```

2. **Crear entorno virtual**
   ```bash
   uv venv
   source .venv/bin/activate  # En macOS/Linux
   .venv\Scripts\activate     # En Windows
   ```

3. **Instalar dependencias**
   ```bash
   uv sync
   ```

4. **Iniciar el servidor**
   ```bash
   python server.py
   ```

## 🎯 Uso del MCP

### **🚀 Inicialización de Proyecto**

#### 1. Inicializar nuevo proyecto
```python
await init_project(
    project_name="mi-ecommerce",
    project_features=["auth", "products", "cart", "payments", "notifications"]
)
```

#### 2. Obtener schemas y documentación
```python
# Obtener guías de uso
await get_usage_guidelines()

# Obtener schemas de validación  
await get_task_schema()
await get_definitions_schema()
```

#### 3. Crear template de definitions.json
```python
await create_definitions_template(
    project_features=["user-management", "inventory", "orders"]
)
```

### **📋 Gestión de Tareas**

#### 1. Crear tarea (con validaciones automáticas)
```python
await add_task(
    context="auth",  # ✅ Válido: lowercase con guiones
    title="[API] Implement JWT authentication",  # ✅ Formato correcto
    description="Create JWT token generation and validation system",
    priority="high",
    tags=["jwt", "security", "backend"]  # ✅ Tags válidos
)
```

#### 2. Actualizar estado (con workflow validation)
```python
await update_task_status(
    context="auth",
    task_id=1,
    status="inprogress"  # ✅ Transición válida: todo → inprogress
)
```

#### 3. Crear subtarea
```python
await add_subtask(
    context="auth",
    task_id=1,
    title="[DB] Design user schema", 
    description="Define database structure for users",
    tags=["database", "schema"]
)
```

### **🔍 Validación y Consulta**

#### 1. Validar archivos del proyecto
```python
await validate_project_files(
    tasks_file_path="./tasks.json",
    definitions_file_path="./definitions.json"
)
```

#### 2. Listar tareas con filtros
```python
await list_tasks(
    context="auth",
    tag="security", 
    limit=20
)
```

## ⚡ Validaciones Automáticas

### **🏷️ Context Names**
- **Patrón**: `^[a-z][a-z0-9-]*$`
- **✅ Válido**: `auth`, `user-management`, `payment-processing`
- **❌ Inválido**: `Auth`, `user_management`, `1auth`

### **🏷️ Tag Names** 
- **Patrón**: `^[a-z0-9-]+$`
- **✅ Válido**: `api`, `frontend`, `jwt-auth`
- **❌ Inválido**: `API`, `frontend_ui`, `JWT Auth`

### **📝 Title Format**
- **Patrón**: `^\\[([A-Z]+)\\]\\s+.+`
- **✅ Válido**: `[API] Implement authentication`, `[FRONTEND] Create login form`
- **⚠️ Advertencia**: Si no sigue el formato (no bloquea, solo advierte)

### **🔄 Status Workflow**
```
todo → inprogress, blocked
inprogress → inreview, testing, blocked, done
inreview → inprogress, testing, done  
testing → inprogress, done, blocked
blocked → todo, inprogress
done → (final state)
```

### **🔗 Dependencies**
- **Mismo contexto**: `5` (solo ID numérico)
- **Cross-context**: `auth:1` o `auth:1:5` (context:task:subtask)

## 📊 Ejemplo de definitions.json

```json
{
  "features": {
    "auth": {
      "description": "Authentication and authorization system",
      "common_tags": ["jwt", "login", "security", "sessions"],
      "related_contexts": ["user-management"]
    },
    "user-management": {
      "description": "User lifecycle and profile management", 
      "common_tags": ["users", "profiles", "crud", "permissions"],
      "related_contexts": ["auth"]
    },
    "payments": {
      "description": "Payment processing and financial transactions",
      "common_tags": ["stripe", "billing", "subscriptions"],
      "related_contexts": ["user-management", "notifications"]
    }
  },
  "tech_tags": {
    "api": "Backend/API development tasks",
    "frontend": "Frontend UI/UX tasks", 
    "mobile": "Mobile application tasks",
    "db": "Database and data layer tasks",
    "devops": "Infrastructure and deployment"
  }
}
```

## 📊 Ejemplo de tasks.json

```json
{
  "auth": {
    "tasks": [
      {
        "id": 1,
        "title": "[API] JWT Authentication System",
        "description": "Implement complete JWT authentication",
        "priority": "high",
        "status": "inprogress", 
        "tags": ["api", "jwt", "security"],
        "dependencies": [],
        "creationDate": "2025-08-25T10:00:00",
        "subtasks": [
          {
            "id": 1,
            "title": "[DB] User schema design",
            "description": "Design database structure for users",
            "status": "done",
            "tags": ["db", "schema"],
            "dependencies": [],
            "creationDate": "2025-08-25T10:00:00",
            "subtasks": []
          }
        ]
      }
    ],
    "metadata": {
      "created": "2025-08-25T10:00:00.000Z",
      "updated": "2025-08-25T10:00:00.000Z", 
      "description": "Authentication and authorization features"
    }
  }
}
```

## 📚 Herramientas MCP Disponibles

### **🔧 Documentación y Ayuda**
- `get_usage_guidelines` - Guías completas de uso
- `get_task_schema` - Schema de validación para tasks.json
- `get_definitions_schema` - Schema de validación para definitions.json
- `validate_project_files` - Validar archivos del proyecto

### **🛠️ Generación de Archivos**
- `init_project` - Inicializar proyecto completo
- `create_definitions_template` - Generar definitions.json personalizado

### **📋 Gestión de Tareas**
- `add_task` - Crear tarea (con validaciones)
- `list_tasks` - Listar con filtros
- `get_task` - Obtener tarea específica
- `update_task_status` - Cambiar estado (con workflow validation)
- `delete_task` - Eliminar tarea

### **📋 Gestión de Subtareas**
- `add_subtask` - Crear subtarea (con validaciones)
- `list_subtasks` - Listar subtareas 
- `get_subtask_by_id` - Obtener subtarea específica
- `update_subtask_status` - Cambiar estado (con workflow validation)
- `delete_subtask` - Eliminar subtarea

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `TASKS_FILE_PATH` | Ruta del archivo de tareas | `simple-taskmanager/tasks.json` |

## 🆘 Guías de Implementación

El archivo `MCP_USAGE_GUIDELINES.md` contiene:

- ✅ **Validation Rules**: Patrones exactos para nombres y formatos
- 🔄 **Status Workflow**: Transiciones de estado permitidas  
- 📋 **Priority Guidelines**: Cuándo usar cada prioridad
- 🛠️ **Implementation Requirements**: Qué debe validar el MCP server

## ✨ Beneficios de la Nueva Arquitectura

### **Para Desarrolladores**
- 🎯 **Mejor organización**: Features completos vs. capas técnicas fragmentadas
- 📋 **Tracking claro**: Progreso visible por funcionalidad
- 🔍 **Contexto relevante**: Tareas relacionadas agrupadas
- ⚡ **Validaciones automáticas**: Menos errores, más consistencia

### **Para Equipos**
- 🤝 **Colaboración**: Features cross-functional naturalmente agrupados  
- 📊 **Visibilidad**: Estado de funcionalidades completas vs. fragmentos técnicos
- 🎯 **Priorización**: Decisiones basadas en valor de negocio
- 📈 **Planificación**: Dependencias entre features más claras

### **Para IAs**
- 🧠 **Validación consistente**: Patrones claros y aplicados automáticamente
- 🏷️ **Taxonomía clara**: Features vs. tech_tags bien definidos
- 🔄 **Workflow enforcement**: Transiciones de estado controladas
- 📚 **Auto-documentación**: MCP server completamente auto-explicativo

## 🔮 Roadmap

- [ ] Validación JSON Schema completa con jsonschema library
- [ ] Interfaz web para gestión visual
- [ ] Sistema de templates de features más avanzados
- [ ] Integración con sistemas externos (GitHub, Jira)
- [ ] Reportes de progreso por feature
- [ ] Sistema de notificaciones basado en workflow

## 📚 Referencias

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [JSON Schema](https://json-schema.org/)
- [Feature-Based Development](https://en.wikipedia.org/wiki/Feature-driven_development)

---

**Desarrollado con ❤️ usando FastMCP, JSON Schema y arquitectura Feature-Based**