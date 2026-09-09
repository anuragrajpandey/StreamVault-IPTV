from pathlib import Path
p = Path('data/src/main/java/com/streamvault/data/sync/SyncManagerXtreamLiveStrategy.kt')
text = p.read_text()
text = text.replace('        afterCatalogApply = InitialCatalogCallbackRegistry.take(provider.id)\n', '')
p.write_text(text)
Path('tools/fix_strategy_args.py').unlink()
print('removed stray callback argument')
