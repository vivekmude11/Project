package com.sia.app.data.remote

import com.sia.app.data.remote.dto.AnalysisDto
import com.sia.app.data.remote.dto.StockSummaryDto
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface SiaApi {

    @GET("stock/{symbol}/analysis")
    suspend fun analysis(
        @Path("symbol") symbol: String,
        @Query("exchange") exchange: String = "NSE",
        @Query("hit_rate") hitRate: Double? = null,
    ): AnalysisDto

    @GET("stock/{symbol}")
    suspend fun summary(
        @Path("symbol") symbol: String,
        @Query("exchange") exchange: String = "NSE",
    ): StockSummaryDto
}
