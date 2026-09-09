package com.streamvault.data.sync

import java.util.concurrent.ConcurrentHashMap

internal object InitialCatalogCallbackRegistry {
    private val callbacks = ConcurrentHashMap<Long, suspend () -> Unit>()

    fun register(providerId: Long, callback: suspend () -> Unit) { callbacks[providerId] = callback }
    fun take(providerId: Long): suspend () -> Unit = callbacks.remove(providerId) ?: {}
    fun clear(providerId: Long) { callbacks.remove(providerId) }
}
