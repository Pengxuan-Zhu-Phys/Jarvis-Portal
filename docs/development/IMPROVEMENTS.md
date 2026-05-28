# Improvement Suggestions — wolframdict (Round 2)

Focused on the `wolframdict` module and `WolframAdapter`.

---

## 1. Float 序列化精度不足 — roundtrip 丢失精度

**Problem**: `_format_float` 使用 `.15g`，`_format_scientific_number` 使用 `.15e`，均为 15 位有效数字。IEEE 754 double 需要 17 位有效数字才能保证精确 roundtrip。

实测丢失精度的值：

| 原始值 | dumps 输出 | loads 恢复值 |
|--------|-----------|-------------|
| `3.141592653589793` | `3.14159265358979` | `3.14159265358979` ≠ 原值 |
| `0.3333333333333333` | `0.333333333333333` | `0.333333333333333` ≠ 原值 |
| `0.30000000000000004` | `0.3` | `0.3` ≠ 原值 |
| `1.0000000000000002` | `1.0` | `1.0` ≠ 原值 |

**建议**: `wolframdict.py` 中两处修改：
- `_format_float`: `format(value, ".15g")` → `format(value, ".17g")`
- `_format_scientific_number`: `format(value, ".15e")` → `format(value, ".17e")`

经验证 `.17g` 对所有上述值均能精确 roundtrip。

---

## 2. `_format_float` 中 `_format_scientific` 是死代码

**Problem**: `_format_float` 先把 magnitude <0.001 或 >1,000,000 的值分流到 `_format_scientific_number`，再检查 `.15g` 输出是否含 `e`（走 `_format_scientific`）。但对 [0.001, 1,000,000] 范围，`.17g` 永远不会产生 `e` 记法（指数在 [-3, 5]，不满足 `g` 格式阈值）。经 10 万次随机测试确认。

**建议**: 删除 `_format_scientific` 函数及调用它的两行分支，简化 `_format_float` 逻辑。

---

## 3. 不支持 Wolfram 注释 `(* ... *)`

**Problem**: Mathematica 源文件常见 `(* comment *)` 注释。当前 tokenizer 遇到 `(` 会抛出 `Unexpected character` 错误。对于手动编辑或 Mathematica 导出的 `.wl` 文件，这是个实际障碍。

**建议**: 在 `_tokenize` 主循环中检测 `(*`，跳过到匹配的 `*)`（需支持嵌套注释）。

---

## 4. `_get_nested` 允许负列表索引

**Problem**: `_get_nested` 和 `_set_nested` 中 `int(part)` 允许 `-1` 等负索引。`entry: "Channels.-1.BR"` 会静默返回最后一个 Channel 的 BR，而非返回 None。此行为未在文档中说明。

**建议（二选一）**:
- A. 加 `if index < 0: return None` 禁止负索引（`_get_nested` 和 `_set_nested` 各一处）
- B. 在 `WOLFRAM_FORMAT.md` 中文档化此行为，作为特性保留

---

## 5. `_read_sync` 读取文件两次

**Problem**: `wolfram.py` 的 `_read_sync` 先 `path.read_text()` 获取 source，再调用 `_read_wolfram_document(path)` 内部又读一次。JSON adapter 也有同样的模式。

**建议**: 可抽出 `_read_wolfram_document_from_text(text, path, context)` 避免重复 IO。或维持现状保持与 JSON adapter 一致性。

---

## 6. 测试覆盖缺口

**Problem**: `test_wolframdict.py` 缺少：解析错误路径（unterminated string、unexpected character）、尾逗号容错、未知标识符（`Infinity` → 字符串）。`test_wolfram_adapter.py` 缺少：文件不存在和格式错误 `.wl` 文件的行为测试。

**建议**: 补充上述测试用例，约 50 行。

---

## Priority Summary

| # | Item | 严重程度 | 修改量 |
|---|------|---------|-------|
| 1 | float 精度 `.15g` → `.17g` | 高 | 改两行 |
| 2 | 删除死代码 `_format_scientific` | 低 | 删 5 行 |
| 3 | 支持 `(* *)` 注释 | 中 | 加 ~15 行 |
| 4 | 负列表索引处理 | 低 | 加 1-2 行或文档化 |
| 5 | `_read_sync` 双重读取 | 低 | 可选优化 |
| 6 | 补充测试覆盖 | 中 | 加 ~50 行 |
