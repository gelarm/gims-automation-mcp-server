# GIMS Automation MCP Server

MCP (Model Context Protocol) сервер для интеграции coding-агентов (Claude Code CLI и др.) с системой GIMS Automation.

## Возможности

- Разработка сценариев автоматизации (Scripts)
- Разработка типов источников данных (MultyDataSourceType) с методами и свойствами
- Разработка типов активаторов (ActivatorType) с кодом и свойствами
- Поиск по коду и имени
- Автоматическое обновление токена доступа при истечении срока действия

## Установка

### Из GitLab

```bash
pip install git+ssh://git@gitlab.gelarm.ru/gelarm/gims-automation-mcp-server.git
```

### Для разработки

```bash
git clone git@gitlab.gelarm.ru:gelarm/gims-automation-mcp-server.git
cd gims-automation-mcp-server
pip install -e ".[dev]"
```

## Конфигурация

### Claude Code CLI

Создайте файл `.mcp.json` в корне вашего проекта:

```json
{
  "mcpServers": {
    "gims-automation": {
      "command": "gims-mcp-server",
      "env": {
        "GIMS_URL": "https://gims.example.com",
        "GIMS_ACCESS_TOKEN": "<JWT_ACCESS_TOKEN>",
        "GIMS_REFRESH_TOKEN": "<JWT_REFRESH_TOKEN>"
      }
    }
  }
}
```

#### Self-signed сертификаты

Для работы с серверами с самоподписанными сертификатами добавьте `GIMS_VERIFY_SSL`:

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

### Параметры

| Параметр | CLI | Env | Описание |
|----------|-----|-----|----------|
| URL | `--url` | `GIMS_URL` | URL GIMS сервера |
| Access Token | `--access-token` | `GIMS_ACCESS_TOKEN` | JWT токен доступа |
| Refresh Token | `--refresh-token` | `GIMS_REFRESH_TOKEN` | JWT токен обновления |
| Verify SSL | `--verify-ssl` | `GIMS_VERIFY_SSL` | Проверка SSL сертификата (по умолчанию: true) |
| Max Response Size | `--max-response-size` | `GIMS_MAX_RESPONSE_SIZE_KB` | Лимит размера ответа в КБ (по умолчанию: 10). Примерный пересчёт в токены: 1КБ ≈ 250 токенов (ASCII) или 170 токенов (кириллица) |

### Получение токенов

1. Войдите в GIMS через веб-интерфейс
2. Откройте Developer Tools → Application → Cookies
3. Скопируйте значения `access_token` и `refresh_token`

### Автоматическое обновление токена

MCP сервер автоматически обновляет access token при получении ошибки 401 (токен истёк). Для этого используется refresh token.

При недействительном refresh token выводится сообщение:
```
Ошибка аутентификации: токен обновления недействителен. Проверьте учётную запись и получите новые токены в GIMS.
```

## Доступные Tools (48)

### Scripts (10 tools)

| Tool | Описание |
|------|----------|
| `list_script_folders` | Список папок скриптов с иерархией |
| `create_script_folder` | Создать папку |
| `update_script_folder` | Обновить папку |
| `delete_script_folder` | Удалить папку |
| `list_scripts` | Список скриптов (с фильтром по папке) |
| `get_script` | Получить скрипт с кодом |
| `create_script` | Создать скрипт |
| `update_script` | Обновить скрипт |
| `delete_script` | Удалить скрипт |
| `search_scripts` | Поиск по коду и/или имени |

### DataSource Types (22 tools)

#### Папки (4 tools)

| Tool | Описание |
|------|----------|
| `list_datasource_type_folders` | Список папок типов ИД |
| `create_datasource_type_folder` | Создать папку |
| `update_datasource_type_folder` | Обновить папку |
| `delete_datasource_type_folder` | Удалить папку |

#### Типы (5 tools)

| Tool | Описание |
|------|----------|
| `list_datasource_types` | Список типов ИД |
| `get_datasource_type` | Получить тип с properties и methods |
| `create_datasource_type` | Создать тип |
| `update_datasource_type` | Обновить тип |
| `delete_datasource_type` | Удалить тип |

#### Свойства (4 tools)

| Tool | Описание |
|------|----------|
| `list_datasource_type_properties` | Список свойств типа |
| `create_datasource_type_property` | Добавить свойство |
| `update_datasource_type_property` | Обновить свойство |
| `delete_datasource_type_property` | Удалить свойство |

#### Методы (4 tools)

| Tool | Описание |
|------|----------|
| `list_datasource_type_methods` | Список методов типа |
| `create_datasource_type_method` | Добавить метод |
| `update_datasource_type_method` | Обновить метод (включая код) |
| `delete_datasource_type_method` | Удалить метод |

#### Параметры методов (4 tools)

| Tool | Описание |
|------|----------|
| `list_method_parameters` | Список параметров метода |
| `create_method_parameter` | Добавить параметр |
| `update_method_parameter` | Обновить параметр |
| `delete_method_parameter` | Удалить параметр |

#### Поиск (1 tool)

| Tool | Описание |
|------|----------|
| `search_datasource_type_code` | Поиск по коду методов |

### Activator Types (14 tools)

#### Папки (4 tools)

| Tool | Описание |
|------|----------|
| `list_activator_type_folders` | Список папок типов активаторов |
| `create_activator_type_folder` | Создать папку |
| `update_activator_type_folder` | Обновить папку |
| `delete_activator_type_folder` | Удалить папку |

#### Типы (5 tools)

| Tool | Описание |
|------|----------|
| `list_activator_types` | Список типов активаторов |
| `get_activator_type` | Получить тип с кодом и properties |
| `create_activator_type` | Создать тип |
| `update_activator_type` | Обновить тип (включая код) |
| `delete_activator_type` | Удалить тип |

#### Свойства (4 tools)

| Tool | Описание |
|------|----------|
| `list_activator_type_properties` | Список свойств типа |
| `create_activator_type_property` | Добавить свойство |
| `update_activator_type_property` | Обновить свойство |
| `delete_activator_type_property` | Удалить свойство |

#### Поиск (1 tool)

| Tool | Описание |
|------|----------|
| `search_activator_type_code` | Поиск по коду типов |

### Справочники (2 tools)

| Tool | Описание |
|------|----------|
| `list_value_types` | Типы значений (только чтение) |
| `list_property_sections` | Разделы свойств (только чтение) |

## Разработка

### Запуск тестов

```bash
pytest
```

### Линтинг

```bash
ruff check src tests
```

### Покрытие тестами

```bash
pytest --cov=gims_mcp --cov-report=term-missing
```

## Лицензия

MIT
