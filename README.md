# Consent and Privacy Datahub

将数据主体的授权、撤回、删除和导出请求整理为可审计的数据治理流水线。系统保留不可变事件，并从事件中物化当前授权状态，适合继续扩展字段级策略、影响范围计算和下游删除传播。

## 运行

```bash
PYTHONPATH=src python3 -m consent_privacy.cli \
  --fixture fixtures/sample.json \
  --database /tmp/consent-and-privacy-datahub.sqlite3
```

## 外部依赖类型与版本

- Python 3.11+
- SQLite 3.x
- pytest 8.3.x（测试）

示例只使用虚构主体 ID 和本地数据，不包含真实账号、连接串、token 或密钥。

## 验证

```bash
PYTHONPATH=src python3 -m pytest --import-mode=importlib tests
PYTHONPATH=src python3 -m compileall -q src
```
