---
mcp_server: gims-automation
required_tools:
  - mcp__gims_automation__list_scripts
  - mcp__gims_automation__get_script
fallback_skill: /gims-automations-developer
applicability: |
  These instructions apply ONLY when gims-mcp-server is installed, running, and functional.
  To verify availability, check for MCP tools prefixed with 'mcp__gims_automation__'.
  If MCP server is unavailable, use the skill '/gims-automations-developer' instead.
---

# IMPORTANT: Conditional Application

**READ THIS FIRST BEFORE USING ANY INSTRUCTIONS BELOW**

These instructions are for the `gims-mcp-server` MCP server ONLY.

## Applicability Check

1. **Check if MCP tools are available**: Look for tools like `mcp__gims_automation__list_scripts`, `mcp__gims_automation__get_script`, etc.
2. **If MCP tools exist** → Use instructions in this document
3. **If MCP tools DO NOT exist** → IGNORE this document and use skill `/gims-automations-developer` instead

## How to Check

Run this mental check:
- Do I see MCP tools prefixed with `mcp__gims_automation__*`?
- Can I call `mcp__gims_automation__list_scripts`?
- If NO → This document does NOT apply to the current session

## Fallback

If `gims-mcp-server` is not available:
- Use skill: `/gims-automations-developer` (located in `.claude/skills/gims-automations-developer`)
- The skill provides similar functionality without MCP server dependency

## Related Skills

- `/gims-automations-developer` — Development of automation components via CLI scripts (includes `gims_sync.py` for Git sync)

---

# GIMS Automation Development Guide

## Overview

This project uses GIMS Automation MCP Server for developing automation components:
- **Scripts** — automation scenarios (Python code)
- **DataSource Types** — data source type definitions with properties and methods
- **Activator Types** — activator type definitions with code and properties

## MCP Tools Available

### Scripts (11 tools)

| Tool | Purpose |
|------|---------|
| `list_script_folders` | Get folder hierarchy |
| `list_scripts` | List all scripts with paths |
| `get_script` | Get script metadata (code filtered) |
| `get_script_code` | Get script code explicitly |
| `create_script` | Create new script |
| `update_script` | Update script code/name |
| `delete_script` | Delete script |
| `search_scripts` | Search by code/name |
| `create_script_folder` | Create folder |
| `update_script_folder` | Rename/move folder |
| `delete_script_folder` | Delete folder |

### Script Execution Log (1 tool)

| Tool | Purpose |
|------|---------|
| `get_script_execution_log` | Collect script execution logs via SSE streaming |

#### When to Use

Use `get_script_execution_log` after the user manually runs a script in GIMS portal to collect and analyze the execution output. The tool connects to GIMS SSE log stream, waits for log data until an END SCRIPT marker or timeout, and returns the collected log payload for analysis.

#### Workflow

1. User runs a script manually in GIMS portal
2. User asks to collect logs: "Запусти агента для сбора лога скрипта id 5"
3. LLM calls `get_script_execution_log(scr_id=5)`
4. Tool streams log data until END SCRIPT marker or timeout
5. Returns collected log payload for analysis

#### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `scr_id` | Yes | Script ID to collect logs for |
| `timeout` | No | Override default timeout (seconds). Default: 60 seconds from `GIMS_LOG_STREAM_TIMEOUT` |
| `end_markers` | No | Custom end markers array for different termination conditions |
| `filter_pattern` | No | Regex pattern to filter log lines (reduces output size) |
| `keep_timestamp` | No | Keep date/time in output (default: false, timestamps removed) |

#### Best Practices

1. **Default timeout** is 60 seconds from `GIMS_LOG_STREAM_TIMEOUT` environment variable
2. **Log parsing**: Lines are automatically parsed to extract payload (timestamp/level removed unless `keep_timestamp=true`)
3. **Filtering**: Use `filter_pattern` to reduce output size when looking for specific messages (e.g., `ERROR|WARNING`)
4. **Multiple end markers**: Specify multiple `end_markers` for different termination conditions

#### Example Prompts (Russian)

| Prompt | Description |
|--------|-------------|
| "Запусти агента для сбора лога скрипта id 5" | Collect logs for script ID 5 with default timeout |
| "Получи логи работы скрипта id 5 в течение 120 секунд" | Collect logs with custom 120-second timeout |
| "Получи логи скрипта 10, выбери только записи с ERROR" | Collect logs filtered by ERROR pattern |

#### Example Usage

