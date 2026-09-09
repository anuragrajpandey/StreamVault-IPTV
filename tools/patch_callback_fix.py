from pathlib import Path
import re

manager = Path('data/src/main/java/com/streamvault/data/sync/SyncManager.kt')
text = manager.read_text()
text = text.replace('import kotlinx.coroutines.SupervisorJob\n', 'import kotlinx.coroutines.SupervisorJob\nimport java.util.concurrent.atomic.AtomicBoolean\n', 1)
old = '''            val firstCatalogResult = CompletableDeferred<com.streamvault.domain.model.Result<Unit>>()
            initialOnboardingBackgroundScope.launch {
                try {
                    val backgroundResult = syncWithProviderOverride(
'''
new = '''            val firstCatalogResult = CompletableDeferred<com.streamvault.domain.model.Result<Unit>>()
            val catalogSignalDelivered = AtomicBoolean(false)
            suspend fun signalFirstCatalog() {
                if (!catalogSignalDelivered.compareAndSet(false, true)) return
                try {
                    afterCatalogApply?.invoke()
                    firstCatalogResult.complete(com.streamvault.domain.model.Result.success(Unit))
                } catch (error: Throwable) {
                    firstCatalogResult.completeExceptionally(error)
                    throw error
                }
            }
            InitialCatalogCallbackRegistry.register(providerId, ::signalFirstCatalog)
            initialOnboardingBackgroundScope.launch {
                try {
                    val backgroundResult = syncWithProviderOverride(
'''
if text.count(old) != 1: raise SystemExit('manager block mismatch')
text = text.replace(old, new, 1)
old = '''                        afterCatalogApply = {
                            try {
                                afterCatalogApply?.invoke()
                                firstCatalogResult.complete(com.streamvault.domain.model.Result.success(Unit))
                            } catch (error: Throwable) {
                                firstCatalogResult.completeExceptionally(error)
                                throw error
                            }
                        }
'''
if text.count(old) != 1: raise SystemExit('manager callback mismatch')
text = text.replace(old, '                        afterCatalogApply = { signalFirstCatalog() }\n', 1)
old = '''                } catch (error: Throwable) {
                    if (!firstCatalogResult.isCompleted) firstCatalogResult.completeExceptionally(error)
                }
            }
'''
new = '''                } catch (error: Throwable) {
                    InitialCatalogCallbackRegistry.clear(providerId)
                    if (!firstCatalogResult.isCompleted) firstCatalogResult.completeExceptionally(error)
                }
            }
'''
if text.count(old) != 1: raise SystemExit('manager catch mismatch')
text = text.replace(old, new, 1)
manager.write_text(text)

strategy = Path('data/src/main/java/com/streamvault/data/sync/SyncManagerXtreamLiveStrategy.kt')
text = strategy.read_text()
text = text.replace(', afterCatalogApply = afterCatalogApply', '', 2)
text = text.replace(',\n            afterCatalogApply = afterCatalogApply', '', 1)
text = re.sub(r',\n\s*afterCatalogApply: suspend \(\) -> Unit', '', text)
text = text.replace('afterCatalogApply = afterCatalogApply', 'afterCatalogApply = InitialCatalogCallbackRegistry.take(provider.id)', 2)
strategy.write_text(text)

Path('data/src/main/java/com/streamvault/data/sync/InitialCatalogCallbackRegistry.kt').write_text('''package com.streamvault.data.sync\n\nimport java.util.concurrent.ConcurrentHashMap\n\ninternal object InitialCatalogCallbackRegistry {\n    private val callbacks = ConcurrentHashMap<Long, suspend () -> Unit>()\n\n    fun register(providerId: Long, callback: suspend () -> Unit) {\n        callbacks[providerId] = callback\n    }\n\n    fun take(providerId: Long): (suspend () -> Unit)? = callbacks.remove(providerId)\n\n    fun clear(providerId: Long) {\n        callbacks.remove(providerId)\n    }\n}\n''')
Path('tools/patch_callback_fix.py').unlink()
print('callback patch applied')
