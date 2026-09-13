package com.streamvault.domain.manager

import com.streamvault.domain.model.ProviderType

data class ProviderCredentials(
    val serverUrl: String,
    val username: String,
    val password: String,
    val providerType: ProviderType? = null,
)
