package com.streamvault.data.manager


    candidateStartMs: Long,
    candidateEndMs: Long,
    return firstOrNull { item ->
        item.status in statuses &&
            item.scheduledStartMs < candidateEndMs &&
            item.scheduledEndMs > candidateStartMs
    }
}

internal fun Iterable<RecordingRunEntity>.findRecordingRunConflict(
    candidateStartMs: Long,
    candidateEndMs: Long,
    ignoredRunId: String? = null
): RecordingRunEntity? {
    return firstOrNull { item ->
        item.id != ignoredRunId &&
            item.scheduleEnabled &&
            item.status in statuses &&
            item.scheduledStartMs < candidateEndMs &&
            item.scheduledEndMs > candidateStartMs
    }
}

internal fun RecordingRunEntity.toConflictFailure(
    conflictStartMs: Long,
    conflictEndMs: Long,
    reason: String,
    nowMs: Long = System.currentTimeMillis()
): RecordingRunEntity {
    return copy(
        id = java.util.UUID.randomUUID().toString(),
        scheduledStartMs = conflictStartMs,
        scheduledEndMs = conflictEndMs,
        sourceType = com.streamvault.domain.model.RecordingSourceType.UNKNOWN,
        resolvedUrl = null,
        headersJson = "{}",
        userAgent = null,
        expirationTime = null,
        providerLabel = null,
        outputUri = null,
        outputDisplayPath = null,
        bytesWritten = 0L,
        averageThroughputBytesPerSecond = 0L,
        retryCount = 0,
        lastProgressAtMs = null,
        failureCategory = RecordingFailureCategory.SCHEDULE_CONFLICT,
        failureReason = reason,
        terminalAtMs = nowMs,
        startedAtMs = null,
        endedAtMs = nowMs,
        scheduleEnabled = false,
        alarmStartAtMs = null,
        alarmStopAtMs = null,
        createdAt = nowMs,
        updatedAt = nowMs
    )
}
