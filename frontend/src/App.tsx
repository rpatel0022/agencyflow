import { useCallback, useState } from 'react';
import { WelcomeState } from './components/WelcomeState';
import { BriefUpload } from './components/BriefUpload';
import { PipelineProgress } from './components/PipelineProgress';
import { Dashboard } from './components/Dashboard';
import { DemoToggle } from './components/DemoToggle';
import { usePipeline } from './hooks/usePipeline';
import { startPipeline, startPipelineWithFile, fetchDemo } from './hooks/useApi';
import type { AgentName } from './types/pipeline';

type AppView = 'welcome' | 'upload' | 'running';

function App() {
  const [view, setView] = useState<AppView>('welcome');
  const [isDemo, setIsDemo] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentName | null>(null);

  const pipeline = usePipeline();

  const handleStartUpload = useCallback(() => {
    setView('upload');
  }, []);

  const handleDemo = useCallback(async () => {
    setIsLoading(true);
    try {
      const result = await fetchDemo();
      pipeline.setDemoOutputs(result.outputs);
      setIsDemo(true);
      setView('running');
      setSelectedAgent(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Demo failed');
    } finally {
      setIsLoading(false);
    }
  }, [pipeline]);

  const handleSubmitText = useCallback(async (text: string) => {
    setIsLoading(true);
    try {
      const result = await startPipeline(text);
      pipeline.connectSSE(result.run_id);
      setIsDemo(false);
      setView('running');
      setSelectedAgent(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to start pipeline');
    } finally {
      setIsLoading(false);
    }
  }, [pipeline]);

  const handleSubmitFile = useCallback(async (file: File) => {
    setIsLoading(true);
    try {
      const result = await startPipelineWithFile(file);
      pipeline.connectSSE(result.run_id);
      setIsDemo(false);
      setView('running');
      setSelectedAgent(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to start pipeline');
    } finally {
      setIsLoading(false);
    }
  }, [pipeline]);

  const handleCancel = useCallback(() => {
    setView('welcome');
  }, []);

  const handleReset = useCallback(() => {
    pipeline.reset();
    setView('welcome');
    setSelectedAgent(null);
    setIsDemo(false);
  }, [pipeline]);

  const handleToggleDemo = useCallback(() => {
    if (!isDemo) {
      handleDemo();
    } else {
      handleReset();
    }
  }, [isDemo, handleDemo, handleReset]);

  return (
    <div className="app">
      <header className="app-header">
        <h1
          onClick={handleReset}
          style={{ cursor: 'pointer' }}
        >
          AgencyFlow
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {view === 'running' && (
            <button className="btn btn-outline" onClick={handleReset} style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }}>
              New Run
            </button>
          )}
          <DemoToggle isDemo={isDemo} onToggle={handleToggleDemo} />
        </div>
      </header>

      {view === 'welcome' && (
        <div className="app-main">
          <div className="content">
            <WelcomeState onUpload={handleStartUpload} onDemo={handleDemo} />
          </div>
        </div>
      )}

      {view === 'upload' && (
        <div className="app-main">
          <div className="content">
            <BriefUpload
              onSubmitText={handleSubmitText}
              onSubmitFile={handleSubmitFile}
              onCancel={handleCancel}
              isLoading={isLoading}
            />
          </div>
        </div>
      )}

      {view === 'running' && (
        <div className="app-main">
          <div className="sidebar">
            <PipelineProgress
              steps={pipeline.steps}
              selectedAgent={selectedAgent}
              onSelectAgent={setSelectedAgent}
            />
          </div>
          <div className="content">
            <Dashboard
              selectedAgent={selectedAgent}
              outputs={pipeline.outputs}
              error={pipeline.error}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