```
# Basic log collection
get_script_execution_log(scr_id=5)

# With custom timeout
get_script_execution_log(scr_id=5, timeout=120)

# Filter only ERROR messages
get_script_execution_log(scr_id=10, filter_pattern="ERROR")

# Keep timestamps in output
get_script_execution_log(scr_id=5, keep_timestamp=true)

# Multiple filter patterns
get_script_execution_log(scr_id=5, filter_pattern="ERROR|WARNING|CRITICAL")
```

### DataSource Types (24 tools)

**Types:** `list_datasource_types`, `get_datasource_type`, `create_datasource_type`, `update_datasource_type`, `delete_datasource_type`

**Properties:** `list_datasource_type_properties`, `create_datasource_type_property`, `update_datasource_type_property`, `delete_datasource_type_property`

**Methods:** `list_datasource_type_methods`, `get_datasource_type_method` (code filtered), `get_datasource_type_method_code`, `create_datasource_type_method`, `update_datasource_type_method`, `delete_datasource_type_method`

**Parameters:** `list_method_parameters`, `create_method_parameter`, `update_method_parameter`, `delete_method_parameter`

**Folders:** `list_datasource_type_folders`, `create_datasource_type_folder`, `update_datasource_type_folder`, `delete_datasource_type_folder`

**Search:** `search_datasource_types`

### Activator Types (15 tools)

**Types:** `list_activator_types`, `get_activator_type` (code filtered), `get_activator_type_code`, `create_activator_type`, `update_activator_type`, `delete_activator_type`

**Properties:** `list_activator_type_properties`, `create_activator_type_property`, `update_activator_type_property`, `delete_activator_type_property`

**Folders:** `list_activator_type_folders`, `create_activator_type_folder`, `update_activator_type_folder`, `delete_activator_type_folder`

**Search:** `search_activator_types`

### References (2 tools)

| Tool | Purpose |
|------|---------|
| `list_value_types` | Get available value types (str, int, bool, etc.) |
| `list_property_sections` | Get property sections for UI grouping |

### Git Sync (8 tools)

Tools для синхронизации компонентов автоматизации с Git-репозиторием.

#### Export Tools

| Tool | Purpose |
|------|---------|
| `export_script` | Экспорт скрипта в Git-формат (meta.yaml + code.py) |
| `export_datasource_type` | Экспорт типа ИД со всеми методами и свойствами |
| `export_activator_type` | Экспорт типа активатора со свойствами и кодом |

#### Import Tools

| Tool | Purpose |
|------|---------|
| `import_script` | Импорт скрипта с валидацией Python синтаксиса |
| `import_datasource_type` | Импорт типа ИД |
| `import_activator_type` | Импорт типа активатора |

#### Utility Tools

| Tool | Purpose |
|------|---------|
| `validate_python_code` | Проверка синтаксиса Python через ast.parse() |
| `compare_with_git` | Сравнение версии в GIMS с Git (по updated_at/exported_at) |

#### Tool Parameters

**export_script:**
- `script_id` (int, optional) — ID скрипта
- `script_name` (string, optional) — Имя скрипта (альтернатива ID)

**import_script:**
- `meta_yaml` (string, required) — Содержимое meta.yaml
- `code` (string, required) — Python код скрипта
- `target_name` (string, optional) — Имя для создания (если отличается от meta)
- `target_folder_id` (int, optional) — ID папки для сохранения
- `update_existing` (bool, default: false) — Обновить существующий скрипт

**export_datasource_type / export_activator_type:**
- `type_id` (int, optional) — ID типа
- `type_name` (string, optional) — Имя типа (альтернатива ID)

**import_datasource_type / import_activator_type:**
- `files` (object, required) — Словарь файлов {путь: содержимое}
- `target_name` (string, optional) — Имя для создания
- `update_existing` (bool, default: false) — Обновить существующий

**validate_python_code:**
- `code` (string, required) — Python код для проверки

**compare_with_git:**
- `component_type` (enum: script/datasource_type/activator_type, required)
- `gims_name` (string, required) — Имя компонента в GIMS
- `git_exported_at` (string, required) — Дата экспорта из Git meta.yaml

## Development Workflow

### Working with Scripts

1. **Explore existing scripts:**
   ```
   list_script_folders  → get folder structure
   list_scripts         → see all scripts with paths
   search_scripts       → find scripts by code/name
   ```

2. **Read and understand:**
   ```
   get_script(script_id=X)       → get script metadata (code filtered as [FILTERED])
   get_script_code(script_id=X)  → get script code (use when you need to read/analyze code)
   ```

3. **Create/Update:**
   ```
   create_script(name="my_script", code="...", folder_id=X)
   update_script(script_id=X, code="...")
   ```

### Working with DataSource Types

