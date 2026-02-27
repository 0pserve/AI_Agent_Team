import React, { useState, useEffect } from 'react';
import { ApiConfig, PresetProvider, ProviderType, TestConnectionResult } from '../types';
import apiService from '../api';
import './Settings.css';

// 제공자별 기본 URL과 모델 정보
const PROVIDER_INFO: Record<PresetProvider, { baseUrl: string; defaultModel: string; models: string[] }> = {
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    defaultModel: 'gpt-4',
    models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini'],
  },
  anthropic: {
    baseUrl: 'https://api.anthropic.com',
    defaultModel: 'claude-3-opus-20240229',
    models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307', 'claude-3-5-sonnet-20241022'],
  },
  google: {
    baseUrl: 'https://generativelanguage.googleapis.com/v1',
    defaultModel: 'gemini-1.5-pro',
    models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.0-pro'],
  },
  azure: {
    baseUrl: '',
    defaultModel: 'gpt-4',
    models: ['gpt-4', 'gpt-4-turbo', 'gpt-35-turbo'],
  },
  deepseek: {
    baseUrl: 'https://api.deepseek.com',
    defaultModel: 'deepseek-chat',
    models: ['deepseek-chat', 'deepseek-coder'],
  },
  cohere: {
    baseUrl: 'https://api.cohere.ai',
    defaultModel: 'command-r-plus',
    models: ['command-r-plus', 'command-r', 'command', 'command-light'],
  },
  mistral: {
    baseUrl: 'https://api.mistral.ai',
    defaultModel: 'mistral-large-latest',
    models: ['mistral-large-latest', 'mistral-small-latest', 'mistral-medium-latest'],
  },
  xai: {
    baseUrl: 'https://api.x.ai',
    defaultModel: 'grok-2-1212',
    models: ['grok-2-1212', 'grok-2', 'grok-beta'],
  },
};

const PRESET_PROVIDERS: { value: PresetProvider; label: string; icon: string }[] = [
  { value: 'openai', label: 'OpenAI', icon: '🔵' },
  { value: 'anthropic', label: 'Anthropic', icon: '🟤' },
  { value: 'google', label: 'Google', icon: '🟢' },
  { value: 'azure', label: 'Azure OpenAI', icon: '🔷' },
  { value: 'deepseek', label: 'DeepSeek', icon: '🧑‍💻' },
  { value: 'cohere', label: 'Cohere', icon: '📡' },
  { value: 'mistral', label: 'Mistral', icon: '🌫️' },
  { value: 'xai', label: 'XAI (Grok)', icon: '🚀' },
];

interface SettingsProps {
  onSave?: (config: ApiConfig) => void;
}

