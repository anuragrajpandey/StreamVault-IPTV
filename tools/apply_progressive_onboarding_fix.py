from pathlib import Path
import re


def patch_sync_manager():
    path = Path("data/src/main/java/com/streamvault/data/sync/SyncManager.kt")
    text = path.read_text()
    text = text.replace(
        "import kotlinx.coroutines.CancellationException\n",
        "import kotlinx.coroutines.CancellationException\n"
        "import kotlinx.coroutines.CompletableDeferred\n"
        "import kotlinx.coroutines.CoroutineScope\n"
        "import kotlinx.coroutines.SupervisorJob\n",
        1,
    )
    anchor = "    private val syncProviderSnapshotAdapter = SyncProviderSnapshotAdapter(providerSnapshotRepository)\n"
    if text.count(anchor) != 1:
        raise RuntimeError("SyncManager scope anchor mismatch")
    text = text.replace(
        anchor,
        anchor + "    private val initialOnboardingBackgroundScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)\n",
        1,
    )
    signature = "): com.streamvault.domain.model.Result<Unit> = withProviderLock(providerId) lock@{\n"
    branch = "): com.streamvault.domain.model.Result<Unit> {\n" \
        "        if (trackInitialLiveOnboarding) {\n" \
        "            val firstCatalogResult = CompletableDeferred<com.streamvault.domain.model.Result<Unit>>()\n" \
        "            initialOnboardingBackgroundScope.launch {\n" \
        "                try {\n" \
        "                    val backgroundResult = syncWithProviderOverride(\n" \
        "                        providerId = providerId,\n" \
        "                        force = force,\n" \
        "                        movieFastSyncOverride = movieFastSyncOverride,\n" \
        "                        epgSyncModeOverride = epgSyncModeOverride,\n" \
        "                        onProgress = onProgress,\n" \
        "                        trackInitialLiveOnboarding = false,\n" \
        "                        providerOverride = providerOverride,\n" \
        "                        afterCatalogApply = {\n" \
        "                            try {\n" \
        "                                afterCatalogApply?.invoke()\n" \
        "                                firstCatalogResult.complete(com.streamvault.domain.model.Result.success(Unit))\n" \
        "                            } catch (error: Throwable) {\n" \
        "                                firstCatalogResult.completeExceptionally(error)\n" \
        "                                throw error\n" \
        "                            }\n" \
        "                        }\n" \
        "                    )\n" \
        "                    if (!firstCatalogResult.isCompleted) {\n" \
        "                        firstCatalogResult.complete(backgroundResult)\n" \
        "                    }\n" \
        "                } catch (error: Throwable) {\n" \
        "                    if (!firstCatalogResult.isCompleted) {\n" \
        "                        firstCatalogResult.completeExceptionally(error)\n" \
        "                    }\n" \
        "                }\n" \
        "            }\n" \
        "            return firstCatalogResult.await()\n" \
        "        }\n" \
        "        return withProviderLock(providerId) lock@{\n"
    if text.count(signature) != 1:
        raise RuntimeError("SyncManager syncWithProviderOverride anchor mismatch")
    path.write_text(text.replace(signature, branch, 1))


