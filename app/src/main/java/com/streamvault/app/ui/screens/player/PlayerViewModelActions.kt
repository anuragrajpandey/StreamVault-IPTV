package com.streamvault.app.ui.screens.player

import androidx.lifecycle.viewModelScope
import com.streamvault.app.R
import com.streamvault.domain.model.ContentType
import com.streamvault.domain.model.Result
import com.streamvault.domain.model.StreamInfo
import com.streamvault.domain.usecase.ScheduleRecordingCommand
import kotlinx.coroutines.launch

fun PlayerViewModel.castCurrentMedia(onRouteSelectionRequired: () -> Unit) {
    viewModelScope.launch {
        val request = when (val result = buildCastRequestResult()) {
            is PlayerCastRequestResult.Success -> result.request
            is PlayerCastRequestResult.Failure -> {
                showPlayerNotice(
                    message = result.message,
                    recoveryType = PlayerRecoveryType.SOURCE
                )
                return@launch
            }
        }

        when (playerCastCoordinator.startCasting(request)) {
            CastStartResult.STARTED -> {
                showPlayerNotice(
                    message = appContext.getString(R.string.cast_started),
                    recoveryType = PlayerRecoveryType.NETWORK
                )
            }

            CastStartResult.ROUTE_SELECTION_REQUIRED -> {
                onRouteSelectionRequired()
            }

            CastStartResult.UNAVAILABLE -> {
                showPlayerNotice(
                    message = appContext.getString(R.string.cast_unavailable),
                    recoveryType = PlayerRecoveryType.SOURCE
                )
            }

            CastStartResult.UNSUPPORTED -> {
                showPlayerNotice(
                    message = toPlayerCastUnsupportedMessage(request),
                    recoveryType = PlayerRecoveryType.SOURCE
                )
            }
        }
    }
}

internal fun PlayerViewModel.observeCastPlaybackEvents() {
    viewModelScope.launch {
        playerCastCoordinator.playbackEvents.collect { event ->
            handleCastPlaybackEvent(event)
        }
    }
}

private fun PlayerViewModel.handleCastPlaybackEvent(event: CastPlaybackEvent) {
    if (event is CastPlaybackEvent.RouteSelectionCancelled) {
        return
    }
    val isSuccess = event is CastPlaybackEvent.MediaLoadSucceeded
        return
    }
    if (isSuccess) {
        playerEngine.pause()
    }
    showPlayerNotice(
        message = toPlayerCastPlaybackMessage(event),
        recoveryType = if (isSuccess) PlayerRecoveryType.NETWORK else PlayerRecoveryType.SOURCE
    )
}

fun PlayerViewModel.stopCasting() {
    playerCastCoordinator.stopCasting()
    showPlayerNotice(
        message = appContext.getString(R.string.cast_disconnected),
        recoveryType = PlayerRecoveryType.NETWORK
    )
}

fun PlayerViewModel.startManualRecording() {
    val channel = currentChannel.value
    if (currentContentType != ContentType.LIVE || channel == null || currentProviderId <= 0) {
        showPlayerNotice(message = "Recording needs a valid live channel context.")
        return
    }
    viewModelScope.launch {
        val now = System.currentTimeMillis()
        val result = playerRecordingCoordinator.startManualRecording(
            RecordingRequest(
                providerId = currentProviderId,
                channelId = channel.id,
                channelName = channel.name,
                streamUrl = currentStreamUrl,
                scheduledStartMs = now,
                scheduledEndMs = currentProgram.value?.endTime ?: (now + 30 * 60_000L),
                programTitle = currentProgram.value?.title
            )
        )
        if (result is Result.Error) {
            showPlayerNotice(message = result.message, recoveryType = PlayerRecoveryType.SOURCE)
        } else {
            showPlayerNotice(message = "Recording started for ${channel.name}.")
        }
    }
}

fun PlayerViewModel.scheduleRecording() {
}

fun PlayerViewModel.scheduleDailyRecording() {
}

