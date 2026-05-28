# Wolfram Format Adapter Design

## Context

Jarvis-Portal 需要新增 Wolfram Language (`.wl`) 格式的 IO 支持。`.wl` 文件使用 Mathematica 的 Association 语法（`<| "key" -> value |>`），结构上与 JSON 等价——都是嵌套的 key-value。因此 YAML spec 设计与 JSON 完全一致，使用 `entry` 做点分路径寻址。额外支持列表索引（`entry: "Channels.0.BR"`）以访问 list of associations 中的元素。

参考输入文件：`/Users/p.zhu/Workshop/QI/2511.17321/examples/sm_higgs_ee_input.wl`
参考输出文件：`/Users/p.zhu/Workshop/QI/2511.17321/sm_higgs_ee_from_br.wl`

## WL 格式语法摘要

```
<| "key" -> value, ... |>    → Python dict
{ item, item, ... }          → Python list
"string"                     → str
123, 123.45                  → int / float
2.5*^-6                      → float (Mathematica 科学计数法 = 2.5e-6)
True, False                  → bool
```

## YAML Spec 设计

与 JSON 完全一致，仅 `type: Wolfram`：

### Input (写入)

```yaml
input:
  - name: params
    path: "input.wl"
    type: Wolfram
    actions:
      - type: Dump
        variables:
          - { name: "HiggsMass", entry: "SMParameters.HiggsMass" }
          - { name: "mb", entry: "SMParameters.mb" }
          - { name: "alpha_s", entry: "SMParameters.alpha_s" }
          - { name: "BR_bb", expression: "BR_bb", entry: "BranchingFractions.bb" }
```

- `name`: 变量标识符 + observable 名（与 JSON 一致）
- `entry`: 点分路径，写入嵌套 association 中的指定位置
- `expression`: 可选，有 expression 则求值后成为 observable
- 无 `entry` 时用 `name` 作为顶层 key（与 JSON 一致）

### Output (读取)

```yaml
output:
  - name: observables
    path: "output.wl"
    type: Wolfram
    variables:
      - { name: "LinearEntropy" }
      - { name: "BRSum", entry: "BranchingFractionSum" }
      - { name: "BR_bb", entry: "Channels.0.BR" }
      - { name: "EntropyTerm_WW", entry: "Channels.12.EntropyTerm" }
```

- `name`: observable 名
- `entry`: 点分路径，支持数字索引访问列表元素
  - `"Channels.0.BR"` → `payload["Channels"][0]["BR"]`
  - 路径中某段是数字且当前值是 list → 当做列表索引
  - 路径中某段是数字但当前值是 dict → 当做字符串 key
- 无 `entry` 时用 `name` 作为顶层 key
- 缺失数据（路径不存在、索引越界）→ 返回 `None`（与 JSON 行为一致）

## 实现计划

### 1. `wolframdict` 模块：`src/jarvis_portal/wolframdict.py`

独立的 WL Association 解析/序列化模块，API 完全对齐 Python `json` 模块：

```python
from jarvis_portal import wolframdict

# 从文件对象读取
with open("output.wl", "r") as f:
    data = wolframdict.load(f)

# 从字符串读取
data = wolframdict.loads(wl_text)

# 写入文件对象
with open("input.wl", "w") as f:
    wolframdict.dump(data, f, indent=2)

# 序列化为字符串
text = wolframdict.dumps(data, indent=2)
```

公开 API：

| 函数 | 签名 | 说明 |
|------|------|------|
| `load` | `load(fp) → dict` | 从文件对象读取 WL 文本并解析为 dict |
| `loads` | `loads(text: str) → dict` | 从字符串解析 WL 文本为 dict |
| `dump` | `dump(obj, fp, indent=2)` | 将 dict 序列化为 WL 文本并写入文件对象 |
| `dumps` | `dumps(obj, indent=2) → str` | 将 dict 序列化为 WL 文本字符串 |

模块通过 `from jarvis_portal import wolframdict` 导入，在 `__init__.py` 中导出。

### 2. WL 解析器（`wolframdict` 内部实现）

Tokenizer + 递归下降 parser，零外部依赖：

