<template>
  <div class="container-main spacing-section">
    <!-- ヘッダー -->
    <div class="text-center mb-8">
      <h1 class="text-heading text-4xl animate-fade-in">
        UIコンポーネントテスト - Phase 1-4-2
      </h1>
      <p class="text-body-sm text-muted mt-2">
        統一デザインシステム基礎コンポーネントの動作確認
      </p>
    </div>

    <!-- ボタンコンポーネントテスト -->
    <Card title="Button Components" class="mb-8">
      <template #headerActions>
        <Button size="sm" variant="ghost" @click="refreshButtonTests">
          🔄 リフレッシュ
        </Button>
      </template>
      
      <div class="space-y-6">
        <!-- バリアントテスト -->
        <div>
          <h4 class="text-subheading text-base mb-3">バリアント</h4>
          <div class="flex flex-wrap gap-3">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="danger">Danger</Button>
          </div>
        </div>
        
        <!-- サイズテスト -->
        <div>
          <h4 class="text-subheading text-base mb-3">サイズ</h4>
          <div class="flex flex-wrap items-center gap-3">
            <Button size="xs">Extra Small</Button>
            <Button size="sm">Small</Button>
            <Button size="md">Medium</Button>
            <Button size="lg">Large</Button>
            <Button size="xl">Extra Large</Button>
          </div>
        </div>
        
        <!-- 状態テスト -->
        <div>
          <h4 class="text-subheading text-base mb-3">状態</h4>
          <div class="flex flex-wrap gap-3">
            <Button icon-left="🚀" variant="primary">With Icon</Button>
            <Button :loading="buttonLoading" variant="primary" @click="toggleLoading">
              {{ buttonLoading ? 'Loading...' : 'Click to Load' }}
            </Button>
            <Button :disabled="true" variant="primary">Disabled</Button>
            <Button full-width variant="outline" class="max-w-md">Full Width</Button>
          </div>
        </div>
      </div>
    </Card>

    <!-- カードコンポーネントテスト -->
    <Card title="Card Components" class="mb-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- デフォルトカード -->
        <Card variant="default" title="Default Card">
          <p class="text-body">
            これはデフォルトカードです。基本的なシャドウとボーダーが設定されています。
          </p>
          <template #footer>
            <Button size="sm" variant="outline" full-width>アクション</Button>
          </template>
        </Card>
        
        <!-- アウトラインカード -->
        <Card variant="outlined" title="Outlined Card">
          <p class="text-body">
            これはアウトラインカードです。太いボーダーが特徴です。
          </p>
          <template #footer>
            <div class="flex gap-2">
              <Button size="sm" variant="primary">OK</Button>
              <Button size="sm" variant="ghost">Cancel</Button>
            </div>
          </template>
        </Card>
        
        <!-- エレベートカード -->
        <Card variant="elevated" title="Elevated Card" :hoverable="true">
          <p class="text-body">
            これは立体的なカードです。ホバー効果付きです。
          </p>
          <template #headerActions>
            <Button size="xs" variant="ghost">⚙️</Button>
          </template>
        </Card>

        <!-- グラスカード -->
        <Card variant="glass" title="Glass Effect Card" class="bg-weather-gradient-sunny">
          <p class="text-white">
            グラスモーフィズム効果のカードです。背景が透けて見えます。
          </p>
        </Card>

        <!-- クリッカブルカード -->
        <Card 
          variant="default" 
          title="Clickable Card" 
          :clickable="true"
          :hoverable="true"
          @click="handleCardClick"
        >
          <p class="text-body">
            このカードはクリック可能です。試してみてください。
          </p>
        </Card>

        <!-- カスタムパディング -->
        <Card variant="outlined" padding="lg" title="Large Padding">
          <p class="text-body">
            大きなパディングが設定されたカードです。
          </p>
        </Card>
      </div>
    </Card>

    <!-- インプットコンポーネントテスト -->
    <Card title="Input Components" class="mb-8">
      <div class="space-y-6 max-w-2xl">
        <!-- 基本入力 -->
        <div>
          <h4 class="text-subheading text-base mb-3">基本入力フィールド</h4>
          <div class="space-y-4">
            <Input 
              v-model="testInput1"
              label="基本入力フィールド"
              placeholder="テキストを入力..."
              help-text="これはヘルプテキストです。"
            />
            
            <Input 
              v-model="testInput2"
              label="メールアドレス"
              type="email"
              placeholder="example@domain.com"
              icon-left="📧"
              :clearable="true"
            />
            
            <Input 
              v-model="testInput3"
              label="パスワード"
              type="password"
              placeholder="パスワードを入力"
              icon-left="🔒"
              :required="true"
            />
          </div>
        </div>

        <!-- サイズバリエーション -->
        <div>
          <h4 class="text-subheading text-base mb-3">サイズバリエーション</h4>
          <div class="space-y-3">
            <Input 
              v-model="testInput4"
              size="sm"
              placeholder="Small size"
              label="Small Input"
            />
            <Input 
              v-model="testInput5"
              size="md"
              placeholder="Medium size (default)"
              label="Medium Input"
            />
            <Input 
              v-model="testInput6"
              size="lg"
              placeholder="Large size"
              label="Large Input"
            />
          </div>
        </div>

        <!-- バリアント -->
        <div>
          <h4 class="text-subheading text-base mb-3">スタイルバリアント</h4>
          <div class="space-y-3">
            <Input 
              v-model="testInput7"
              variant="default"
              placeholder="Default variant"
              label="Default Style"
            />
            <Input 
              v-model="testInput8"
              variant="outlined"
              placeholder="Outlined variant"
              label="Outlined Style"
            />
            <Input 
              v-model="testInput9"
              variant="filled"
              placeholder="Filled variant"
              label="Filled Style"
            />
          </div>
        </div>

        <!-- エラー状態 -->
        <div>
          <h4 class="text-subheading text-base mb-3">エラー状態</h4>
          <Input 
            v-model="testInputError"
            label="エラー状態の入力フィールド"
            placeholder="入力してください"
            error-message="この項目は必須です。正しい形式で入力してください。"
            :required="true"
          />
        </div>

        <!-- 無効状態 -->
        <div>
          <h4 class="text-subheading text-base mb-3">無効・読み取り専用状態</h4>
          <div class="space-y-3">
            <Input 
              model-value="無効状態のフィールド"
              label="無効状態"
              :disabled="true"
            />
            <Input 
              model-value="読み取り専用フィールド"
              label="読み取り専用"
              :readonly="true"
            />
          </div>
        </div>
      </div>
    </Card>

    <!-- ローディングコンポーネントテスト -->
    <Card title="Loading Components" class="mb-8">
      <div class="space-y-8">
        <!-- タイプ別テスト -->
        <div>
          <h4 class="text-subheading text-base mb-3">ローディングタイプ</h4>
          <div class="flex flex-wrap gap-8 items-center">
            <div class="text-center space-y-2">
              <Loading type="spinner" size="md" />
              <p class="text-xs text-muted">Spinner</p>
            </div>
            <div class="text-center space-y-2">
              <Loading type="dots" size="md" />
              <p class="text-xs text-muted">Dots</p>
            </div>
            <div class="text-center space-y-2">
              <Loading type="pulse" size="md" />
              <p class="text-xs text-muted">Pulse</p>
            </div>
            <div class="text-center space-y-2">
              <Loading type="skeleton" size="md" class="w-20" />
              <p class="text-xs text-muted">Skeleton</p>
            </div>
          </div>
        </div>

        <!-- サイズテスト -->
        <div>
          <h4 class="text-subheading text-base mb-3">サイズバリエーション</h4>
          <div class="flex flex-wrap gap-4 items-center">
            <Loading type="spinner" size="xs" />
            <Loading type="spinner" size="sm" />
            <Loading type="spinner" size="md" />
            <Loading type="spinner" size="lg" />
            <Loading type="spinner" size="xl" />
          </div>
        </div>

        <!-- カラーテスト -->
        <div>
          <h4 class="text-subheading text-base mb-3">カラーバリエーション</h4>
          <div class="flex flex-wrap gap-4 items-center">
            <Loading type="spinner" color="primary" size="md" />
            <Loading type="spinner" color="secondary" size="md" />
            <div class="bg-secondary-800 p-3 rounded">
              <Loading type="spinner" color="white" size="md" />
            </div>
          </div>
        </div>

        <!-- テキスト付きローディング -->
        <div>
          <h4 class="text-subheading text-base mb-3">テキスト付きローディング</h4>
          <div class="space-y-4">
            <Loading 
              type="spinner" 
              :show-text="true" 
              text="データを読み込み中..."
              :center="true"
            />
            
            <Loading 
              type="dots" 
              :show-text="true" 
              text="処理中です..."
              :center="true"
            />
          </div>
        </div>

        <!-- インラインローディング -->
        <div>
          <h4 class="text-subheading text-base mb-3">インラインローディング</h4>
          <div class="space-y-3">
            <div class="flex items-center gap-2">
              <Loading type="spinner" size="sm" />
              <span class="text-body">処理中...</span>
            </div>
            
            <Button :loading="inlineLoading" @click="toggleInlineLoading">
              {{ inlineLoading ? 'ローディング中' : 'ローディング開始' }}
            </Button>
          </div>
        </div>
      </div>
    </Card>

    <!-- 統合テスト -->
    <Card title="統合テスト - 天気アプリ風デモ" variant="elevated" class="mb-8">
      <div class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 設定パネル -->
          <div class="space-y-4">
            <h4 class="text-subheading text-lg">設定</h4>
            
            <Input 
              v-model="demoLocation"
              label="地点名"
              placeholder="地点を入力..."
              icon-left="📍"
              :clearable="true"
            />
            
            <div class="flex gap-2">
              <Button 
                variant="primary" 
                :loading="demoLoading" 
                @click="startDemo"
                :disabled="!demoLocation"
              >
                🌤️ 天気を取得
              </Button>
              <Button variant="outline" @click="resetDemo">
                リセット
              </Button>
            </div>
          </div>

          <!-- 結果パネル -->
          <Card variant="glass" class="bg-weather-gradient-sunny">
            <h4 class="text-white font-semibold mb-3">天気情報</h4>
            
            <div v-if="demoLoading" class="text-center py-8">
              <Loading 
                type="spinner" 
                color="white" 
                :show-text="true" 
                text="天気データを取得中..."
                :center="true"
              />
            </div>
            
            <div v-else-if="demoResult" class="text-white space-y-2">
              <p><strong>地点:</strong> {{ demoResult.location }}</p>
              <p><strong>天気:</strong> {{ demoResult.weather }}</p>
              <p><strong>気温:</strong> {{ demoResult.temperature }}°C</p>
              <p><strong>コメント:</strong> {{ demoResult.comment }}</p>
            </div>
            
            <div v-else class="text-white/70 text-center py-8">
              地点を選択して「天気を取得」ボタンを押してください
            </div>
          </Card>
        </div>
      </div>
    </Card>

    <!-- アクセシビリティチェック -->
    <Card title="アクセシビリティチェック" variant="outlined" class="mb-8">
      <div class="space-y-4">
        <div class="alert-blue">
          <h4 class="font-semibold mb-2">✅ 実装済みアクセシビリティ機能</h4>
          <ul class="text-sm space-y-1 list-disc list-inside">
            <li>適切なARIA属性（aria-label, aria-describedby, aria-invalid など）</li>
            <li>キーボードナビゲーション対応</li>
            <li>フォーカス可視化（focus-visible）</li>
            <li>スクリーンリーダー対応（role属性、sr-only クラス）</li>
            <li>適切なセマンティックHTML要素</li>
            <li>色に依存しない情報伝達</li>
          </ul>
        </div>
        
        <div class="flex gap-2">
          <Button size="sm" variant="outline" @click="testKeyboardNavigation">
            ⌨️ キーボードナビゲーションテスト
          </Button>
          <Button size="sm" variant="outline" @click="testScreenReader">
            🔊 スクリーンリーダーテスト
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({
  title: 'UI Components Test - Phase 1-4-2'
})

