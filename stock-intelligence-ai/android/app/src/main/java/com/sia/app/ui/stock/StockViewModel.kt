package com.sia.app.ui.stock

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sia.app.core.UiState
import com.sia.app.data.remote.dto.AnalysisDto
import com.sia.app.data.repo.StockRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class StockViewModel @Inject constructor(
    private val repo: StockRepository,
) : ViewModel() {

    private val _state = MutableStateFlow<UiState<AnalysisDto>>(UiState.Loading)
    val state: StateFlow<UiState<AnalysisDto>> = _state.asStateFlow()

    fun load(symbol: String) {
        _state.value = UiState.Loading
        viewModelScope.launch {
            repo.analysis(symbol, hitRate = 0.68)
                .onSuccess { dto ->
                    if (dto.error != null) _state.value = UiState.Error("No analysis: ${dto.error}")
                    else _state.value = UiState.Success(dto)
                }
                .onFailure { _state.value = UiState.Error(it.message ?: "Request failed") }
        }
    }
}