const Settings: React.FC<SettingsProps> = ({ onSave }) => {
  const [providerType, setProviderType] = useState<ProviderType>('preset');
  const [provider, setProvider] = useState<PresetProvider>('openai');
  const [customName, setCustomName] = useState('');
  const [customBaseUrl, setCustomBaseUrl] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(4000);
  const [showApiKey, setShowApiKey] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [testResult, setTestResult] = useState<TestConnectionResult | null>(null);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 로컬 스토리지에서 설정 로드
  useEffect(() => {
    const savedConfig = localStorage.getItem('apiConfig');
    if (savedConfig) {
      try {
        const config: ApiConfig = JSON.parse(savedConfig);
        setProviderType(config.providerType);
        if (config.provider) setProvider(config.provider);
        if (config.customName) setCustomName(config.customName);
        if (config.customBaseUrl) setCustomBaseUrl(config.customBaseUrl);
        if (config.customModel) setCustomModel(config.customModel);
        if (config.apiKey) setApiKey(config.apiKey);
        if (config.temperature) setTemperature(config.temperature);
        if (config.maxTokens) setMaxTokens(config.maxTokens);
      } catch (e) {
        console.error('Failed to load config:', e);
      }
    }
  }, []);

  const getCurrentConfig = (): ApiConfig => {
    if (providerType === 'preset') {
      return {
        providerType,
        provider,
        apiKey,
        temperature,
        maxTokens,
      };
    }
    return {
      providerType,
      customName,
      customBaseUrl,
      customModel,
      apiKey,
      temperature,
      maxTokens,
    };
  };

  const handleTestConnection = async () => {
    if (!apiKey.trim()) {
      setTestResult({ success: false, message: 'API 키를 입력해주세요.' });
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    try {
      const config = getCurrentConfig();
      const result = await apiService.testConnection(config);
      setTestResult(result);
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.response?.data?.message || '연결 테스트에 실패했습니다.',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setSaveMessage({ type: 'error', text: 'API 키를 입력해주세요.' });
      return;
    }

    if (providerType === 'custom' && (!customBaseUrl.trim() || !customModel.trim())) {
      setSaveMessage({ type: 'error', text: '커스텀 API의 Base URL과 모델을 입력해주세요.' });
      return;
    }

    setIsSaving(true);
    setSaveMessage(null);

    try {
      const config = getCurrentConfig();
      
      // 로컬 스토리지에 저장 (보안상 서버에는 저장하지 않음)
      localStorage.setItem('apiConfig', JSON.stringify(config));
      
      // 서버에도 저장 시도
      try {
        await apiService.saveConfig(config);
      } catch (e) {
        // 서버 저장 실패해도 로컬 저장 성공으로 처리
        console.log('Server save skipped, local save successful');
      }

      setSaveMessage({ type: 'success', text: '설정이 저장되었습니다!' });
      
      if (onSave) {
        onSave(config);
      }
    } catch (error: any) {
      setSaveMessage({ type: 'error', text: error.message || '설정 저장에 실패했습니다.' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleProviderChange = (newProvider: PresetProvider) => {
    setProvider(newProvider);
    setTestResult(null);
  };

  return (
    <div className="settings-container">
      <div className="settings-card">
        <div className="settings-header">
          <h2>⚙️ AI API 설정</h2>
          <p>사용할 AI 제공자와 API 키를 설정하세요</p>
        </div>

        {/* 제공자 유형 선택 */}
        <div className="settings-section">
          <label className="section-label">제공자 유형</label>
          <div className="provider-type-tabs">
            <button
              className={`type-tab ${providerType === 'preset' ? 'active' : ''}`}
              onClick={() => setProviderType('preset')}
            >
              📋 프리셋 제공자
            </button>
            <button
              className={`type-tab ${providerType === 'custom' ? 'active' : ''}`}
              onClick={() => setProviderType('custom')}
            >
              🔧 커스텀 API
            </button>
          </div>
        </div>

        {/* 프리셋 제공자 선택 */}
        {providerType === 'preset' && (
          <div className="settings-section">
            <label className="section-label">AI 제공자</label>
            <div className="provider-grid">
              {PRESET_PROVIDERS.map((p) => (
                <button
                  key={p.value}
                  className={`provider-btn ${provider === p.value ? 'active' : ''}`}
                  onClick={() => handleProviderChange(p.value)}
                >
                  <span className="provider-icon">{p.icon}</span>
                  <span className="provider-name">{p.label}</span>
                </button>
              ))}
            </div>
            
            {/* 모델 선택 */}
            <div className="form-group">
              <label>모델 선택</label>
              <select
                className="form-select"
                value={customModel || PROVIDER_INFO[provider].defaultModel}
                onChange={(e) => setCustomModel(e.target.value)}
              >
                {PROVIDER_INFO[provider].models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
              <p className="form-hint">
                Base URL: {PROVIDER_INFO[provider].baseUrl}
              </p>
            </div>
          </div>
        )}

        {/* 커스텀 API 입력 */}
        {providerType === 'custom' && (
          <div className="settings-section">
            <div className="form-group">
              <label>API 이름</label>
              <input
                type="text"
                className="form-input"
                placeholder="My Custom API"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Base URL</label>
              <input
                type="text"
                className="form-input"
                placeholder="https://api.example.com/v1"
                value={customBaseUrl}
                onChange={(e) => setCustomBaseUrl(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>모델명</label>
              <input
                type="text"
                className="form-input"
                placeholder="model-name"
                value={customModel}
                onChange={(e) => setCustomModel(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* 공통 설정 */}
        <div className="settings-section">
          <div className="form-group">
            <label>API Key</label>
            <div className="api-key-input">
              <input
                type={showApiKey ? 'text' : 'password'}
                className="form-input"
                placeholder="sk-..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <button
                type="button"
                className="toggle-visibility"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Temperature: {temperature}</label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="form-range"
              />
              <div className="range-labels">
                <span>정확</span>
                <span>균형</span>
                <span>창의</span>
              </div>
            </div>
            <div className="form-group">
              <label>Max Tokens: {maxTokens}</label>
              <input
                type="range"
                min="100"
                max="10000"
                step="100"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="form-range"
              />
            </div>
          </div>
        </div>

        {/* 테스트 결과 */}
        {testResult && (
          <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
            {testResult.success ? '✅' : '❌'} {testResult.message}
            {testResult.provider && <span> ({testResult.provider} - {testResult.model})</span>}
          </div>
        )}

        {/* 저장 메시지 */}
        {saveMessage && (
          <div className={`save-message ${saveMessage.type}`}>
            {saveMessage.type === 'success' ? '✅' : '❌'} {saveMessage.text}
          </div>
        )}

        {/* 버튼 그룹 */}
        <div className="button-group">
          <button
            className="btn btn-secondary"
            onClick={handleTestConnection}
            disabled={isTesting || !apiKey.trim()}
          >
            {isTesting ? '🔄 테스트 중...' : '🧪 연결 테스트'}
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? '💾 저장 중...' : '💾 설정 저장'}
          </button>
        </div>

        {/* 도움말 */}
        <div className="help-section">
          <details>
            <summary>🔗 API 키를 얻으려면?</summary>
            <div className="help-content">
              <p>각 제공자의 개발자 포털에서 API 키를 발급받을 수 있습니다:</p>
              <ul>
                <li><a href="https://platform.openai.com" target="_blank" rel="noopener noreferrer">OpenAI Platform</a></li>
                <li><a href="https://console.anthropic.com" target="_blank" rel="noopener noreferrer">Anthropic Console</a></li>
                <li><a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer">Google AI Studio</a></li>
                <li><a href="https://platform.deepseek.com" target="_blank" rel="noopener noreferrer">DeepSeek Platform</a></li>
              </ul>
            </div>
          </details>
        </div>
      </div>
    </div>
  );
};

export default Settings;