1. **Explore existing types:**
   ```
   list_datasource_type_folders  → folder structure
   list_datasource_types         → all types
   get_datasource_type(type_id=X) → type with properties, methods (code filtered)
   get_datasource_type(type_id=X, include_properties=false, include_methods=false) → only basic type info
   get_datasource_type_method(method_id=X) → method metadata and parameters (code filtered)
   get_datasource_type_method_code(method_id=X) → method code (use when you need to read/analyze code)
   ```

2. **Before creating properties:**
   ```
   list_value_types        → get value_type_id for property
   list_property_sections  → get section_name_id for UI grouping
   ```

3. **Create type with components:**
   ```
   create_datasource_type(name="MyType", description="...")
   create_datasource_type_property(mds_type_id=X, name="host", label="host", value_type_id=1, section_name_id=1)
   create_datasource_type_method(mds_type_id=X, name="connect", label="connect", code="...")
   create_method_parameter(method_id=X, label="timeout", value_type_id=2)
   ```

### Working with Activator Types

1. **Explore existing types:**
   ```
   list_activator_type_folders  → folder structure
   list_activator_types         → all types
   get_activator_type(type_id=X) → type metadata and properties (code filtered as [FILTERED])
   get_activator_type(type_id=X, include_properties=false) → only type metadata (code filtered)
   get_activator_type_code(type_id=X) → activator code (use when you need to read/analyze code)
   ```

2. **Create type:**
   ```
   create_activator_type(name="MyActivator", code="...", description="...")
   create_activator_type_property(activator_type_id=X, name="interval", label="interval", ...)
   ```

### Git Sync Workflow

Git Sync позволяет синхронизировать компоненты GIMS с внешним Git-репозиторием для версионирования и переноса между системами.

**ВАЖНО:** Git операции выполняются через Bash tool, не через MCP. Перед коммитами проверяй git config.

#### Git Configuration Check

Перед выполнением git commit **ОБЯЗАТЕЛЬНО** проверь конфигурацию:

```bash
git config user.name
git config user.email
```

Если не настроено, предложи пользователю:

```bash
# Глобально
git config --global user.name "Имя Пользователя"
git config --global user.email "user@example.com"

# Или локально для репозитория
git config user.name "Имя Пользователя"
git config user.email "user@example.com"
```

#### Git Repository Structure

```
automation-components/
├── scripts/
│   └── <script_folder>/
│       ├── meta.yaml
│       └── code.py
├── datasource_types/
│   └── <type_folder>/
│       ├── meta.yaml
│       ├── properties.yaml
│       └── methods/
│           └── <method_label>/
│               ├── meta.yaml
│               ├── code.py
│               └── params.yaml
└── activator_types/
    └── <type_folder>/
        ├── meta.yaml
        ├── code.py
        └── properties.yaml
```

#### Export to Git Workflow

1. **Экспортируй компонент через MCP tool:**
   ```
   export_script(script_name="ICMP Monitor")
   # Результат: {files: {"meta.yaml": "...", "code.py": "..."}, suggested_folder: "icmp_monitor"}
   ```

2. **Создай папку и сохрани файлы:**
   ```bash
   mkdir -p automation-components/scripts/icmp_monitor
   ```
   ```
   # Write meta.yaml и code.py содержимое из результата export_script
   ```

3. **Git операции:**
   ```bash
   cd automation-components
   git add scripts/icmp_monitor/
   git commit -m "Export script 'ICMP Monitor'"
   git push origin main
   ```

#### Import from Git Workflow

1. **Получи последние изменения:**
   ```bash
   git pull origin main
   ```

2. **Прочитай файлы компонента:**
   ```
   # Read: automation-components/scripts/icmp_monitor/meta.yaml
   # Read: automation-components/scripts/icmp_monitor/code.py
   ```

3. **Импортируй через MCP tool:**
   ```
   import_script(meta_yaml="<содержимое meta.yaml>", code="<содержимое code.py>")
   # или с обновлением существующего:
   import_script(meta_yaml="...", code="...", update_existing=true)
   ```

#### Sync Decision Workflow

Для определения направления синхронизации:

1. **Сравни версии:**
   ```
   compare_with_git(component_type="script", gims_name="ICMP Monitor", git_exported_at="2026-01-19T10:30:00Z")
   ```

2. **Результаты:**
   - `status: "gims_newer"` → рекомендуется export
   - `status: "git_newer"` → рекомендуется import
   - `status: "in_sync"` → синхронизировано
   - `status: "not_found_in_gims"` → рекомендуется import

#### Conflict Resolution

При конфликте имён (скрипт уже существует):

