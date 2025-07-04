<template>
  <div class="container-main spacing-section">
    <!-- ヘッダー -->
    <div class="text-center">
      <h1 class="text-heading text-4xl animate-fade-in">
        UnoCSS テスト - Phase 1-4-1
      </h1>
      <p class="text-body-sm text-muted mt-2">
        天気アプリ特化カラーシステム & ショートカット動作確認
      </p>
    </div>

    <!-- カラーテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">カラーシステム</h2>
      
      <!-- プライマリ・セカンダリ -->
      <div class="grid-responsive mb-6">
        <div class="card p-4 bg-primary-500 text-white">Primary 500</div>
        <div class="card p-4 bg-secondary-500 text-white">Secondary 500</div>
        <div class="card p-4 bg-success-500 text-white">Success 500</div>
      </div>

      <!-- 天気カラー -->
      <div class="grid-responsive">
        <div class="weather-card weather-sunny">
          <span class="text-3xl mb-2">☀️</span>
          <span class="font-semibold">Sunny Weather</span>
        </div>
        <div class="weather-card weather-rainy">
          <span class="text-3xl mb-2">🌧️</span>
          <span class="font-semibold">Rainy Weather</span>
        </div>
        <div class="weather-card weather-cloudy">
          <span class="text-3xl mb-2">☁️</span>
          <span class="font-semibold">Cloudy Weather</span>
        </div>
        <div class="weather-card weather-stormy">
          <span class="text-3xl mb-2">⛈️</span>
          <span class="font-semibold">Stormy Weather</span>
        </div>
      </div>
    </section>

    <!-- レイアウトテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">レイアウトシステム</h2>
      
      <div class="card p-6 mb-6">
        <h3 class="text-heading text-lg mb-3">Flexbox Shortcuts</h3>
        <div class="space-y-3">
          <div class="flex-between p-3 bg-secondary-50 rounded">
            <span>flex-between</span>
            <span>→</span>
          </div>
          <div class="flex-center p-3 bg-secondary-50 rounded">
            <span>flex-center</span>
          </div>
          <div class="flex-start gap-2 p-3 bg-secondary-50 rounded">
            <span>✓</span>
            <span>flex-start with gap</span>
          </div>
        </div>
      </div>

      <div class="card p-6">
        <h3 class="text-heading text-lg mb-3">Grid System</h3>
        <div class="grid-auto-fit">
          <div class="p-4 bg-primary-100 rounded text-center">Auto Fit 1</div>
          <div class="p-4 bg-primary-100 rounded text-center">Auto Fit 2</div>
          <div class="p-4 bg-primary-100 rounded text-center">Auto Fit 3</div>
        </div>
      </div>
    </section>

    <!-- アニメーションテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">アニメーション</h2>
      <div class="grid-responsive">
        <div class="card p-6 text-center animate-fade-in">
          <h4 class="text-heading text-base mb-2">Fade In</h4>
          <span class="text-3xl animate-pulse-weather">☀️</span>
        </div>
        <div class="card p-6 text-center animate-slide-up">
          <h4 class="text-heading text-base mb-2">Slide Up</h4>
          <span class="text-3xl">🌧️</span>
        </div>
        <div class="card p-6 text-center animate-scale-in">
          <h4 class="text-heading text-base mb-2">Scale In</h4>
          <span class="text-3xl">⛈️</span>
        </div>
      </div>
    </section>

    <!-- ボタンテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">ボタンシステム</h2>
      <div class="card p-6">
        <div class="flex flex-wrap gap-3">
          <button class="btn-primary btn-sm">Primary Small</button>
          <button class="btn-primary btn-md">Primary Medium</button>
          <button class="btn-outline btn-md">Outline</button>
          <button class="btn-green btn-md">Success</button>
          <button class="btn-red btn-md">Error</button>
        </div>
      </div>
    </section>

    <!-- アラートテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">アラートシステム</h2>
      <div class="spacing-compact">
        <div class="alert-blue">情報アラート - プライマリカラー使用</div>
        <div class="alert-green">成功アラート - 処理が完了しました</div>
        <div class="alert-red">エラーアラート - 何か問題が発生しました</div>
        <div class="alert-warning">警告アラート - 注意が必要です</div>
      </div>
    </section>

    <!-- グラデーション・エフェクトテスト -->
    <section class="spacing-content bg-sky-gradient p-8 rounded-2xl">
      <h2 class="text-white text-2xl mb-4 font-semibold">天気エフェクト</h2>
      <div class="grid-responsive">
        <div class="glass-effect p-6 rounded-xl text-white">
          <h4 class="font-semibold mb-2">Glass Effect</h4>
          <p class="text-sm opacity-90">背景ぼかし効果</p>
        </div>
        <div class="bg-weather-gradient-sunny p-6 rounded-xl text-white">
          <h4 class="font-semibold mb-2">Sunny Gradient</h4>
          <div class="flex-center gap-2">
            <span class="text-2xl">☀️</span>
            <span>25°C</span>
          </div>
        </div>
        <div class="bg-weather-gradient-rainy p-6 rounded-xl text-white">
          <h4 class="font-semibold mb-2">Rainy Gradient</h4>
          <div class="flex-center gap-2">
            <span class="text-2xl">🌧️</span>
            <span>18°C</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ダークモードテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">ダークモード</h2>
      <div class="card p-6">
        <p class="text-body mb-4">
          ダークモード切り替えのテスト。HTMLの<code class="font-mono bg-secondary-100 dark:bg-secondary-800 px-2 py-1 rounded text-sm">.dark</code>クラスで切り替わります。
        </p>
        <button 
          @click="toggleDarkMode" 
          class="btn-outline flex-center gap-2"
        >
          <span>{{ isDark ? '☀️' : '🌙' }}</span>
          {{ isDark ? 'ライトモード' : 'ダークモード' }}に切り替え
        </button>
      </div>
    </section>

    <!-- フォームテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">フォームコンポーネント</h2>
      <div class="card p-6 max-w-md">
        <div class="spacing-comfortable">
          <div>
            <label class="text-body font-medium mb-2 block">地点選択</label>
            <select class="form-select">
              <option>東京</option>
              <option>大阪</option>
              <option>札幌</option>
            </select>
          </div>
          
          <div>
            <label class="text-body font-medium mb-2 block">コメント</label>
            <input 
              type="text" 
              placeholder="天気コメントを入力..." 
              class="form-input"
            >
          </div>
          
          <button class="btn-primary w-full">
            生成開始
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

definePageMeta({
  title: 'UnoCSS Test - Phase 1-4-1'
})

const isDark = ref(false)

const toggleDarkMode = () => {
  isDark.value = !isDark.value
  if (process.client) {
    document.documentElement.classList.toggle('dark', isDark.value)
  }
}

onMounted(() => {
  if (process.client) {
    isDark.value = document.documentElement.classList.contains('dark')
  }
})
</script>