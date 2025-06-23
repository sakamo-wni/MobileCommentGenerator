import { defineStore } from 'pinia'
import { watch } from 'vue'

interface Provider {
  label: string
  value: string
}

export const useSettingsStore = defineStore('settings', () => {
  // State
  const selectedProvider = ref<Provider>({ label: 'Google Gemini', value: 'gemini' })
  const providers = ref<Provider[]>([
    { label: 'Google Gemini', value: 'gemini' },
    { label: 'Claude 3.5 Sonnet', value: 'claude' },
    { label: 'OpenAI GPT-4', value: 'openai' },
    { label: 'Groq Llama 3', value: 'groq' }
  ])
  
  // Actions
  const setProvider = (provider: Provider) => {
    selectedProvider.value = provider
  }
  
  const getProviderByValue = (value: string): Provider | undefined => {
    return providers.value.find(p => p.value === value)
  }
  
  // $persist を使用して永続化設定
  // @ts-ignore
  if (process.client) {
    const savedProvider = localStorage.getItem('selected-provider')
    if (savedProvider) {
      selectedProvider.value = JSON.parse(savedProvider)
    }
    
    watch(selectedProvider, (newProvider) => {
      localStorage.setItem('selected-provider', JSON.stringify(newProvider))
    }, { deep: true })
  }
  
  return {
    // State
    selectedProvider,
    providers: readonly(providers),
    
    // Actions
    setProvider,
    getProviderByValue
  }
})