1. **Обновить существующий:**
   ```
   import_script(..., update_existing=true)
   ```

2. **Создать с другим именем:**
   ```
   import_script(..., target_name="ICMP Monitor Imported")
   ```

При конфликте в Git-репозитории (папка с таким именем уже существует):

1. Спросить пользователя какую версию использовать
2. Предложить альтернативные имена папок (например, `icmp_monitor_prod`, `icmp_monitor_dev`)

#### Validation

**ВАЖНО:** Перед импортом всегда проверяй синтаксис Python:

```
validate_python_code(code="<python_code>")
# Результат: {"valid": true, "error": null}
# или: {"valid": false, "error": "Синтаксическая ошибка в строке 5: ..."}
```

Импорт автоматически отклоняется если код не проходит валидацию.

## Code Conventions

### Scripts

- Scripts are Python code executed by Celery tasks in GIMS sandbox
- Use `print_help()` to see available built-in functions
- Access datasources via `ds` variable
- Access activator properties via `props` variable

**IMPORTANT: Returning values from scripts**

If a script needs to return a computed value (as result of Celery task), assign the value to the special variable `return_result_` at the end of the script:

```python
# Script that computes and returns a value
data = ds.my_datasource.fetch_data()
processed = process_data(data)

# Return value - MUST use return_result_ variable
return_result_ = processed
```

The `return_result_` variable is the ONLY way to return a value from a script. Do NOT use `return` statement at script level.

### DataSource Type Methods

**CRITICAL: Method code structure**

Methods do NOT use `return` statement to return values. Instead:
1. Define **input parameters** (`input_type=true`) - passed when method is called
2. Define **output parameters** (`input_type=false`) - returned as dict from method
3. In method code, assign values to output parameter variables

```python
# Method with input parameter 'promql' and output parameter 'result'
# Input: promql (string) - available as variable
# Output: result (any) - must be assigned

import requests

response = requests.get(
    f"{self.url}/api/v1/query",
    params={"query": promql},
    timeout=self.timeout
)

# Assign to output parameter - this is returned as {"result": ...}
result = response.json()["data"]["result"]
```

**Key rules for method code:**

1. **NO `return` statement** at method level - values are returned via output parameters
2. **Access datasource type properties** via `self.property_label` (e.g., `self.url`, `self.timeout`)
3. **Call other methods** of same type via `self.method_name(param=value)` - returns dict if method has output params
4. **Output parameters MUST be assigned** - always assign values to all output parameters
5. **Internal helper functions** can be defined, but they must NOT use `self`

```python
# Example: Method calling another method
# Method: query_range with inputs (promql, start, end, step) and output (result)

def format_time(timestamp):
    # Internal helper - no self allowed here
    return timestamp.isoformat()

response = requests.get(
    f"{self.url}/api/v1/query_range",
    params={
        "query": promql,
        "start": format_time(start),
        "end": format_time(end),
        "step": step
    },
    timeout=self.timeout
)

# Assign output parameter
result = response.json()["data"]["result"]
```

**Calling datasource methods from scripts/activators:**

```python
# Access datasource by name, pass parameters as keyword arguments
response = gims_fault_ds.list_alerts(filter=alert_filter, limit=limit_alarms)
# response is a dict: {"result": [...], "count": 100}
```

### Activator Type Code

**CRITICAL: Property access in activators**

Activator properties are accessed **directly by label name** (NOT through `self` or `props`):

```python
# Activator with properties: interval (int), target_url (str), threshold (int)

# CORRECT - access properties directly by label
if interval > 0:
    response = requests.get(target_url, timeout=30)
    if response.status_code != 200 and threshold > 0:
        log.warning(f"Check failed: {response.status_code}")

# WRONG - do not use self or props
# self.interval  - WRONG
# props.interval - WRONG
```

**Activator structure:**

```python
# Properties are available as variables (by label name)
# ds - access to datasources
# log - logger

def check_health():
    """Internal function - can be used for logic organization."""
    # Access datasource methods
    result = ds.my_datasource.get_status()
    return result.get("status") == "ok"

# Main activator logic
if check_health():
    log.info("System is healthy")
else:
    log.error("System check failed")
```

### Value Type Restrictions

**IMPORTANT:** Do NOT use these value types for properties and method parameters:
- `Список` (List) - causes errors
- `Справочник` (Dictionary) - causes errors

**Use instead:**
- `Объект` (Object) - works correctly for complex data structures

## GIMS Built-in Functions Reference

Все сценарии и активаторы GIMS выполняются в специальном sandbox-окружении с предопределёнными переменными и функциями. Код пишется на Python 3.10.

