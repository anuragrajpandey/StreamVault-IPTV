from pathlib import Path
p = Path('data/src/main/java/com/streamvault/data/sync/SyncManagerXtreamLiveStrategy.kt')
text = p.read_text()
text = text.replace(',\n            afterCatalogApply = InitialCatalogCallbackRegistry.take(provider.id)', '', 3)
text = text.replace('        afterCatalogApply = afterCatalogApply\n', '', 1)
needle = 'syncCatalogStore.upsertLiveCatalog(providerId = provider.id, categories = fallbackCollector.entities(), channels = bootstrapChannels)'
replacement = 'syncCatalogStore.upsertLiveCatalog(providerId = provider.id, categories = fallbackCollector.entities(), channels = bootstrapChannels, afterCatalogApply = InitialCatalogCallbackRegistry.take(provider.id))'
text = text.replace(needle, replacement)
p.write_text(text)
Path('tools/fix_strategy_callback.py').unlink()
print('strategy callback callsites fixed')
