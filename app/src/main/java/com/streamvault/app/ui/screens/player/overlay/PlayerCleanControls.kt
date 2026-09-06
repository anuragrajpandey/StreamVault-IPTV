package com.streamvault.app.ui.screens.player.overlay

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AspectRatio
import androidx.compose.material.icons.filled.AudioFile
import androidx.compose.material.icons.filled.Cast
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.HighQuality
import androidx.compose.material.icons.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Pause
import androidx.compose.material.icons.filled.PictureInPictureAlt
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Replay10
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.SkipNext
import androidx.compose.material.icons.filled.Subtitles
import androidx.compose.material.icons.filled.VolumeOff
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.tv.material3.ClickableSurfaceDefaults
import androidx.tv.material3.Icon
import androidx.tv.material3.MaterialTheme
import androidx.tv.material3.Text
import com.streamvault.app.R
import com.streamvault.app.ui.interaction.TvClickableSurface
import com.streamvault.app.ui.screens.player.SeekPreviewState
import com.streamvault.app.ui.screens.player.SleepTimerUiState
import com.streamvault.app.ui.screens.player.PlayerTimeshiftUiState
import com.streamvault.app.ui.theme.Primary
import com.streamvault.domain.model.Channel
import com.streamvault.domain.model.Program
import com.streamvault.domain.model.RecordingStatus
import java.util.Locale

private val ClearWhite = Color.White
private val Glass = Color.White.copy(alpha = 0.075f)
private val GlassStrong = Color.White.copy(alpha = 0.14f)