### Встроенные переменные сценариев

| Переменная | Тип | Описание |
|------------|-----|----------|
| `script_id` | int | ID сценария из БД |
| `script_name` | str | Имя сценария из БД |
| `activator_id` | int/None | ID активатора (None, если запущен из редактора портала) |
| `activator_name` | str | Имя активатора (пустое, если запущен из редактора) |
| `activator_server_name` | str | Имя сервера активатора из Конфигуратора |
| `activator_server_address` | str | Адрес сервера активатора из Конфигуратора |
| `cluster_id` | int | ID кластера из БД |
| `server_id` | int | ID сервера из БД |

### Встроенные переменные активаторов

| Переменная | Тип | Описание |
|------------|-----|----------|
| `activator_id` | int | ID активатора из БД |
| `activator_name` | str | Имя активатора из БД |
| `cluster_id` | int | ID кластера из БД |
| `cluster_name` | str | Имя кластера из БД |
| `server_id` | int | ID сервера из БД |

### Функции логирования

Доступны в сценариях, активаторах и методах источников данных.

| Функция | Описание |
|---------|----------|
| `set_level_log(level)` | Установить уровень логирования. `level`: `'DEBUG'`, `'INFO'`, `'WARNING'`, `'ERROR'` |
| `set_log_prefix(prefix='', is_add_obj_name=False)` | Установить префикс для всех сообщений лога |
| `get_log_prefix()` | Получить текущий префикс сообщений |
| `print(text)` | Вывести сообщение с уровнем INFO (функция переопределена в GIMS) |
| `print_err(text)` | Вывести сообщение с уровнем ERROR |
| `print_wrn(text)` | Вывести сообщение с уровнем WARNING |
| `print_dbg(text)` | Вывести сообщение с уровнем DEBUG |

**Пример:**
```python
set_level_log('DEBUG')
set_log_prefix('[MyScript]', is_add_obj_name=True)
print('Начало обработки')  # INFO: [MyScript] Начало обработки
print_dbg(f'Параметры: {params}')  # DEBUG: [MyScript] Параметры: {...}
print_err('Ошибка подключения')  # ERROR: [MyScript] Ошибка подключения
```

### Функции импорта и загрузки

| Функция | Описание |
|---------|----------|
| `load_data_sources(ids_list=None, names_list=None, like_name=None, type_names_list=None, like_type_name=None)` | Загрузить массив источников данных по фильтрам |
| `import_script(script_name)` | Импортировать сценарий как Python-модуль. Возвращает имя модуля для использования |
| `include_script(script_name, propagate_exit=True, only_return_code=False)` | Включить код сценария в текущую точку выполнения |
| `get_script_run_info()` | (Только в активаторах) Получить информацию о прикреплённом сценарии: `{script_id, script_name, script_exec_timeout}` |

**Пример import_script:**
```python
# Импорт сценария как модуля
utils = import_script('common_utils')
result = utils.process_data(data)
```

**Пример include_script:**
```python
# Включение кода сценария (выполняется в текущем контексте)
include_script('init_variables')
# Переменные из init_variables теперь доступны
print(initialized_var)
```

**Пример load_data_sources:**
```python
# Загрузить все источники данных типа "Prometheus"
prometheus_sources = load_data_sources(type_names_list=['Prometheus'])
for ds in prometheus_sources:
    result = ds.query(promql='up')
```

### Функции работы со сценариями

| Функция | Описание |
|---------|----------|
| `script_run2(is_result=False, exec_timeout=0, script_marker=None, is_async_run=True, is_result_exec_state=False, kwargs=None, no_data_source=False)` | Выполнить сценарий. Возвращает `task_id` (async) или `result` (sync) |
| `script_ready(task_id)` | Проверить статус выполнения: `True` — выполнен, `False` — выполняется |
| `script_get_res(task_id, timeout=None, is_return_ready_result=False)` | Получить результат (`return_result_`) с ожиданием |
| `script_get_res_with_while(task_id, timeout=None, delay=1)` | Получить результат с polling (цикл проверки) |
| `script_kill(task_id)` | Завершить задачу Celery: `True` — сигнал отправлен |
| `script_run_chain(scripts_chain_json)` | Выполнить цепочку сценариев |
| `get_queued_tasks()` | Получить количество задач в очереди |

**Важно:** В сценариях использование `script_run2` с `is_async_run=True` может вызвать DeadLock. Безопасное использование: `is_async_run=False` с получением результата.