fun PlayerViewModel.scheduleWeeklyRecording() {
}

    viewModelScope.launch {
        val result = playerRecordingCoordinator.scheduleRecording(
            ScheduleRecordingCommand(
                contentType = currentContentType,
                providerId = currentProviderId,
                channel = currentChannel.value,
                streamUrl = currentStreamUrl,
                currentProgram = currentProgram.value,
                nextProgram = nextProgram.value,
                recurrence = recurrence
            )
        )
        if (result is Result.Error) {
            showPlayerNotice(message = result.message, recoveryType = PlayerRecoveryType.SOURCE)
        } else {
            val recurrenceLabel = when (recurrence) {
            }
            val scheduledItem = (result as? Result.Success)?.data
            val title = scheduledItem?.programTitle ?: "Recording"
            showPlayerNotice(message = "$title scheduled$recurrenceLabel.")
        }
    }
}

fun PlayerViewModel.stopCurrentRecording() {
    viewModelScope.launch {
        val result = playerRecordingCoordinator.stopRecording(recording.id)
        if (result is Result.Error) {
            showPlayerNotice(message = result.message)
        } else {
            showPlayerNotice(message = "Recording stopped.")
        }
    }
}

internal suspend fun PlayerViewModel.buildCastRequest(): CastMediaRequest? {
    return (buildCastRequestResult() as? PlayerCastRequestResult.Success)?.request
}

internal suspend fun PlayerViewModel.buildCastRequestResult(): PlayerCastRequestResult {
    return when (currentContentType) {
        ContentType.LIVE -> {
            val channel = currentChannel.value
                ?: return PlayerCastRequestResult.Failure(
                    toPlayerCastMessage(CastMediaRequestUnsupportedReason.STREAM_UNAVAILABLE)
                )
            // Use preferStableUrl = true for Cast: the credential-based portal URL
            // does not expire, unlike the tokenized direct-source CDN URL.
            val streamInfo = playerChannelCoordinator.getStreamInfo(channel, preferStableUrl = true)
                .getOrNull()
                ?: return PlayerCastRequestResult.Failure(
                    toPlayerCastMessage(CastMediaRequestUnsupportedReason.STREAM_UNAVAILABLE)
                )
            toPlayerCastRequestResult(
                playerCastCoordinator.buildFromStreamInfo(
                    streamInfo = streamInfo,
                    title = mediaTitle.value ?: channel.name,
                    subtitle = currentProgram.value?.title,
                    artworkUrl = channel.logoUrl ?: currentArtworkUrl,
                    isLive = true,
                    startPositionMs = 0L
                )
            )
        }

        ContentType.MOVIE,
        ContentType.VOD -> {
            val movie = playerContentResolver.getMovie(currentContentId)
            val repositoryStreamInfo = movie?.let { playerContentResolver.getMovieStreamInfo(it).getOrNull() }
            val streamInfo = selectPreferredVodCastStreamInfo(
                activeStreamInfo = currentResolvedStreamInfo.takeIf { currentContentType == ContentType.MOVIE },
                activePlaybackUrl = currentResolvedPlaybackUrl,
                fallbackStreamInfo = repositoryStreamInfo
            )
                ?: return directCastRequest()
            toPlayerCastRequestResult(
                playerCastCoordinator.buildFromStreamInfo(
                    streamInfo = streamInfo,
                    title = currentTitle.ifBlank { movie?.name.orEmpty() },
                    subtitle = movie?.genre,
                    artworkUrl = currentArtworkUrl ?: movie?.posterUrl ?: movie?.backdropUrl,
                    isLive = false,
                    startPositionMs = playerEngine.currentPosition.value
                )
            )
        }

        ContentType.SERIES,
        ContentType.SERIES_EPISODE -> buildSeriesCastRequestResult()
    }
}

