// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },
  
  // UI Framework
  modules: ['@nuxt/ui'],
  
  // TypeScript設定
  typescript: {
    strict: true,
    shim: false
  },

  // ランタイム設定
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    }
  },

  // 開発サーバープロキシ設定
  nitro: {
    devProxy: {
      '/api': {
        target: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },

  // Vueコンパイラオプション
  vue: {
    compilerOptions: {
      isCustomElement: (tag) => tag === 'lang' // LangGraphタグを許可
    }
  }
})
