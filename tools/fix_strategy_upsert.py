from pathlib import Path
p = Path('data/src/main/java/com/streamvault/data/sync/SyncManagerXtreamLiveStrategy.kt')
text = p.read_text()
old = 'afterCatalogApply = afterCatalogApply'
if text.count(old) != 1:
    raise SystemExit(f'expected one stray callback reference, found {text.count(old)}')
text = text.replace(old, 'afterCatalogApply = InitialCatalogCallbackRegistry.take(provider.id)', 1)
p.write_text(text)
Path('tools/fix_strategy_upsert.py').unlink()
print('fixed final onboarding upsert callback')