**Пример асинхронного запуска (в активаторе):**
```python
# Запустить сценарий асинхронно
task_id = script_run2(script_marker='process_data', kwargs={'batch_id': 123})

# Дождаться результата
result = script_get_res_with_while(task_id, timeout=300, delay=5)
print(f'Результат: {result}')
```

**Пример синхронного запуска:**
```python
# Запустить и сразу получить результат
result = script_run2(
    script_marker='calculate_metrics',
    is_result=True,
    is_async_run=False,
    exec_timeout=60,
    kwargs={'metric_type': 'cpu'}
)
```

### Функции кэширования

| Функция | Описание |
|---------|----------|
| `set_cache(key, value, timeout=None)` | Сохранить значение в локальном кэше. `timeout` — время жизни в секундах |
| `get_cache(key, default=None)` | Получить значение из кэша. `default` — значение по умолчанию |
| `delete_cache(key)` | Удалить ключ из кэша |

**Пример:**
```python
# Кэширование результата тяжёлого запроса
cached_data = get_cache('heavy_query_result')
if cached_data is None:
    cached_data = perform_heavy_query()
    set_cache('heavy_query_result', cached_data, timeout=300)  # 5 минут
```

### Исключения GIMS

При работе со встроенными функциями могут возникать следующие исключения:

| Исключение | Когда возникает |
|------------|-----------------|
| `ScriptRunError` | Ошибка запуска сценария через `script_run2` |
| `ScriptReadyError` | Ошибка проверки статуса через `script_ready` |
| `ScriptGetResultError` | Ошибка получения результата |
| `ScriptGetResultTimeout` | Таймаут ожидания результата |
| `ScriptKillError` | Ошибка завершения задачи |
| `ScriptRunChainError` | Ошибка выполнения цепочки сценариев |
| `ImportScriptError` | Ошибка импорта сценария через `import_script` |
| `IncludeScriptError` | Ошибка включения сценария через `include_script` |
| `LoadDataSourcesError` | Ошибка загрузки источников данных |

**Пример обработки:**
```python
try:
    task_id = script_run2(script_marker='risky_script', is_async_run=True)
    result = script_get_res(task_id, timeout=60)
except ScriptGetResultTimeout:
    print_err('Сценарий не успел выполниться за 60 секунд')
    script_kill(task_id)
except ScriptRunError as e:
    print_err(f'Ошибка запуска: {e}')
```

## Development Recommendations

### Рекомендации по разработке кода GIMS

#### Разбиение большого кода

Если код сценария слишком большой (высокий расход контекста LLM при загрузке), рекомендуется разбить его:

1. **На части через `include_script`** — код включается в текущий контекст:
   ```python
   include_script('config_loader')      # загружает конфигурацию
   include_script('data_processor')     # обрабатывает данные
   # Переменные из обоих сценариев доступны здесь
   ```

2. **На модули через `import_script`** — код импортируется как Python-модуль:
   ```python
   utils = import_script('string_utils')
   validators = import_script('data_validators')

   clean_data = utils.normalize(raw_data)
   if validators.is_valid(clean_data):
       process(clean_data)
   ```

#### Параллельное выполнение

Активатор может запускать сценарии как отдельные Celery tasks через `script_run2`:

```python
# Запуск нескольких сценариев параллельно
task_ids = []
for batch in data_batches:
    task_id = script_run2(
        script_marker='process_batch',
        is_async_run=True,
        kwargs={'batch': batch}
    )
    task_ids.append(task_id)

# Сбор результатов
results = []
for task_id in task_ids:
    result = script_get_res_with_while(task_id, timeout=300)
    results.append(result)
```

#### Диагностика и отладка

Используйте функции логирования для диагностики:

```python
set_level_log('DEBUG')  # Включить debug-вывод

print_dbg(f'Входные параметры: {params}')
print(f'Обработано {count} записей')
print_wrn('Обнаружены дубликаты, пропускаем')
print_err(f'Критическая ошибка: {error}')
```

### Рекомендации по взаимодействию с пользователем

#### Проверка библиотек

Если код использует `import`, рекомендуйте проверить наличие библиотек. Установленные библиотеки см. в `installed-requirements.txt`. Для установки недостающих:

```bash
uv pip install --no-cache <package_name>
```

#### Планирование больших задач

Для больших задач всегда:
1. Выполнить анализ задачи
2. Спланировать и спроектировать решение
3. Предложить пользователю план реализации
4. После подтверждения и уточнения дискуссионных моментов — разработать код

### Доступ к системным функциям из методов источников данных

В коде методов источников данных доступны системные функции того окружения, откуда вызываются методы (из кода активатора или сценария). Это означает, что методы могут использовать `print`, `print_err`, `set_cache` и другие функции.

