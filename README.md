# 🚀 Small Task Manager - MCP

Un sistema de gestión de tareas multi-contexto basado en **Model Context Protocol (MCP)** y **FastMCP**, diseñado para organizar y gestionar tareas de manera jerárquica y contextual.

## 📋 Características Principales

- **Gestión Multi-Contexto**: Organiza tareas en diferentes contextos (proyectos, equipos, áreas)
- **Estructura Jerárquica**: Soporte para subtareas anidadas ilimitadas
- **Sistema de Prioridades**: 4 niveles de prioridad (low, medium, high, critical)
- **Estados de Tarea**: Flujo completo desde todo hasta completado
- **Dependencias**: Gestión de dependencias entre tareas y contextos
- **Sistema de Tags**: Categorización y filtrado avanzado
- **API MCP**: Integración nativa con herramientas MCP
- **Validación JSON Schema**: Estructura de datos robusta y validada

## 🏗️ Arquitectura

### Componentes Principales

- **`server.py`**: Servidor MCP principal con FastMCP
- **`schema.json`**: Esquema JSON para validación de datos
- **`uv.lock`**: Gestión de dependencias con uv

### Estructura de Datos

```json
{
  "contexto": {
    "tasks": [
      {
        "id": 1,
        "title": "Título de la tarea",
        "description": "Descripción detallada",
        "priority": "high",
        "status": "inprogress",
        "dependencies": [],
        "subtasks": [...],
        "tags": ["backend", "core"],
        "team": "backend"
      }
    ],
    "metadata": {
      "created": "2025-01-XX...",
      "updated": "2025-01-XX...",
      "description": "Descripción del contexto"
    }
  }
}
```

## 🚀 Instalación

### Prerrequisitos

- Python 3.10+
- uv (gestor de paquetes Python)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd small-taskmanager
   ```

2. **Crear entorno virtual**
   ```bash
   uv venv
   source .venv/bin/activate  # En macOS/Linux
   # o
   .venv\Scripts\activate     # En Windows
   ```

3. **Instalar dependencias**
   ```bash
   uv sync
   ```

4. **Configurar variables de entorno (opcional)**
   ```bash
   export TASKS_FILE_PATH="ruta/personalizada/tasks.json"
   ```

## 🎯 Uso

### Iniciar el Servidor

```bash
python server.py
```

El servidor MCP se iniciará y estará listo para recibir comandos.

### Herramientas Disponibles

#### 1. Crear Tarea (`add_task`)
```python
await add_task(
    context="proyecto",
    title="Implementar autenticación",
    description="Sistema JWT para usuarios",
    priority="high",
    tags=["security", "backend"]
)
```

#### 2. Listar Tareas (`list_tasks`)
```python
await list_tasks(
    context="proyecto",  # opcional
    tag="backend",       # opcional
    limit=20,
    offset=0
)
```

#### 3. Obtener Tarea (`get_task`)
```python
await get_task(
    context="proyecto",
    task_id=1
)
```

#### 4. Actualizar Estado (`update_task_status`)
```python
await update_task_status(
    context="proyecto",
    task_id=1,
    status="done"
)
```

### Estados de Tarea Válidos

- `todo` - Pendiente
- `inprogress` - En progreso
- `inreview` - En revisión
- `testing` - En pruebas
- `done` - Completada
- `blocked` - Bloqueada

### Prioridades Válidas

- `low` - Baja
- `medium` - Media
- `high` - Alta
- `critical` - Crítica

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `TASKS_FILE_PATH` | Ruta del archivo de tareas | `simple-taskmanager/tasks.json` |

### Personalización del Schema

El archivo `schema.json` define la estructura completa de las tareas. Puedes modificarlo para:

- Agregar nuevos campos
- Cambiar validaciones
- Modificar tipos de datos
- Ajustar restricciones

## 📊 Ejemplos de Uso

### Contexto de Desarrollo Backend
```json
{
  "backend": {
    "tasks": [
      {
        "id": 1,
        "title": "API de Usuarios",
        "description": "Endpoints CRUD para gestión de usuarios",
        "priority": "high",
        "status": "inprogress",
        "team": "backend",
        "tags": ["api", "users", "crud"],
        "subtasks": [
          {
            "id": 101,
            "title": "Modelo de Usuario",
            "description": "Definir estructura de datos",
            "status": "done"
          }
        ]
      }
    ],
    "metadata": {
      "description": "Desarrollo del backend de la aplicación"
    }
  }
}
```

### Contexto de Frontend
```json
{
  "frontend": {
    "tasks": [
      {
        "id": 1,
        "title": "Dashboard de Usuario",
        "description": "Interfaz principal del usuario",
        "priority": "medium",
        "status": "todo",
        "dependencies": ["backend:1"],
        "team": "frontend",
        "tags": ["ui", "dashboard", "react"]
      }
    ],
    "metadata": {
      "description": "Desarrollo de la interfaz de usuario"
    }
  }
}
```

## 🧪 Testing

Para ejecutar las pruebas (cuando estén implementadas):

```bash
# Usar base de datos SQLite para tests
pytest --db=sqlite
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Si tienes problemas o preguntas:

- Abre un issue en GitHub
- Revisa la documentación del esquema JSON
- Consulta los ejemplos de uso

## 🔮 Roadmap

- [ ] Interfaz web para gestión visual
- [ ] Sistema de notificaciones
- [ ] Integración con sistemas externos (GitHub, Jira)
- [ ] Reportes y analytics
- [ ] API REST adicional
- [ ] Sistema de permisos y roles
- [ ] Backup y sincronización

## 📚 Referencias

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [JSON Schema](https://json-schema.org/)
- [uv - Fast Python Package Installer](https://github.com/astral-sh/uv)

---

**Desarrollado con ❤️ usando FastMCP y Python**
