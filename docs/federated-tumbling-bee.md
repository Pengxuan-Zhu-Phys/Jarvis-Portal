# Table Format YAML Design Plan

## Context

Jarvis-Portal 目前只有 JSON adapter。需要新增三种表格格式的 IO 支持：CSV、TSV、DAT（空格分隔）。三种格式共享相同的 YAML spec 结构设计，仅 `type` 字段不同。本阶段只完成用户端 YAML 设计和 example 文件，不写 adapter 代码。

## YAML Spec 设计

### 与 JSON 的映射关系

| JSON 概念 | 表格概念 | 说明 |
|-----------|---------|------|
| `entry: "fit.loglike"` | `column: "loglike"` | 定位字段：JSON 用点分路径，表格用列名/列索引 |
| （无） | `row: 0` | 表格多了行维度；不指定时读整列返回 list |
| （无） | `header: true` | 表格需要声明是否有表头 |
| （无） | `columns: [...]` | 无表头时可显式命名列 |
| （无） | `comment: "#"` | DAT 格式支持注释行前缀 |

### Spec 级别字段（三种格式通用）

```yaml
- name: params              # spec 名称
  path: "input.csv"         # 文件路径
  type: CSV | TSV | DAT     # 格式类型
  save: false               # 是否保存副本
  header: true              # 是否有表头行（默认 true）
  columns: [col1, col2]     # 显式列名（header: false 时使用）
  comment: "#"              # 注释行前缀（仅 DAT 有默认值 "#"）
```

### DAT 格式空格分隔的稳健性

DAT 格式使用 Python `str.split()`（无参数）进行列分隔，具备以下特性：
- 自动处理任意数量的连续空格和 tab
- 自动忽略行首尾空白
- 混合空格与 tab 均正确分隔
- 读取时跳过以 `comment` 前缀开头的行（默认 `#`）和纯空行
- 写出时列间用单个空格分隔，保持整洁

### Input (写入) YAML 结构

与 JSON 对齐：`actions` → `type: Dump` → `variables`

**关键区别**：与 JSON 不同，表格 input variable 的 `name` 仅是变量标识符，不作为列名的 fallback。`column` 是必须显式指定的写入目标列。

```yaml
input:
  - name: params
    path: "input.csv"
    type: CSV
    header: true
    actions:
      - type: Dump
        variables:
          - { name: "var_mass",     expression: "x * Pi",     column: "mass" }
          - { name: "var_coupling", expression: "y * Pi",     column: "coupling" }
          - { name: "var_config",   expression: "(x+y)*Pi",   column: "config" }
```

Variable 字段：
- `name`: 变量标识符（仅用于标识和 observable 返回名，**不**映射到列名）
- `expression`: 值或表达式（有 expression 时先求值得到 value，且该变量成为 observable）
- `column`: **必填**，指定写入哪一列（列名或列索引）
- `row`: 写入行号（可选，默认 0，即第一行数据行，不是 header 行）

### Output (读取) YAML 结构

```yaml
output:
  - name: observables
    path: "output.csv"
    type: CSV
    header: true
    variables:
      - { name: "chi2" }                              # 读 "chi2" 列全部数据 → list
      - { name: "best_mass", column: "mass", row: 0 } # 读 "mass" 列第 0 行 → 单值
      - { name: "loglike", column: "fit_loglike" }     # 读 "fit_loglike" 列 → list
```

Variable 字段：
- `name`: observable 名（同时作为默认列名）
- `column`: 显式列名（可选，不指定时用 `name` 作为列名）
- `row`: 行号（可选，不指定则返回整列 list；指定则返回单值）
- **自动解包**：不指定 `row` 时，若整列只有 1 个元素，自动返回该元素而非长度为 1 的 list
- **缺失处理**：若 variable 未读出任何数据（列不存在、行越界等），该 variable **不写入** 返回的 observables dict。Jarvis-HEP 依赖键的有无判断输入是否齐全，缺键会中断后续计算——这是硬限制

**Input vs Output 的 column 语义差异**：
- Input: `column` **必填**，`name` 仅是变量标识符
- Output: `column` **可选**，不指定时 `name` 既是 observable 名也是列名

## 文件创建计划

为每种格式在 `examples/formats/` 下创建目录，包含 5 个文件：

### 1. `examples/formats/csv/`
- `README.md` — 格式说明
- `adapter-spec.yaml` — jportal 可直接运行的 spec
- `jarvis-hep.yaml` — Jarvis-HEP Calculators 形状
- `input.csv` — 样例输入模板
- `output.csv` — 样例输出数据

### 2. `examples/formats/tsv/`
- 同上，`.csv` → `.tsv`，`type: CSV` → `type: TSV`

### 3. `examples/formats/dat/`
- 同上，文件用 `.dat`，`type: DAT`
- DAT 示例包含 `comment: "#"` 和注释行
- 使用 `header: false` + `columns: [...]` 展示无表头场景

### 4. 更新 `tests/test_format_examples.py`
- 将 `FORMAT_DIRS` 加入 `"csv"`, `"tsv"`, `"dat"`
- 仅校验文件结构和 YAML 合法性（不运行 adapter）

## 验证

- `pytest tests/test_format_examples.py` 通过
- 所有 YAML 文件可被 `yaml.safe_load` 正确解析
- YAML 结构与 JSON 例子一致（有 name/path/type/actions/variables）