def patch_live_strategy():
    path = Path("data/src/main/java/com/streamvault/data/sync/SyncManagerXtreamLiveStrategy.kt")
    text = path.read_text()
    text = text.replace(
        "fullPayload = loadXtreamLiveFull(provider, api, runtimeProfile)",
        "fullPayload = loadXtreamLiveFull(\n"
        "                provider = provider,\n"
        "                api = api,\n"
        "                runtimeProfile = runtimeProfile,\n"
        "                trackInitialLiveOnboarding = trackInitialLiveOnboarding,\n"
        "                afterCatalogApply = afterCatalogApply\n"
        "            )",
        1,
    )
    text = text.replace(
        "            runtimeProfile = runtimeProfile\n        )\n        return CatalogSyncPayload(",
        "            runtimeProfile = runtimeProfile,\n"
        "            trackInitialLiveOnboarding = trackInitialLiveOnboarding,\n"
        "            afterCatalogApply = afterCatalogApply\n"
        "        )\n        return CatalogSyncPayload(",
        1,
    )
    text = text.replace(
        "    suspend fun loadXtreamLiveFull(\n"
        "        provider: Provider,\n"
        "        api: XtreamProvider,\n"
        "        runtimeProfile: CatalogSyncRuntimeProfile\n"
        "    ): CatalogSyncPayload<Channel> {",
        "    suspend fun loadXtreamLiveFull(\n"
        "        provider: Provider,\n"
        "        api: XtreamProvider,\n"
        "        runtimeProfile: CatalogSyncRuntimeProfile,\n"
        "        trackInitialLiveOnboarding: Boolean,\n"
        "        afterCatalogApply: suspend () -> Unit\n"
        "    ): CatalogSyncPayload<Channel> {",
        1,
    )
    if len(list(re.finditer(r"runtimeProfile = runtimeProfile\n\s*\)\n", text))) < 3:
        raise RuntimeError("Expected three full-stream call sites")
    text = re.sub(
        r"runtimeProfile = runtimeProfile\n(\s*)\)\n",
        r"runtimeProfile = runtimeProfile,\n"
        r"\1trackInitialLiveOnboarding = trackInitialLiveOnboarding,\n"
        r"\1afterCatalogApply = afterCatalogApply\n"
        r"\1)\n",
        text,
        count=3,
    )
    text = text.replace(
        "        runtimeProfile: CatalogSyncRuntimeProfile\n"
        "    ): CatalogSyncPayload<Channel> {\n"
        "        val fallbackCollector",
        "        runtimeProfile: CatalogSyncRuntimeProfile,\n"
        "        trackInitialLiveOnboarding: Boolean,\n"
        "        afterCatalogApply: suspend () -> Unit\n"
        "    ): CatalogSyncPayload<Channel> {\n"
        "        val fallbackCollector",
        1,
    )
    text = text.replace(
        "        var stagingElapsedMs = 0L\n",
        "        var stagingElapsedMs = 0L\n        var initialCatalogCommitted = false\n",
        1,
    )
    old = (
        "            stagedSessionId = staged.sessionId\n"
        "            acceptedCount += staged.acceptedCount\n"
        "            flushCount++\n"
    )
    new = (
        "            stagedSessionId = staged.sessionId\n"
        "            acceptedCount += staged.acceptedCount\n"
        "            if (trackInitialLiveOnboarding && staged.acceptedCount > 0 && !initialCatalogCommitted) {\n"
        "                val bootstrapChannels = mappedChannels\n"
        "                    .filter { it.streamId > 0L }\n"
        "                    .distinctBy { it.streamId }\n"
        "                if (bootstrapChannels.isNotEmpty()) {\n"
        "                    syncCatalogStore.upsertLiveCatalog(\n"
        "                        providerId = provider.id,\n"
        "                        categories = fallbackCollector.entities(),\n"
        "                        channels = bootstrapChannels,\n"
        "                        afterCatalogApply = afterCatalogApply\n"
        "                    )\n"
        "                    initialCatalogCommitted = true\n"
        "                    val continuationSessionId = syncCatalogStore.newSessionId()\n"
        "                    syncCatalogStore.stageChannelBatch(\n"
        "                        providerId = provider.id,\n"
        "                        sessionId = continuationSessionId,\n"
        "                        channels = bootstrapChannels.map { it.toEntity() }\n"
        "                    )\n"
        "                    stagedSessionId = continuationSessionId\n"
        "                }\n"
        "            }\n"
        "            flushCount++\n"
    )
    if text.count(old) != 1:
        raise RuntimeError("Full live staging block mismatch")
    text = text.replace(old, new, 1)
    text = text.replace(
        "    suspend fun loadXtreamLiveByCategory(\n"
        "        provider: Provider,\n"
        "        api: XtreamProvider,\n"
        "        rawCategories: List<XtreamCategory>,\n"
        "        onProgress: ((String) -> Unit)?,\n"
        "        preferSequential: Boolean,\n"
        "        runtimeProfile: CatalogSyncRuntimeProfile\n"
        "    ): CatalogSyncPayload<Channel> {",
        "    suspend fun loadXtreamLiveByCategory(\n"
        "        provider: Provider,\n"
        "        api: XtreamProvider,\n"
        "        rawCategories: List<XtreamCategory>,\n"
        "        onProgress: ((String) -> Unit)?,\n"
        "        preferSequential: Boolean,\n"
        "        runtimeProfile: CatalogSyncRuntimeProfile,\n"
        "        trackInitialLiveOnboarding: Boolean,\n"
        "        afterCatalogApply: suspend () -> Unit\n"
        "    ): CatalogSyncPayload<Channel> {",
        1,
    )
    text = text.replace(
        "        var stagedAcceptedCount = 0\n",
        "        var stagedAcceptedCount = 0\n        var initialCatalogCommitted = false\n",
        1,
    )
    old = (
        "                stagedSessionId = staged.sessionId\n"
        "                stagedAcceptedCount += staged.acceptedCount\n"
    )
    new = (
        "                stagedSessionId = staged.sessionId\n"
        "                stagedAcceptedCount += staged.acceptedCount\n"
        "                if (trackInitialLiveOnboarding && staged.acceptedCount > 0 && !initialCatalogCommitted) {\n"
        "                    val bootstrapChannels = channels\n"
        "                        .filter { it.streamId > 0L }\n"
        "                        .distinctBy { it.streamId }\n"
        "                    if (bootstrapChannels.isNotEmpty()) {\n"
        "                        syncCatalogStore.upsertLiveCatalog(\n"
        "                            providerId = provider.id,\n"
        "                            categories = fallbackCollector.entities(),\n"
        "                            channels = bootstrapChannels,\n"
        "                            afterCatalogApply = afterCatalogApply\n"
        "                        )\n"
        "                        initialCatalogCommitted = true\n"
        "                        val continuationSessionId = syncCatalogStore.newSessionId()\n"
        "                        syncCatalogStore.stageChannelBatch(\n"
        "                            providerId = provider.id,\n"
        "                            sessionId = continuationSessionId,\n"
        "                            channels = bootstrapChannels.map { it.toEntity() }\n"
        "                        )\n"
        "                        stagedSessionId = continuationSessionId\n"
        "                    }\n"
        "                }\n"
    )
    if text.count(old) != 1:
        raise RuntimeError("Category staging block mismatch")
    text = text.replace(old, new, 1)
    path.write_text(text)


