export default defineNuxtPlugin(async () => {
  // 最小限のセットアップのみ
  const { $pinia } = useNuxtApp()
  
  // persistedstateプラグイン追加
  if (process.client) {
    const piniaPluginPersistedstate = await import('pinia-plugin-persistedstate')
    $pinia.use(piniaPluginPersistedstate.default)
  }
})