## Best Practices

1. **Always explore first** — use `list_*` and `get_*` before making changes
2. **Search before creating** — use `search_*` to find existing code to reuse
3. **Get references** — always call `list_value_types` and `list_property_sections` before creating properties
4. **Use meaningful names** — `label` is code identifier (English, snake_case), `name` is display name (can be localized)
5. **Test incrementally** — create minimal code first, then expand
6. **Use folders** — organize scripts/types in logical folder hierarchy

## Common Patterns

### Find and modify script
```
search_scripts(query="health_check", search_in="name")
get_script(script_id=<found_id>)           # get metadata (code: [FILTERED])
get_script_code(script_id=<found_id>)      # get actual code when needed
update_script(script_id=<found_id>, code="<new_code>")
```

### Create complete datasource type with Prometheus example
```
list_value_types()  # note: str=4, int=2, bool=3, object=6 (use object instead of list/dict!)
list_property_sections()  # note: Основные=1, Подключение=2

# 1. Create the type
create_datasource_type(name="Prometheus", description="Prometheus monitoring")
# type_id = <returned_id>

# 2. Create properties (accessed via self.label in method code)
create_datasource_type_property(mds_type_id=type_id, name="URL", label="url", value_type_id=4, section_name_id=2, is_required=True, description="URL Prometheus сервера")
create_datasource_type_property(mds_type_id=type_id, name="Timeout", label="timeout", value_type_id=2, section_name_id=2, default_value="30", description="Таймаут запросов в секундах")

# 3. Create method with proper code structure
# Method code - NO return statement, assign to output parameter
method_code = '''
import requests

response = requests.get(
    f"{self.url}/api/v1/query",
    params={"query": promql},
    timeout=self.timeout
)
response.raise_for_status()

# Assign output parameter (returned as {"result": ...})
result = response.json()["data"]["result"]
'''

create_datasource_type_method(mds_type_id=type_id, name="Query", label="query", code=method_code, description="Выполнить PromQL запрос")
# method_id = <returned_id>

# 4. Create method parameters
# Input parameter - passed when calling the method
create_method_parameter(method_id=method_id, label="promql", value_type_id=4, input_type=True, description="PromQL запрос")
# Output parameter - returned from method as dict key
create_method_parameter(method_id=method_id, label="result", value_type_id=6, input_type=False, description="Результат запроса")
```

### Create activator type
```
# Activator properties accessed directly by label (NOT through self)
activator_code = '''
# Properties: check_interval, target_url are available as variables

import requests

if check_interval > 0:
    try:
        response = requests.get(target_url, timeout=30)
        if response.status_code == 200:
            log.info("Health check passed")
        else:
            log.warning(f"Health check failed: {response.status_code}")
    except Exception as e:
        log.error(f"Health check error: {e}")
'''

create_activator_type(name="HealthCheck", code=activator_code, description="Периодическая проверка здоровья")
# activator_type_id = <returned_id>

# Properties - accessed directly by label name in code
create_activator_type_property(activator_type_id=activator_type_id, name="Интервал проверки", label="check_interval", value_type_id=2, section_name_id=1, default_value="60")
create_activator_type_property(activator_type_id=activator_type_id, name="URL для проверки", label="target_url", value_type_id=4, section_name_id=1, is_required=True)
```

### Search and analyze code
```
search_datasource_types(query="execute", search_in="code")  # find methods using execute
search_activator_types(query="schedule", search_in="code")  # find activators with scheduling
search_scripts(query="prometheus", search_in="both")  # find prometheus-related scripts
```

### Git Sync: Full synchronization workflow

```
# 1. Проверить git config
git config user.name && git config user.email

# 2. Получить последние изменения
git pull origin main

# 3. Определить направление синхронизации для скрипта
compare_with_git(component_type="script", gims_name="ICMP Monitor", git_exported_at="2026-01-18T15:00:00Z")
# Результат: {"status": "gims_newer", "recommendation": "export"}

# 4a. Если GIMS новее — экспорт
export_script(script_name="ICMP Monitor")
# Сохранить файлы в Git-репозиторий через Write tool
# git add, commit, push

# 4b. Если Git новее — импорт
# Прочитать meta.yaml и code.py через Read tool
import_script(meta_yaml="...", code="...", update_existing=true)
```

### Git Sync: Export script to new Git folder

