// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },
  
  // UI Framework
  modules: [
    '@pinia/nuxt',
    '@unocss/nuxt',
    '@vueuse/nuxt', 
    '@nuxt/icon'
  ],
  css: ['@unocss/reset/tailwind.css'],

  components: [
    {
      path: '~/components',
      pathPrefix: false,
    }
  ],
  
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

  // Vite proxy configuration
  vite: {
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false
        }
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