private suspend fun PlayerViewModel.buildSeriesCastRequestResult(): PlayerCastRequestResult {
    val resolution = resolvePlaybackStreamResolution(
        logicalUrl = currentStreamUrl,
        internalContentId = currentStableEpisodeId?.takeIf { it > 0L } ?: currentContentId,
        providerId = currentProviderId,
        contentType = currentContentType,
    )
    resolution.credentialFailureMessage?.let { message ->
        return PlayerCastRequestResult.Failure(message)
    }
    resolution.resolutionFailureMessage?.let { message ->
        return PlayerCastRequestResult.Failure(message)
    }
    val streamInfo = selectPreferredVodCastStreamInfo(
        activeStreamInfo = currentResolvedStreamInfo.takeIf {
            currentContentType == ContentType.SERIES || currentContentType == ContentType.SERIES_EPISODE
        },
        activePlaybackUrl = currentResolvedPlaybackUrl,
        fallbackStreamInfo = resolution.streamInfo
    )
        ?: return PlayerCastRequestResult.Failure(
            toPlayerCastMessage(CastMediaRequestUnsupportedReason.STREAM_UNAVAILABLE)
        )
    val episode = currentEpisode.value
    val series = currentSeries.value
    val castTitle = if (series != null && episode != null) {
        "${series.name} - S${episode.seasonNumber}E${episode.episodeNumber}"
    } else {
        currentTitle.ifBlank { episode?.let(::buildEpisodePlaybackTitle).orEmpty() }
    }
    return toPlayerCastRequestResult(
        playerCastCoordinator.buildFromStreamInfo(
            streamInfo = streamInfo,
            title = castTitle,
            subtitle = episode?.title,
            artworkUrl = currentArtworkUrl ?: episode?.coverUrl ?: series?.posterUrl ?: series?.backdropUrl,
            isLive = false,
            startPositionMs = playerEngine.currentPosition.value
        )
    )
}

internal fun PlayerViewModel.directCastRequest(): PlayerCastRequestResult {
    val url = currentStreamUrl.takeIf { it.isNotBlank() }
        ?: return PlayerCastRequestResult.Failure(
            toPlayerCastMessage(CastMediaRequestUnsupportedReason.EMPTY_URL)
        )
    return toPlayerCastRequestResult(
        playerCastCoordinator.buildFromStreamInfo(
            streamInfo = StreamInfo(url = url),
            title = currentTitle,
            subtitle = null,
            artworkUrl = currentArtworkUrl,
            isLive = false,
            startPositionMs = playerEngine.currentPosition.value
        )
    )
}

private fun PlayerViewModel.toPlayerCastRequestResult(
    result: CastMediaRequestBuildResult
): PlayerCastRequestResult = when (result) {
    is CastMediaRequestBuildResult.Success -> PlayerCastRequestResult.Success(result.request)
    is CastMediaRequestBuildResult.Unsupported -> PlayerCastRequestResult.Failure(toPlayerCastMessage(result.reason))
}

sealed interface PlayerCastRequestResult {
    data class Success(val request: CastMediaRequest) : PlayerCastRequestResult
    data class Failure(val message: String) : PlayerCastRequestResult
}

private fun PlayerViewModel.toPlayerCastMessage(
    reason: CastMediaRequestUnsupportedReason
): String = appContext.getString(
    when (reason) {
        CastMediaRequestUnsupportedReason.STREAM_UNAVAILABLE,
        CastMediaRequestUnsupportedReason.EMPTY_URL -> R.string.cast_item_unavailable
        CastMediaRequestUnsupportedReason.UNSUPPORTED_PROTOCOL -> R.string.cast_protocol_unsupported
        CastMediaRequestUnsupportedReason.DRM_PROTECTED -> R.string.cast_drm_unsupported
    }
)

private fun PlayerViewModel.toPlayerCastUnsupportedMessage(request: CastMediaRequest): String = appContext.getString(
    when (request.rewriteRequiredReason) {
        CastRewriteRequiredReason.LOCAL_URI -> R.string.cast_local_url_unsupported
        CastRewriteRequiredReason.CUSTOM_HEADERS -> R.string.cast_headers_unsupported
        CastRewriteRequiredReason.CUSTOM_USER_AGENT -> R.string.cast_user_agent_unsupported
        CastRewriteRequiredReason.PROXY -> R.string.cast_proxy_unsupported
        CastRewriteRequiredReason.INVALID_SSL,
        CastRewriteRequiredReason.SCOPED_TRANSPORT -> R.string.cast_invalid_ssl_unsupported
        null -> R.string.cast_stream_unsupported
    }
)

private fun PlayerViewModel.toPlayerCastPlaybackMessage(event: CastPlaybackEvent): String = appContext.getString(
    when (event) {
        is CastPlaybackEvent.MediaLoadSucceeded -> R.string.cast_started
        is CastPlaybackEvent.MediaLoadFailed -> R.string.cast_load_failed
        is CastPlaybackEvent.SessionStartFailed -> R.string.cast_session_failed
        is CastPlaybackEvent.ReceiverUnavailable -> R.string.cast_receiver_unavailable
        CastPlaybackEvent.RouteSelectionCancelled -> R.string.cast_selection_cancelled
    }
)
