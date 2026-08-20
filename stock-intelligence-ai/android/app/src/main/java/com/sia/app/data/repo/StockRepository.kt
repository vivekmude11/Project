package com.sia.app.data.repo

import com.sia.app.data.remote.SiaApi
import com.sia.app.data.remote.dto.AnalysisDto
import com.sia.app.data.remote.dto.StockSummaryDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class StockRepository @Inject constructor(private val api: SiaApi) {

    suspend fun analysis(symbol: String, hitRate: Double? = null): Result<AnalysisDto> =
        safeCall { api.analysis(symbol, hitRate = hitRate) }

    suspend fun summary(symbol: String): Result<StockSummaryDto> =
        safeCall { api.summary(symbol) }

    private suspend fun <T> safeCall(block: suspend () -> T): Result<T> =
        withContext(Dispatchers.IO) { runCatching { block() } }
}
