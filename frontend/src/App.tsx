import React, { useState, useEffect, useCallback } from 'react';
import apiService from './api';
import { TaskStatus, ProjectRequest, ApiConfig } from './types';
import Settings from './components/Settings';
import './App.css';

function App() {
  const [projectDescription, setProjectDescription] = useState('');
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null);
  const [tasks, setTasks] = useState<TaskStatus[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [apiConfig, setApiConfig] = useState<ApiConfig | null>(null);

  const loadTasks = useCallback(async () => {
    try {
      const taskList = await apiService.listTasks();
      setTasks(taskList);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    }
  }, []);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // 로컬 스토리지에서 API 설정 로드
  useEffect(() => {
    const savedConfig = localStorage.getItem('apiConfig');
    if (savedConfig) {
      try {
        const config: ApiConfig = JSON.parse(savedConfig);
        setApiConfig(config);
      } catch (e) {
        console.error('Failed to load API config:', e);
      }
    } else {
      // 설정이 없으면 설정 페이지로 이동
      setShowSettings(true);
    }
  }, []);

  // Polling for current task status
  useEffect(() => {
    if (!currentTask || currentTask.status === 'completed' || currentTask.status === 'failed') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const status = await apiService.getTaskStatus(currentTask.task_id);
        setCurrentTask(status);
        
        if (status.status === 'completed' || status.status === 'failed') {
          loadTasks();
        }
      } catch (err) {
        console.error('Failed to get task status:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [currentTask, loadTasks]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!projectDescription.trim()) {
      setError('프로젝트 설명을 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: ProjectRequest = {
        project_overview: projectDescription,
      };
      
      const task = await apiService.executeProject(request);
      setCurrentTask(task);
      setProjectDescription('');
    } catch (err) {
      setError('프로젝트 실행에 실패했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#4caf50';
      case 'failed': return '#f44336';
      case 'running': return '#2196f3';
      default: return '#9e9e9e';
    }
  };

  const getProgressPercentage = (task: TaskStatus) => {
    return task.progress;
  };

  const handleSettingsSave = (config: ApiConfig) => {
    setApiConfig(config);
    setShowSettings(false);
  };

  // 설정 페이지가 표시될 때
  if (showSettings) {
    return (
      <div className="app">
        <header className="header">
          <h1>🤖 AI Agent Team</h1>
          <p>AI 기반 소프트웨어 개발 자동화 시스템</p>
        </header>
        <main className="main">
          <Settings onSave={handleSettingsSave} />
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div>
            <h1>🤖 AI Agent Team</h1>
            <p>AI 기반 소프트웨어 개발 자동화 시스템</p>
          </div>
          <button
            className="settings-btn"
            onClick={() => setShowSettings(true)}
            title="API 설정"
          >
            ⚙️
          </button>
        </div>
        {apiConfig && (
          <div className="api-status">
            <span className="status-dot"></span>
            {apiConfig.providerType === 'preset' ? apiConfig.provider : apiConfig.customName} 연결됨
          </div>
        )}
      </header>

      <main className="main">
        <section className="input-section">
          <h2>새 프로젝트 시작</h2>
          <form onSubmit={handleSubmit} className="project-form">
            <textarea
              className="project-input"
              placeholder="만들고 싶은 소프트웨어를 설명해주세요...&#10;예: Python으로 REST API 서버를 만들어줘. 사용자는 회원가입하고 게시물을 작성할 수 있어야 해."
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="submit-btn"
              disabled={isLoading || !projectDescription.trim()}
            >
              {isLoading ? '실행 중...' : '🚀 프로젝트 시작'}
            </button>
          </form>
          {error && <div className="error-message">{error}</div>}
        </section>

        {currentTask && currentTask.status !== 'completed' && currentTask.status !== 'failed' && (
          <section className="current-task">
            <h2>현재 진행 상황</h2>
            <div className="task-card">
              <div className="task-header">
                <span 
                  className="status-badge"
                  style={{ backgroundColor: getStatusColor(currentTask.status) }}
                >
                  {currentTask.status === 'pending' && '대기중'}
                  {currentTask.status === 'running' && '실행중'}
                </span>
                <span className="task-id">Task ID: {currentTask.task_id.slice(0, 8)}...</span>
              </div>
              
              <div className="progress-bar">
                <div 
                  className="progress-fill"
                  style={{ width: `${getProgressPercentage(currentTask)}%` }}
                />
              </div>
              
              <p className="stage-info">
                {currentTask.current_stage === 'planning' && '📋 프로젝트 계획 수립 중...'}
                {currentTask.current_stage === 'initializing' && '⚙️ 초기화 중...'}
                {!currentTask.current_stage && '대기중...'}
              </p>
            </div>
          </section>
        )}

        {currentTask?.result && (
          <section className="results-section">
            <h2>📊 결과</h2>
            
            {currentTask.result.success ? (
              <>
                <div className="success-banner">
                  ✅ 프로젝트가 성공적으로 완료되었습니다!
                </div>
                
                {currentTask.result.project_plan && (
                  <div className="result-card">
                    <h3>📋 프로젝트 계획</h3>
                    <p><strong>프로젝트명:</strong> {currentTask.result.project_plan.project_name}</p>
                    <p><strong>설명:</strong> {currentTask.result.project_plan.description}</p>
                    <p><strong>기술 스택:</strong> {currentTask.result.project_plan.tech_stack.join(', ')}</p>
                    <p><strong>요구사항:</strong> {currentTask.result.project_plan.requirements.length}개</p>
                  </div>
                )}

                {currentTask.result.generated_code && (
                  <div className="result-card">
                    <h3>💻 생성된 코드</h3>
                    <p>생성된 파일 수: {currentTask.result.generated_code.files.length}개</p>
                    <ul className="file-list">
                      {currentTask.result.generated_code.files.map((file, idx) => (
                        <li key={idx}>
                          <span className="file-path">{file.path}</span>
                          <span className="file-lang">{file.language}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {currentTask.result.evaluation && (
                  <div className="result-card">
                    <h3>📈 코드 평가</h3>
                    <p><strong>품질 수준:</strong> {currentTask.result.evaluation.quality_level}</p>
                    <p><strong>점수:</strong> {currentTask.result.evaluation.score}/100</p>
                    <p><strong>요약:</strong> {currentTask.result.evaluation.summary}</p>
                    
                    {currentTask.result.evaluation.issues.length > 0 && (
                      <div className="issues">
                        <h4>발견된 문제점:</h4>
                        <ul>
                          {currentTask.result.evaluation.issues.map((issue, idx) => (
                            <li key={idx} className={`issue-${issue.severity}`}>
                              [{issue.severity.toUpperCase()}] {issue.message}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {currentTask.result.evaluation.suggestions.length > 0 && (
                      <div className="suggestions">
                        <h4>권장 사항:</h4>
                        <ul>
                          {currentTask.result.evaluation.suggestions.map((suggestion, idx) => (
                            <li key={idx}>{suggestion}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <p className="iterations">반복 횟수: {currentTask.result.iterations}</p>
              </>
            ) : (
              <div className="error-banner">
                ❌ 프로젝트 실행에 실패했습니다.
                {currentTask.result.error && <p>오류: {currentTask.result.error}</p>}
              </div>
            )}
          </section>
        )}

        <section className="history-section">
          <h2>📜 실행 기록</h2>
          {tasks.length === 0 ? (
            <p className="no-tasks">아직 실행된 프로젝트가 없습니다.</p>
          ) : (
            <div className="task-list">
              {tasks.map((task) => (
                <div 
                  key={task.task_id} 
                  className="history-item"
                  onClick={() => setCurrentTask(task)}
                >
                  <span 
                    className="status-dot"
                    style={{ backgroundColor: getStatusColor(task.status) }}
                  />
                  <span className="history-id">Task {task.task_id.slice(0, 8)}</span>
                  <span className="history-status">
                    {task.status === 'completed' && '완료'}
                    {task.status === 'failed' && '실패'}
                    {task.status === 'running' && '진행중'}
                    {task.status === 'pending' && '대기'}
                  </span>
                  <span className="history-progress">{task.progress}%</span>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        <p>AI Agent Team © 2024 | Powered by AI</p>
      </footer>
    </div>
  );
}

export default App;
