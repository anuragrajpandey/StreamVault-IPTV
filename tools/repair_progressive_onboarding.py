from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected 1 match, found {count}")
    path.write_text(text.replace(old, new, 1))


sync_manager = ROOT / "data/src/main/java/com/streamvault/data/sync/SyncManager.kt"
replace_once(
    sync_manager,
    '''    ): com.streamvault.domain.model.Result<Unit> = withProviderLock(providerId) lock@{
        if (trackInitialLiveOnboarding) {
            return@lock awaitInitialCatalog(
                providerId = providerId,
                force = force,
                movieFastSyncOverride = movieFastSyncOverride,
                epgSyncModeOverride = epgSyncModeOverride,
                onProgress = onProgress,
                trackInitialLiveOnboarding = trackInitialLiveOnboarding,
                providerOverride = providerOverride,
                afterCatalogApply = afterCatalogApply
            )
        }

        var progressSession: SyncProgressSession? = null''',
    '''    ): com.streamvault.domain.model.Result<Unit> {
        if (trackInitialLiveOnboarding && afterCatalogApply != null) {
            return awaitInitialCatalog(
                providerId = providerId,
                force = force,
                movieFastSyncOverride = movieFastSyncOverride,
                epgSyncModeOverride = epgSyncModeOverride,
                onProgress = onProgress,
                trackInitialLiveOnboarding = trackInitialLiveOnboarding,
                providerOverride = providerOverride,
                afterCatalogApply = afterCatalogApply
            )
        }

        return withProviderLock(providerId) lock@{
        var progressSession: SyncProgressSession? = null''',
)
replace_once(
    sync_manager,
    '''        }
    }

    fun resetState''',
    '''        }
        }
    }

    fun resetState''',
)

registry = ROOT / "data/src/main/java/com/streamvault/data/sync/InitialCatalogCallbackRegistry.kt"
replace_once(
    registry,
    "fun take(providerId: Long): suspend () -> Unit = callbacks.remove(providerId) ?: {}",
    "fun take(providerId: Long): (suspend () -> Unit)? = callbacks.remove(providerId)",
)

strategy = ROOT / "data/src/main/java/com/streamvault/data/sync/SyncManagerXtreamLiveStrategy.kt"
replace_once(
    strategy,
    "if (trackInitialLiveOnboarding && staged.acceptedCount > 0 && !initialCatalogCommitted) {",
    "val initialCatalogCallback = if (trackInitialLiveOnboarding) InitialCatalogCallbackRegistry.take(provider.id) else null\n            if (initialCatalogCallback != null && staged.acceptedCount > 0 && !initialCatalogCommitted) {",
)
replace_once(
    strategy,
    "if (trackInitialLiveOnboarding && staged.acceptedCount > 0 && !initialCatalogCommitted) {",
    "val initialCatalogCallback = if (trackInitialLiveOnboarding) InitialCatalogCallbackRegistry.take(provider.id) else null\n            if (initialCatalogCallback != null && staged.acceptedCount > 0 && !initialCatalogCommitted) {",
)
replace_once(
    strategy,
    "afterCatalogApply = InitialCatalogCallbackRegistry.take(provider.id)",
    "afterCatalogApply = initialCatalogCallback",
)
replace_once(
    strategy,
    "afterCatalogApply = InitialCatalogCallbackRegistry.take(provider.id)",
    "afterCatalogApply = initialCatalogCallback",
)

print("Progressive onboarding repair applied successfully.")