**Tokenizer** 产出 token 类型：
- `ASSOC_OPEN` (`<|`), `ASSOC_CLOSE` (`|>`)
- `LIST_OPEN` (`{`), `LIST_CLOSE` (`}`)
- `ARROW` (`->`)
- `COMMA` (`,`)
- `STRING` (双引号字符串)
- `NUMBER` (整数、浮点数、`*^` 科学计数法)
- `IDENT` (`True`, `False`, `Null` 等裸标识符)

**Parser** 语法：
```
value       := association | list | string | number | ident
association := '<|' (pair (',' pair)*)? '|>'
pair        := string '->' value
list        := '{' (value (',' value)*)? '}'
```

科学计数法处理：`2.5*^-6` → tokenize 时直接识别为单个 NUMBER token → `float(2.5e-6)`

### 3. WL 序列化器（`wolframdict` 内部实现）

Python → WL 文本，带缩进美化：
- `dict` → `<| "key" -> value, ... |>`
- `list` → `{ item, ... }`
- `str` → `"escaped_string"`
- `float` → 如果绝对值 < 0.001 或 > 1e6 则用 `*^` 记法，否则普通小数
- `int` → 直接输出
- `bool` → `True` / `False`
- `None` → `Null`

### 4. `WolframAdapter`：`src/jarvis_portal/adapters/wolfram.py`

核心结构与 `json.py` 平行，内部使用 `wolframdict.loads()` / `wolframdict.dumps()` 替代 `json.loads()` / `json.dumps()`：

```
WolframAdapter
  format_name = "Wolfram"
  direction = "both"
  _write_sync: wolframdict.loads → 修改 → wolframdict.dumps → 写回
  _read_sync:  wolframdict.loads → 按 entry 提取 → 返回 observables
```

adapter 内部工具函数：
- `_get_nested(payload, entry)` — 点分路径读取，支持列表索引
- `_set_nested(payload, entry, value)` — 点分路径写入，支持列表索引
- `_iter_write_operations` / `_operation_from_variable` / `_evaluate_expression`
- `_save_copy_if_requested` / `_log_error`

### 5. 带列表索引的路径寻址

扩展 JSON 的 `_get_nested` / `_set_nested`：

```python
def _get_nested(payload, entry):
    current = payload
    for part in entry.split("."):
        if isinstance(current, list):
            try:
                index = int(part)
                current = current[index]
                continue
            except (ValueError, IndexError):
                return None
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        else:
            return None
    return current
```

### 6. 注册与导出

- `builtins.py`: 添加 `registry.register("Wolfram", WolframAdapter(), "both")`
- `adapters/__init__.py`: 导出 `WolframAdapter`
- `registry.py`: `EXPOSED_FORMATS` 加入 `"wolfram"`
- `__init__.py`: 导出 `wolframdict` 模块

### 7. CLI manual

- `cli.py`: `render_manual` 添加 `wolfram` topic
- `render_manual(None)` 的格式列表中加入 wolfram

### 8. Example 文件

`examples/formats/wolfram/` 目录：
- `README.md`
- `adapter-spec.yaml`
- `jarvis-hep.yaml`
- `input.wl` — 简化版输入（嵌套 association）
- `output.wl` — 简化版输出（含 list of associations）

### 9. 测试

`tests/test_wolframdict.py`：
- `loads` / `dumps` 基础测试：association、嵌套、列表、科学计数法、空输入
- roundtrip 测试：`loads(dumps(data))` 一致
- `load` / `dump` 文件对象测试
- 用参考 `.wl` 文件做真实数据 roundtrip

`tests/test_wolfram_adapter.py`：
- write_input 测试：通过 entry 写入嵌套路径
- read_output 测试：通过 entry 读取嵌套值 + 列表索引
- 缺失数据返回 None
- example 文件集成测试

更新 `tests/test_format_examples.py`: `FORMAT_DIRS` 加入 `"wolfram"`

## 验证

```bash
pytest tests/test_wolframdict.py tests/test_wolfram_adapter.py tests/test_format_examples.py tests/test_registry.py -v
```

- `wolframdict` 能正确解析参考输入/输出 `.wl` 文件
- roundtrip 序列化不丢失数据
- `from jarvis_portal import wolframdict` 可正常导入
- entry 路径（含列表索引）正确读写
- 现有测试不受影响
