<template>
  <div class="container-main spacing-section">
    <!-- ヘッダーセクション -->
    <div class="text-center spacing-comfortable">
      <h1 class="text-heading text-4xl animate-fade-in">
        UnoCSS 設定テスト
      </h1>
      <p class="text-body-sm text-muted">
        Phase 1-4-1: UnoCSS基盤設定の動作確認
      </p>
    </div>

    <!-- カラーパレットテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">カラーパレット</h2>
      
      <!-- プライマリカラー -->
      <div class="mb-6">
        <h3 class="text-heading text-lg mb-3">Primary Colors</h3>
        <div class="grid-responsive">
          <div class="card p-4 bg-primary-50 text-primary-900">Primary 50</div>
          <div class="card p-4 bg-primary-500 text-white">Primary 500</div>
          <div class="card p-4 bg-primary-700 text-white">Primary 700</div>
        </div>
      </div>

      <!-- 天気カラー -->
      <div class="mb-6">
        <h3 class="text-heading text-lg mb-3">Weather Colors</h3>
        <div class="grid-responsive">
          <div class="card p-4 bg-weather-sunny text-white rounded-lg">
            <div class="flex-center gap-2">
              <span>☀️ Sunny</span>
            </div>
          </div>
          <div class="card p-4 bg-weather-rainy text-white rounded-lg">
            <div class="flex-center gap-2">
              <span>🌧️ Rainy</span>
            </div>
          </div>
          <div class="card p-4 bg-weather-cloudy text-white rounded-lg">
            <div class="flex-center gap-2">
              <span>☁️ Cloudy</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ステータスカラー -->
      <div class="mb-6">
        <h3 class="text-heading text-lg mb-3">Status Colors</h3>
        <div class="grid-responsive">
          <div class="alert-green">Success Alert</div>
          <div class="alert-blue">Info Alert</div>
          <div class="alert-red">Error Alert</div>
        </div>
      </div>
    </section>

    <!-- アイコンテスト（絵文字版） -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">アイコンシステム（絵文字版）</h2>
      <div class="grid-responsive">
        <!-- 天気アイコン -->
        <div class="card p-6 text-center spacing-compact">
          <h4 class="text-heading text-base">天気アイコン</h4>
          <div class="flex-center gap-4 text-3xl">
            <span class="animate-pulse-weather">☀️</span>
            <span>🌧️</span>
            <span>❄️</span>
            <span>⛈️</span>
          </div>
        </div>

        <!-- UI アイコン -->
        <div class="card p-6 text-center spacing-compact">
          <h4 class="text-heading text-base">UI アイコン</h4>
          <div class="flex-center gap-4 text-2xl text-secondary-600">
            <span>📍</span>
            <span class="animate-spin">⟳</span>
            <span>🔄</span>
          </div>
        </div>

        <!-- その他アイコン -->
        <div class="card p-6 text-center spacing-compact">
          <h4 class="text-heading text-base">その他アイコン</h4>
          <div class="flex-center gap-4 text-2xl text-primary-600">
            <span>☁️</span>
            <span>🌞</span>
            <span>🌙</span>
          </div>
        </div>
      </div>
    </section>

    <!-- レイアウトテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">レイアウトシステム</h2>
      
      <!-- Flexbox テスト -->
      <div class="card p-6 mb-6">
        <h4 class="text-heading text-base mb-3">Flexbox Utilities</h4>
        <div class="space-y-4">
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

      <!-- Grid テスト -->
      <div class="card p-6">
        <h4 class="text-heading text-base mb-3">Grid System</h4>
        <div class="grid-auto-fit">
          <div class="p-4 bg-primary-100 rounded text-center">Item 1</div>
          <div class="p-4 bg-primary-100 rounded text-center">Item 2</div>
          <div class="p-4 bg-primary-100 rounded text-center">Item 3</div>
        </div>
      </div>
    </section>

    <!-- タイポグラフィテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">タイポグラフィ</h2>
      <div class="card p-6 spacing-comfortable">
        <h1 class="text-heading text-4xl">Display Font H1</h1>
        <h2 class="text-subheading text-2xl">Display Font H2</h2>
        <h3 class="text-heading text-xl">Display Font H3</h3>
        <p class="text-body">
          これは本文テキストです。Inter フォントを使用しており、読みやすさを重視した設計になっています。
          <a href="#" class="text-link">こちらはリンクテキスト</a>の例です。
        </p>
        <p class="text-body-sm">小さなテキストサイズの例です。</p>
        <p class="text-muted">ミュートされたテキストの例です。</p>
        <code class="font-mono bg-secondary-100 px-2 py-1 rounded text-sm">
          モノスペースフォントのコード例
        </code>
      </div>
    </section>

    <!-- ボタンテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">ボタンシステム</h2>
      <div class="card p-6">
        <div class="flex flex-wrap gap-4">
          <button class="btn-primary btn-sm">Primary Small</button>
          <button class="btn-primary btn-md">Primary Medium</button>
          <button class="btn-primary btn-lg">Primary Large</button>
          <button class="btn-outline btn-md">Outline</button>
          <button class="btn-green btn-md">Success</button>
          <button class="btn-red btn-md">Error</button>
          <button class="btn-gray btn-md">Secondary</button>
        </div>
      </div>
    </section>

    <!-- アニメーションテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">アニメーション</h2>
      <div class="grid-responsive">
        <div class="card p-6 text-center animate-fade-in">
          <h4 class="text-heading text-base mb-2">Fade In</h4>
          <p class="text-muted">animate-fade-in</p>
        </div>
        <div class="card p-6 text-center animate-slide-up">
          <h4 class="text-heading text-base mb-2">Slide Up</h4>
          <p class="text-muted">animate-slide-up</p>
        </div>
        <div class="card p-6 text-center animate-scale-in">
          <h4 class="text-heading text-base mb-2">Scale In</h4>
          <p class="text-muted">animate-scale-in</p>
        </div>
      </div>
    </section>

    <!-- シャドウテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">シャドウシステム</h2>
      <div class="grid-responsive">
        <div class="p-6 bg-white rounded-lg shadow-soft border">
          <h4 class="text-heading text-base">Soft Shadow</h4>
          <p class="text-muted text-sm">shadow-soft</p>
        </div>
        <div class="p-6 bg-white rounded-lg shadow-medium border">
          <h4 class="text-heading text-base">Medium Shadow</h4>
          <p class="text-muted text-sm">shadow-medium</p>
        </div>
        <div class="p-6 bg-white rounded-lg shadow-strong border">
          <h4 class="text-heading text-base">Strong Shadow</h4>
          <p class="text-muted text-sm">shadow-strong</p>
        </div>
      </div>
    </section>

    <!-- グラスモーフィズムテスト -->
    <section class="spacing-content bg-sky-gradient p-8 rounded-2xl">
      <h2 class="text-white text-2xl mb-4 font-semibold">グラスモーフィズム効果</h2>
      <div class="grid-responsive">
        <div class="glass-effect p-6 rounded-xl text-white">
          <h4 class="font-semibold text-base mb-2">Glass Effect</h4>
          <p class="text-sm opacity-90">背景にぼかし効果</p>
        </div>
        <div class="glass-effect p-6 rounded-xl text-white">
          <h4 class="font-semibold text-base mb-2">Weather Card</h4>
          <div class="flex-center gap-2">
            <span class="text-2xl">☀️</span>
            <span>25°C</span>
          </div>
        </div>
        <div class="glass-effect p-6 rounded-xl text-white">
          <h4 class="font-semibold text-base mb-2">Transparent Card</h4>
          <p class="text-sm opacity-90">半透明背景</p>
        </div>
      </div>
    </section>

    <!-- ダークモードテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">ダークモード対応</h2>
      <div class="card p-6">
        <p class="text-body mb-4">
          このコンポーネントは自動的にダークモードに対応します。
          HTMLに <code class="font-mono bg-secondary-100 dark:bg-secondary-800 px-2 py-1 rounded text-sm">.dark</code> 
          クラスを追加することで切り替わります。
        </p>
        <button 
          @click="toggleDarkMode" 
          class="btn-outline flex-center gap-2"
        >
          <span>{{ isDark ? '☀️' : '🌙' }}</span>
          {{ isDark ? 'ライトモード' : 'ダークモード' }}
        </button>
      </div>
    </section>

    <!-- フォームテスト -->
    <section class="spacing-content">
      <h2 class="text-subheading text-2xl mb-4">フォームコンポーネント</h2>
      <div class="card p-6 max-w-md">
        <div class="spacing-comfortable">
          <div>
            <label class="text-body font-medium mb-2 block">入力フィールド</label>
            <input 
              type="text" 
              placeholder="テキストを入力..." 
              class="form-input"
            >
          </div>
          
          <div>
            <label class="text-body font-medium mb-2 block">セレクト</label>
            <select class="form-select">
              <option>オプション 1</option>
              <option>オプション 2</option>
              <option>オプション 3</option>
            </select>
          </div>
          
          <button class="btn-primary w-full">
            送信
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

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