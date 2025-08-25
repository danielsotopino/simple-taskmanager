# MCP Usage Guidelines

## Feature-Based Task Management MCP Server

This MCP server manages tasks organized by business features (not technical layers) with automatic validation.

## File Management Policy

ALL file creation and modification MUST be done through MCP tools only. Never edit JSON files manually.

## Available MCP Tools

### Project Initialization
- `init_project` - Creates tasks.json (empty) and definitions.json with features and standard tech_tags
- `create_definitions_template` - Generate definitions.json template

### Project Management
- `add_project_feature` - Add feature to definitions.json
- `update_project_feature` - Update existing feature
- `remove_project_feature` - Remove feature
- `list_project_features` - List all features and tech_tags
- `add_tech_tag` - Add tech tag with description
- `update_tech_tag` - Update tech tag description  
- `remove_tech_tag` - Remove tech tag
- `get_common_tech_tags` - Get 60+ tech tag examples by category/project type

### Task Management
- `add_task` - Create task with validation
- `list_tasks` - List tasks with filters
- `get_task` - Get specific task
- `update_task_status` - Update status with workflow validation
- `delete_task` - Remove task

### Subtask Management
- `add_subtask` - Create subtask with validation
- `list_subtasks` - List task subtasks
- `get_subtask_by_id` - Get specific subtask
- `update_subtask_status` - Update subtask status with workflow validation
- `delete_subtask` - Remove subtask

### Documentation
- `get_usage_guidelines` - Get this guide
- `get_task_schema` - Get tasks.json validation schema
- `get_definitions_schema` - Get definitions.json validation schema  
- `validate_project_files` - Validate project files

## Project Architecture

```
simple-taskmanager/
├── tasks.json        # Project tasks (managed by MCP)
└── definitions.json  # Project features and tech_tags (managed by MCP)
```

## Feature-Based Organization

Organize by business features, not technical layers:

Good:
- Context: "auth" with tasks tagged as [API], [Frontend], [Mobile]
- Context: "payments" with tasks for different tech layers

Bad:
- Context: "frontend" with mixed business features

## Generated definitions.json Structure

```json
{
  "features": {
    "feature-name": {
      "description": "What this business feature does",
      "common_tags": ["tags", "often", "used"],
      "related_contexts": ["other", "connected", "features"]
    }
  },
  "tech_tags": {
    "tag-name": "Description of technical layer/approach"
  }
}
```

### Standard Tech Tags Included by init_project
- api: Backend/server-side API development
- frontend: Client-side UI/UX development  
- mobile: Mobile app development
- backend: Server-side logic and services
- db: Database operations and data layer
- devops: Infrastructure, deployment, CI/CD
- testing: QA, unit tests, integration tests
- security: Security, auth, compliance tasks
- docs: Documentation tasks

## Validation Rules

### Context Names
Pattern: `^[a-z][a-z0-9-]*$`
Valid: "auth", "user-management", "payment-processing"

### Tag Names  
Pattern: `^[a-z0-9-]+$`
Valid: "api", "frontend", "jwt-auth"

### Task Titles
Pattern: `^\\[([A-Z]+)\\]\\s+.+`
Valid: "[API] JWT Authentication", "[FRONTEND] Login form"
Note: This is recommended format, generates warning if not followed

### Status Workflow
- todo → inprogress, blocked
- inprogress → inreview, testing, blocked, done
- inreview → inprogress, testing, done  
- testing → inprogress, done, blocked
- blocked → todo, inprogress
- done → (final state)

### Dependencies
- Same context: numeric ID only
- Cross-context: "context:task_id" or "context:task_id:subtask_id"

## Priority Levels
- critical: Blocking production issues (immediate response)
- high: Core MVP features (current sprint)
- medium: Important enhancements (2-3 sprints)
- low: Nice-to-have features (backlog)

## Usage Examples

Initialize project:
```json
{"tool": "init_project", "arguments": {"project_name": "my-app", "project_features": ["auth", "users", "payments"]}}
```

Create feature-based task:
```json
{"tool": "add_task", "arguments": {"context": "auth", "title": "[API] JWT Authentication", "description": "Implement JWT auth", "priority": "high", "tags": ["api", "jwt", "security"]}}
```

Add project feature:
```json
{"tool": "add_project_feature", "arguments": {"feature_name": "notifications", "description": "User notification system", "common_tags": ["email", "push", "alerts"]}}
```

Get tech tag examples:
```json
{"tool": "get_common_tech_tags", "arguments": {"project_type": "web-app"}}
```

The MCP enforces feature-based organization with automatic validation and workflow compliance.