@Composable
fun PlayerCleanControls(
    visible: Boolean,
    title: String,
    contentType: String,
    isCatchUpPlayback: Boolean,
    isPlaying: Boolean,
    currentProgram: Program?,
    currentChannel: Channel?,
    currentChannelName: String?,
    displayChannelNumber: Int,
    currentPosition: Long,
    duration: Long,
    aspectRatioLabel: String,
    subtitleTrackCount: Int,
    liveTranslationAvailable: Boolean,
    audioTrackCount: Int,
    videoQualityCount: Int,
    currentRecordingStatus: RecordingStatus?,
    isMuted: Boolean,
    playbackSpeed: Float,
    mediaTitle: String?,
    sleepTimerUiState: SleepTimerUiState,
    timeshiftUiState: PlayerTimeshiftUiState,
    playButtonFocusRequester: FocusRequester,
    quickActionsFocusRequester: FocusRequester,
    onClose: () -> Unit,
    onTogglePlayPause: () -> Unit,
    onSeekBackward: () -> Unit,
    onSeekForward: () -> Unit,
    onRestartProgram: () -> Unit,
    onOpenArchive: () -> Unit,
    onStartRecording: () -> Unit,
    onStopRecording: () -> Unit,
    onScheduleRecording: () -> Unit,
    onScheduleDailyRecording: () -> Unit,
    onScheduleWeeklyRecording: () -> Unit,
    onToggleAspectRatio: () -> Unit,
    onOpenSubtitleTracks: () -> Unit,
    onOpenAudioTracks: () -> Unit,
    onOpenVideoTracks: () -> Unit,
    onOpenPlaybackSpeed: () -> Unit,
    onOpenStopPlaybackTimer: () -> Unit,
    onOpenIdleStandbyTimer: () -> Unit,
    onOpenAudioVideoSync: () -> Unit,
    audioVideoSyncEnabled: Boolean,
    showEpisodesAction: Boolean,
    onOpenEpisodes: () -> Unit,
    onOpenSplitScreen: () -> Unit,
    onEnterPictureInPicture: () -> Unit,
    onToggleMute: () -> Unit,
    isCastConnected: Boolean,
    onCast: () -> Unit,
    onStopCasting: () -> Unit,
    onSeekToLiveEdge: () -> Unit,
    onSeekToPosition: (Long) -> Unit,
    onSetScrubbingMode: (Boolean) -> Unit,
    showExternalPlayerAction: Boolean,
    onOpenExternalPlayer: () -> Unit,
    seekPreview: SeekPreviewState,
    onSeekPreviewPositionChanged: (Long?) -> Unit,
    onUserInteraction: () -> Unit,
    modifier: Modifier = Modifier
) {
    if (!visible) return

    var sliderValue by remember(duration, currentPosition) {
        mutableStateOf(if (duration > 0) currentPosition.toFloat() / duration else 0f)
    }
    var scrubbing by remember { mutableStateOf(false) }

    LaunchedEffect(duration, currentPosition, scrubbing) {
        if (!scrubbing) sliderValue = if (duration > 0) currentPosition.toFloat() / duration else 0f
    }

    Box(modifier = modifier.fillMaxSize().background(Color.Transparent)) {
        Box(
            modifier = Modifier
                .fillMaxHeight()
                .aspectRatio(16f / 9f, matchHeightConstraintsFirst = true)
                .align(Alignment.Center)
        ) {
        Row(
            modifier = Modifier.fillMaxWidth().align(Alignment.TopCenter).padding(horizontal = 32.dp, vertical = 24.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title.ifBlank { mediaTitle.orEmpty() },
                    color = ClearWhite,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                if (contentType == "LIVE" && !currentChannelName.isNullOrBlank()) {
                    Text(
                        text = if (displayChannelNumber > 0) "$displayChannelNumber  •  $currentChannelName" else currentChannelName,
                        color = ClearWhite.copy(alpha = 0.68f),
                        style = MaterialTheme.typography.bodySmall,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
            CleanIconButton(Icons.Default.Close, stringResource(R.string.settings_close_app), onClose)
        }

        Column(
            modifier = Modifier.align(Alignment.Center).padding(horizontal = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(22.dp)
        ) {
            if (seekPreview.visible) {
                Text(
                    text = "${formatCleanDuration(seekPreview.positionMs)}  •  ${seekPreview.title}",
                    color = ClearWhite,
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Medium
                )
            }
            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                CleanIconButton(Icons.Default.Replay10, stringResource(R.string.player_rewind), onSeekBackward, 54.dp)
                TvClickableSurface(
                    onClick = { onUserInteraction(); onTogglePlayPause() },
                    shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(999.dp)),
                    colors = ClickableSurfaceDefaults.colors(
                        containerColor = Primary.copy(alpha = 0.92f),
                        focusedContainerColor = Primary
                    ),
                    modifier = Modifier.size(72.dp).focusRequester(playButtonFocusRequester).semantics {
                        contentDescription = if (isPlaying) "Pause" else "Play"
                    }
                ) {
                    Icon(
                        imageVector = if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                        contentDescription = null,
                        tint = ClearWhite,
                        modifier = Modifier.size(34.dp)
                    )
                }
                CleanIconButton(Icons.Default.KeyboardArrowRight, stringResource(R.string.player_forward), onSeekForward, 54.dp)
                if (showEpisodesAction) {
                    CleanIconButton(Icons.Default.SkipNext, stringResource(R.string.player_episodes), onOpenEpisodes, 54.dp)
                }
            }
        }

        Column(
            modifier = Modifier.align(Alignment.BottomCenter).fillMaxWidth().padding(horizontal = 32.dp, vertical = 22.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            if (duration > 0) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(formatCleanDuration(if (scrubbing) (sliderValue * duration).toLong() else currentPosition), color = ClearWhite, style = MaterialTheme.typography.labelSmall)
                    Slider(
                        value = sliderValue.coerceIn(0f, 1f),
                        onValueChange = {
                            if (!scrubbing) {
                                scrubbing = true
                                onSetScrubbingMode(true)
                            }
                            sliderValue = it.coerceIn(0f, 1f)
                            onSeekPreviewPositionChanged((sliderValue * duration).toLong())
                        },
                        onValueChangeFinished = {
                            onSeekToPosition((sliderValue * duration).toLong())
                            onSetScrubbingMode(false)
                            onSeekPreviewPositionChanged(null)
                            scrubbing = false
                        },
                        modifier = Modifier.weight(1f).padding(horizontal = 10.dp).semantics { contentDescription = "Playback position" },
                        colors = SliderDefaults.colors(
                            activeTrackColor = Primary,
                            inactiveTrackColor = ClearWhite.copy(alpha = 0.26f),
                            thumbColor = Primary
                        )
                    )
                    Text(formatCleanDuration(duration), color = ClearWhite.copy(alpha = 0.72f), style = MaterialTheme.typography.labelSmall)
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (subtitleTrackCount > 0) CleanIconButton(Icons.Default.Subtitles, stringResource(R.string.player_subs), onOpenSubtitleTracks)
                if (audioTrackCount > 0) CleanIconButton(Icons.Default.AudioFile, stringResource(R.string.player_audio), onOpenAudioTracks)
                if (videoQualityCount > 0) CleanIconButton(Icons.Default.HighQuality, stringResource(R.string.player_video_quality), onOpenVideoTracks)
                CleanIconButton(Icons.Default.Settings, "Playback settings", onOpenPlaybackSpeed)
                CleanIconButton(if (isMuted) Icons.Default.VolumeOff else Icons.Default.VolumeUp, if (isMuted) stringResource(R.string.player_unmute) else stringResource(R.string.player_mute), onToggleMute)
                if (isCastConnected) CleanIconButton(Icons.Default.Cast, stringResource(R.string.player_stop_casting), onStopCasting)
                else CleanIconButton(Icons.Default.Cast, stringResource(R.string.player_cast), onCast)
                Spacer(Modifier.weight(1f))
                CleanIconButton(Icons.Default.AspectRatio, aspectRatioLabel, onToggleAspectRatio)
                CleanIconButton(Icons.Default.PictureInPictureAlt, "Picture in picture", onEnterPictureInPicture)
            }
        }
        }
    }
}

@Composable
private fun CleanIconButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    description: String,
    onClick: () -> Unit,
    size: androidx.compose.ui.unit.Dp = 46.dp
) {
    TvClickableSurface(
        onClick = onClick,
        shape = ClickableSurfaceDefaults.shape(RoundedCornerShape(999.dp)),
        colors = ClickableSurfaceDefaults.colors(
            containerColor = Glass,
            focusedContainerColor = GlassStrong
        ),
        modifier = Modifier.size(size).semantics { contentDescription = description }
    ) {
        Icon(icon, contentDescription = null, tint = ClearWhite, modifier = Modifier.size(size * 0.48f))
    }
}

private fun formatCleanDuration(ms: Long): String {
    val seconds = ms.coerceAtLeast(0L) / 1000L
    val h = seconds / 3600L
    val m = (seconds % 3600L) / 60L
    val s = seconds % 60L
    return if (h > 0) String.format(Locale.getDefault(), "%02d:%02d:%02d", h, m, s)
    else String.format(Locale.getDefault(), "%02d:%02d", m, s)
}
