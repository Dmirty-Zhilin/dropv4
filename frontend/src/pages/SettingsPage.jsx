import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { getSettings, updateSettings } from '../lib/enhanced-api-client'
import { Settings, Key, Brain, Database, Clock } from 'lucide-react'

const SettingsPage = () => {
  const [settings, setSettings] = React.useState({})
  const [saving, setSaving] = React.useState(false)
  
  const queryClient = useQueryClient()
  
  const { data: settingsData, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: getSettings,
    onSuccess: (data) => {
      setSettings(data)
    }
  })
  
  const updateMutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries(['settings'])
      setSaving(false)
    }
  })
  
  const handleInputChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }))
  }
  
  const handleSave = async () => {
    setSaving(true)
    try {
      await updateMutation.mutateAsync(settings)
    } catch (error) {
      console.error('Failed to save settings:', error)
      setSaving(false)
    }
  }
  
  const availableModels = [
    { value: 'openai/gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'openai/gpt-4', label: 'GPT-4' },
    { value: 'openai/gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'anthropic/claude-3-haiku', label: 'Claude 3 Haiku' },
    { value: 'anthropic/claude-3-sonnet', label: 'Claude 3 Sonnet' },
    { value: 'anthropic/claude-3-opus', label: 'Claude 3 Opus' },
    { value: 'meta-llama/llama-3-8b-instruct', label: 'Llama 3 8B' },
    { value: 'meta-llama/llama-3-70b-instruct', label: 'Llama 3 70B' },
    { value: 'google/gemini-pro', label: 'Gemini Pro' },
    { value: 'mistralai/mixtral-8x7b-instruct', label: 'Mixtral 8x7B' }
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Загрузка настроек...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Настройки</h1>
          <p className="text-gray-600 mt-1">Конфигурация системы и LLM анализа</p>
        </div>
        
        <Button 
          onClick={handleSave}
          disabled={saving || updateMutation.isLoading}
        >
          {saving ? 'Сохранение...' : 'Сохранить настройки'}
        </Button>
      </div>

      {/* OpenRouter API Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            OpenRouter API
          </CardTitle>
          <CardDescription>
            Настройки для интеграции с OpenRouter API
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                API Ключ
              </label>
              <Input
                type="password"
                value={settings.openrouter_api_key || ''}
                onChange={(e) => handleInputChange('openrouter_api_key', e.target.value)}
                placeholder="Введите ваш OpenRouter API ключ"
              />
              <p className="text-sm text-gray-600 mt-1">
                Получите ключ на <a href="https://openrouter.ai" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">openrouter.ai</a>
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Модель по умолчанию
              </label>
              <Select 
                value={settings.openrouter_model || 'openai/gpt-3.5-turbo'}
                onValueChange={(value) => handleInputChange('openrouter_model', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((model) => (
                    <SelectItem key={model.value} value={model.value}>
                      {model.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* LLM Analysis Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            LLM Анализ
          </CardTitle>
          <CardDescription>
            Настройка промптов и параметров для анализа доменов
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Промпт для анализа доменов
              </label>
              <Textarea
                value={settings.analysis_prompt || 'Analyze the following domain data and provide insights about its quality, potential, and recommendations for use.'}
                onChange={(e) => handleInputChange('analysis_prompt', e.target.value)}
                rows={6}
                placeholder="Введите промпт для LLM анализа доменов..."
              />
              <p className="text-sm text-gray-600 mt-1">
                Этот промпт будет использоваться для анализа доменов через LLM
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Системные настройки
          </CardTitle>
          <CardDescription>
            Общие настройки системы и ограничения
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Максимальное количество доменов в пакете
              </label>
              <Input
                type="number"
                value={settings.max_domains_per_batch || '1000'}
                onChange={(e) => handleInputChange('max_domains_per_batch', e.target.value)}
                min="1"
                max="1000"
              />
              <p className="text-sm text-gray-600 mt-1">
                Максимальное количество доменов для пакетного анализа (до 1000)
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Время хранения отчетов (дни)
              </label>
              <Input
                type="number"
                value={settings.reports_retention_days || '30'}
                onChange={(e) => handleInputChange('reports_retention_days', e.target.value)}
                min="1"
                max="365"
              />
              <p className="text-sm text-gray-600 mt-1">
                Отчеты старше указанного количества дней будут автоматически удалены
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">
                Максимальное количество отчетов на пользователя
              </label>
              <Input
                type="number"
                value={settings.max_reports_per_user || '100'}
                onChange={(e) => handleInputChange('max_reports_per_user', e.target.value)}
                min="10"
                max="1000"
              />
              <p className="text-sm text-gray-600 mt-1">
                Максимальное количество отчетов, которые может сохранить один пользователь
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Settings Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Обзор текущих настроек
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-medium">OpenRouter</h4>
              <p className="text-sm text-gray-600">
                API ключ: {settings.openrouter_api_key ? '••••••••' : 'Не настроен'}
              </p>
              <p className="text-sm text-gray-600">
                Модель: {settings.openrouter_model || 'openai/gpt-3.5-turbo'}
              </p>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium">Ограничения</h4>
              <p className="text-sm text-gray-600">
                Доменов в пакете: {settings.max_domains_per_batch || '1000'}
              </p>
              <p className="text-sm text-gray-600">
                Хранение отчетов: {settings.reports_retention_days || '30'} дней
              </p>
              <p className="text-sm text-gray-600">
                Отчетов на пользователя: {settings.max_reports_per_user || '100'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default SettingsPage