def patch_player_ui():
    clean = Path("app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerCleanControls.kt")
    text = clean.read_text()
    text = text.replace(
        '                    CleanIconButton(Icons.Default.MoreHoriz, "More player controls", onOpenStopPlaybackTimer, primaryControlSize)\n',
        "",
    )
    text = text.replace(
        '                            CleanIconButton(Icons.Default.Settings, stringResource(R.string.player_stop_playback_after), onOpenStopPlaybackTimer)\n',
        "",
    )
    clean.write_text(text)

    chrome = Path("app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerControlsChrome.kt")
    text = chrome.read_text()
    pattern = re.compile(
        r"\n\s*add\(PlayerActionSpec\(\s*sleepTimerActionLabel\(\s*"
        r"title = stringResource\(R\.string\.player_stop_playback_after\),.*?"
        r"\n\s*onOpenStopPlaybackTimer\n\s*\)\)",
        re.S,
    )
    text, removed = pattern.subn("", text)
    if removed < 1:
        raise RuntimeError("Legacy stop-timer actions not found")
    chrome.write_text(text)

    overlays = Path("app/src/main/java/com/streamvault/app/ui/screens/player/overlay/PlayerSystemOverlays.kt")
    text = overlays.read_text()
    old = "    val showStopWarning = state.stopTimerWarningVisible\n"
    if text.count(old) != 1:
        raise RuntimeError("Stop timer warning anchor mismatch")
    overlays.write_text(text.replace(old, "    val showStopWarning = false\n", 1))


def cleanup_one_shot_workflow():
    workflow = Path(".github/workflows/release.yml")
    text = workflow.read_text()
    begin = text.find("      # BEGIN ONE-SHOT PROGRESSIVE ONBOARDING PATCH\n")
    end = text.find("      # END ONE-SHOT PROGRESSIVE ONBOARDING PATCH\n")
    if begin != -1 and end != -1:
        end += len("      # END ONE-SHOT PROGRESSIVE ONBOARDING PATCH\n")
        text = text[:begin] + text[end:]
        workflow.write_text(text)
    Path("tools/apply_progressive_onboarding_fix.py").unlink(missing_ok=True)
    Path(".github/workflows/apply-progressive-onboarding-fix.yml").unlink(missing_ok=True)


patch_sync_manager()
patch_live_strategy()
patch_player_ui()
cleanup_one_shot_workflow()
print("Progressive onboarding and player timer UI patches applied.")
