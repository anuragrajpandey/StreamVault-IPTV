package com.streamvault.data.manager

import com.google.common.truth.Truth.assertThat
import org.junit.Test

class RecordingConflictDetectorTest {

    @Test
    fun `findRecordingConflict returns overlapping scheduled item`() {
        val conflict = listOf(
            recordingItem(
                id = "scheduled-1",
                startMs = 1_000L,
                endMs = 5_000L,
            )
        ).findRecordingConflict(
            candidateStartMs = 2_000L,
            candidateEndMs = 4_000L,
        )

        assertThat(conflict?.id).isEqualTo("scheduled-1")
    }

    @Test
    fun `findRecordingConflict ignores terminal recordings`() {
        val conflict = listOf(
            recordingItem(
                id = "completed-1",
                startMs = 1_000L,
                endMs = 5_000L,
            )
        ).findRecordingConflict(
            candidateStartMs = 2_000L,
            candidateEndMs = 4_000L,
        )

        assertThat(conflict).isNull()
    }

    @Test
    fun `findRecordingConflict treats adjacent windows as non-overlapping`() {
        val conflict = listOf(
            recordingItem(
                id = "recording-1",
                startMs = 1_000L,
                endMs = 5_000L,
            )
        ).findRecordingConflict(
            candidateStartMs = 5_000L,
            candidateEndMs = 8_000L,
        )

        assertThat(conflict).isNull()
    }

    @Test
    fun `findRecordingRunConflict returns overlapping manual run for recurring candidate`() {
        val conflict = listOf(
            recordingRun(
                id = "manual-1",
                startMs = 10_000L,
                endMs = 20_000L,
            )
        ).findRecordingRunConflict(
            candidateStartMs = 12_000L,
            candidateEndMs = 18_000L,
        )

        assertThat(conflict?.id).isEqualTo("manual-1")
    }

    @Test
    fun `toConflictFailure marks skipped recurring run as failed conflict`() {
        val failed = recordingRun(
            id = "recurring-1",
            startMs = 10_000L,
            endMs = 20_000L,
            recurringRuleId = "rule-1"
        ).toConflictFailure(
            conflictStartMs = 30_000L,
            conflictEndMs = 40_000L,
            reason = "Skipped recurring occurrence because it conflicts with 'Manual recording'.",
            nowMs = 25_000L
        )

        assertThat(failed.id).isNotEqualTo("recurring-1")
        assertThat(failed.failureCategory).isEqualTo(RecordingFailureCategory.SCHEDULE_CONFLICT)
        assertThat(failed.scheduleEnabled).isFalse()
        assertThat(failed.scheduledStartMs).isEqualTo(30_000L)
        assertThat(failed.scheduledEndMs).isEqualTo(40_000L)
    }

    private fun recordingItem(
        id: String,
        startMs: Long,
        endMs: Long,
        id = id,
        providerId = 1L,
        channelId = 100L,
        channelName = "Sports 1",
        streamUrl = "https://example.com/live.ts",
        scheduledStartMs = startMs,
        scheduledEndMs = endMs,
        programTitle = "Match Day",
        outputPath = "/tmp/$id.ts",
        status = status
    )

    private fun recordingRun(
        id: String,
        startMs: Long,
        endMs: Long,
        recurringRuleId: String? = null
    ) = RecordingRunEntity(
        id = id,
        scheduleId = 1L,
        providerId = 1L,
        channelId = 100L,
        channelName = "Sports 1",
        streamUrl = "https://example.com/live.ts",
        programTitle = "Match Day",
        scheduledStartMs = startMs,
        scheduledEndMs = endMs,
        recurrence = recurrence,
        recurringRuleId = recurringRuleId,
        status = status,
        sourceType = RecordingSourceType.UNKNOWN,
        headersJson = "{}",
        failureCategory = RecordingFailureCategory.NONE,
        scheduleEnabled = true
    )
}
