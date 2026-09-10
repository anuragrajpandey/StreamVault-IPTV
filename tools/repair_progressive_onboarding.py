from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: Path, old: str, new: str, expected: int = 1) -> bool:
    text = path.read_text()
    count = text.count(old)
    if count == 0:
        return False
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} matches, found {count}")
    path.write_text(text.replace(old, new))
    return True


def require_contains(path: Path, needle: str) -> None:
    if needle not in path.read_text():
        raise SystemExit(f"{path}: expected marker not found: {needle!r}")


# The previous repair moved awaitInitialCatalog outside the provider lock, but the
# background invocation deliberately passed trackInitialLiveOnboarding=false. That
# prevented the strategy from ever consuming the registered first-catalog callback.
# Keep the recursive guard explicit while allowing the actual background sync to run
# with progressive tracking enabled.
sync_manager = ROOT / "data/src/main/java/com/streamvault/data/sync/SyncManager.kt"
replace_exact(
    sync_manager,
    "import java.util.concurrent.atomic.AtomicBoolean\n",
    "import java.util.concurrent.ConcurrentHashMap\nimport java.util.concurrent.atomic.AtomicBoolean\n",
)
replace_exact(
    sync_manager,
    "    private val initialOnboardingBackgroundScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)\n",
    "    private val initialOnboardingBackgroundScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)\n    private val initialOnboardingBackgroundProviders = ConcurrentHashMap.newKeySet<Long>()\n",
)
replace_exact(
    sync_manager,
    "    InitialCatalogCallbackRegistry.register(providerId, ::signalFirstCatalog)\n    initialOnboardingBackgroundScope.launch {\n",
    "    InitialCatalogCallbackRegistry.register(providerId, ::signalFirstCatalog)\n    initialOnboardingBackgroundProviders.add(providerId)\n    initialOnboardingBackgroundScope.launch {\n",
)
replace_exact(
    sync_manager,
    "                    trackInitialLiveOnboarding = false,\n                    providerOverride = providerOverride,\n                    afterCatalogApply = { signalFirstCatalog() }\n                )\n                if (!firstCatalogResult.isCompleted) firstCatalogResult.complete(result)\n            } catch (error: Throwable) {\n                InitialCatalogCallbackRegistry.clear(providerId)\n                if (!firstCatalogResult.isCompleted) firstCatalogResult.completeExceptionally(error)\n            }\n        }\n",
    "                    trackInitialLiveOnboarding = true,\n                    providerOverride = providerOverride,\n                    afterCatalogApply = { signalFirstCatalog() }\n                )\n                if (!firstCatalogResult.isCompleted) firstCatalogResult.complete(result)\n            } catch (error: Throwable) {\n                InitialCatalogCallbackRegistry.clear(providerId)\n                if (!firstCatalogResult.isCompleted) firstCatalogResult.completeExceptionally(error)\n            } finally {\n                initialOnboardingBackgroundProviders.remove(providerId)\n            }\n        }\n",
)
replace_exact(
    sync_manager,
    "        if (trackInitialLiveOnboarding && afterCatalogApply != null) {\n",
    "        if (trackInitialLiveOnboarding && afterCatalogApply != null && !initialOnboardingBackgroundProviders.contains(providerId)) {\n",
)

# M3U imports also need an early durable Live-TV commit. The callback registry is empty
# for normal/background refreshes, so this remains completely inert outside onboarding.
m3u = ROOT / "data/src/main/java/com/streamvault/data/sync/SyncManagerM3uImporter.kt"
replace_exact(
    m3u,
    "        val sessionId = syncCatalogStore.newSessionId()\n",
    "        var sessionId = syncCatalogStore.newSessionId()\n",
)
replace_exact(
    m3u,
    "        var insecureStreamCount = 0\n\n        fun enforceInvalidEntryRatio() {\n",
    "        var insecureStreamCount = 0\n        var initialCatalogCommitted = false\n\n        fun enforceInvalidEntryRatio() {\n",
)
replace_exact(
    m3u,
    "        try {\n            openPlaylistStream(provider) { streamed ->\n",
    "        suspend fun flushLiveBatch() {\n            if (channelBatch.isEmpty()) return\n            val stagedBatch = channelBatch.toList()\n            flushChannelBatch(provider.id, sessionId, channelBatch)\n            if (initialCatalogCommitted) return\n            val initialCatalogCallback = InitialCatalogCallbackRegistry.take(provider.id) ?: return\n            if (stagedBatch.isEmpty()) return\n            syncCatalogStore.upsertLiveCatalog(\n                providerId = provider.id,\n                categories = liveCategories.entities(),\n                channels = stagedBatch,\n                afterCatalogApply = initialCatalogCallback\n            )\n            initialCatalogCommitted = true\n            val continuationSessionId = syncCatalogStore.newSessionId()\n            syncCatalogStore.stageChannelBatch(provider.id, continuationSessionId, stagedBatch)\n            if (movieBatch.isNotEmpty()) {\n                syncCatalogStore.stageMovieBatch(provider.id, continuationSessionId, movieBatch.toList())\n                movieBatch.clear()\n            }\n            sessionId = continuationSessionId\n        }\n\n        try {\n            openPlaylistStream(provider) { streamed ->\n",
)
replace_exact(
    m3u,
    "                                flushChannelBatch(provider.id, sessionId, channelBatch)\n",
    "                                flushLiveBatch()\n",
    expected=2,
)
replace_exact(
    m3u,
    "            flushChannelBatch(provider.id, sessionId, channelBatch)\n            flushMovieBatch(provider.id, sessionId, movieBatch)\n",
    "            flushLiveBatch()\n            flushMovieBatch(provider.id, sessionId, movieBatch)\n",
)

# If the current tree already contains the new architecture, the script is intentionally
# idempotent and simply validates the important markers.
require_contains(sync_manager, "trackInitialLiveOnboarding = true,")
require_contains(sync_manager, "initialOnboardingBackgroundProviders")
require_contains(m3u, "suspend fun flushLiveBatch()")
require_contains(m3u, "InitialCatalogCallbackRegistry.take(provider.id)")
require_contains(m3u, "flushLiveBatch()")

print("Progressive onboarding handoff repair applied successfully.")