```
# 1. Экспорт компонента
export_script(script_name="Health Check")
# Результат: {files: {"meta.yaml": "...", "code.py": "..."}, suggested_folder: "health_check"}

# 2. Проверить нет ли конфликта папок в Git
ls automation-components/scripts/

# 3. Если папка существует - спросить пользователя
# "Папка health_check уже существует. Варианты:
#  - Перезаписать существующую
#  - Создать health_check_v2
#  - Создать health_check_prod"

# 4. Создать папку и сохранить файлы
mkdir -p automation-components/scripts/health_check_prod
# Write: automation-components/scripts/health_check_prod/meta.yaml
# Write: automation-components/scripts/health_check_prod/code.py

# 5. Git операции
git add automation-components/scripts/health_check_prod/
git commit -m "Export script 'Health Check' to health_check_prod"
git push origin main
```

### Git Sync: Import script from specific Git folder

```
# Пользователь: "импортируй скрипт из health_check_prod"

# 1. Прочитать файлы
# Read: automation-components/scripts/health_check_prod/meta.yaml
# Read: automation-components/scripts/health_check_prod/code.py

# 2. Проверить синтаксис
validate_python_code(code="<содержимое code.py>")
# Результат: {"valid": true}

# 3. Импортировать
import_script(meta_yaml="<содержимое meta.yaml>", code="<содержимое code.py>")
# Если скрипт существует - спросить обновить или создать копию
```

### Git Sync: Export datasource type with methods

```
# 1. Экспорт типа ИД
export_datasource_type(type_name="Prometheus Monitor")
# Результат: {files: {
#   "meta.yaml": "...",
#   "properties.yaml": "...",
#   "methods/query/meta.yaml": "...",
#   "methods/query/code.py": "...",
#   "methods/query/params.yaml": "..."
# }, suggested_folder: "prometheus_monitor"}

# 2. Создать структуру папок
mkdir -p automation-components/datasource_types/prometheus_monitor/methods/query

# 3. Сохранить все файлы
# Write: каждый файл из результата

# 4. Git операции
git add automation-components/datasource_types/prometheus_monitor/
git commit -m "Export datasource type 'Prometheus Monitor'"
git push origin main
```

## Error Handling

- **401 with "токен обновления недействителен"**: Refresh token invalid — ask user to verify their account is active and get new tokens from browser (Developer Tools → Application → Cookies → `access_token` and `refresh_token`)
- **401**: Access token expired — automatic refresh using refresh token (handled by MCP server)
- **403**: Permission denied — user lacks required permissions
- **404**: Entity not found — verify ID exists
- **400**: Validation error — check required fields and data types

## Configuration

### Project-level configuration (`.mcp.json`)

```json
{
  "mcpServers": {
    "gims-automation": {
      "command": "gims-mcp-server",
      "env": {
        "GIMS_URL": "https://gims.example.com",
        "GIMS_ACCESS_TOKEN": "<JWT_ACCESS_TOKEN>",
        "GIMS_REFRESH_TOKEN": "<JWT_REFRESH_TOKEN>"
      },
      "defer_loading": true
    }
  }
}
```

### Self-signed certificates

For servers with self-signed SSL certificates, add `GIMS_VERIFY_SSL`:

```json
{
  "mcpServers": {
    "gims-automation": {
      "command": "gims-mcp-server",
      "env": {
        "GIMS_URL": "https://gims.example.com",
        "GIMS_ACCESS_TOKEN": "<JWT_ACCESS_TOKEN>",
        "GIMS_REFRESH_TOKEN": "<JWT_REFRESH_TOKEN>",
        "GIMS_VERIFY_SSL": "false"
      }
    }
  }
}
```

Or via CLI: `gims-mcp-server --verify-ssl false`

### Response size limit

To control the maximum response size (useful for managing context window), use `GIMS_MAX_RESPONSE_SIZE_KB`:

```json
{
  "mcpServers": {
    "gims-automation": {
      "command": "gims-mcp-server",
      "env": {
        "GIMS_URL": "https://gims.example.com",
        "GIMS_ACCESS_TOKEN": "<JWT_ACCESS_TOKEN>",
        "GIMS_REFRESH_TOKEN": "<JWT_REFRESH_TOKEN>",
        "GIMS_MAX_RESPONSE_SIZE_KB": "20"
      }
    }
  }
}
```

Or via CLI: `gims-mcp-server --max-response-size 20`

**Token estimation:**
- 1KB ~ 250 tokens (ASCII/English)
- 1KB ~ 170 tokens (Cyrillic/Russian)
- Default: 10KB (~2500 tokens)

### defer_loading option

When `"defer_loading": true` is set:
- Tool definitions are loaded on-demand, not at startup
- Saves ~1-2K tokens of context per session
- Recommended when using multiple MCP servers
- Trade-off: slight latency on first call to each tool
