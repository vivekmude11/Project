package com.sia.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.sia.app.ui.navigation.SiaApp
import com.sia.app.ui.theme.Bg
import com.sia.app.ui.theme.SiaTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            SiaTheme {
                Surface(modifier = Modifier.fillMaxSize().background(Bg), color = Bg) {
                    SiaApp()
                }
            }
        }
    }
}