// リアクティブデータ
const buttonLoading = ref(false)
const inlineLoading = ref(false)

// 入力フィールドのテストデータ
const testInput1 = ref('')
const testInput2 = ref('')
const testInput3 = ref('')
const testInput4 = ref('')
const testInput5 = ref('')
const testInput6 = ref('')
const testInput7 = ref('')
const testInput8 = ref('')
const testInput9 = ref('')
const testInputError = ref('')

// デモ用データ
const demoLocation = ref('')
const demoLoading = ref(false)
const demoResult = ref<{
  location: string
  weather: string
  temperature: number
  comment: string
} | null>(null)

// イベントハンドラー
const refreshButtonTests = () => {
  console.log('Button tests refreshed')
}

const toggleLoading = () => {
  buttonLoading.value = true
  setTimeout(() => {
    buttonLoading.value = false
  }, 2000)
}

const toggleInlineLoading = () => {
  inlineLoading.value = true
  setTimeout(() => {
    inlineLoading.value = false
  }, 1500)
}

const handleCardClick = () => {
  alert('カードがクリックされました！')
}

const startDemo = () => {
  if (!demoLocation.value) return
  
  demoLoading.value = true
  demoResult.value = null
  
  // 模擬API呼び出し
  setTimeout(() => {
    demoResult.value = {
      location: demoLocation.value,
      weather: '晴れ',
      temperature: 25,
      comment: '今日は良い天気ですね！外出日和です。'
    }
    demoLoading.value = false
  }, 2000)
}

const resetDemo = () => {
  demoLocation.value = ''
  demoResult.value = null
  demoLoading.value = false
}

const testKeyboardNavigation = () => {
  alert('Tabキーでフォーカス移動、Enterキーで選択、Escapeキーでキャンセルを試してください。')
}

const testScreenReader = () => {
  alert('スクリーンリーダーでaria-label、role属性、ヘルプテキストが適切に読み上げられるか確認してください。')
}
</script>