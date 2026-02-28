interface WelcomeStateProps {
  onUpload: () => void;
  onDemo: () => void;
}

export function WelcomeState({ onUpload, onDemo }: WelcomeStateProps) {
  return (
    <div className="welcome">
      <h2>AgencyFlow</h2>
      <p>
        Multi-agent AI platform that automates campaign workflows.
        Upload a brief and watch 5 agents transform it into a complete strategy.
      </p>
      <div className="welcome-actions">
        <button className="btn btn-primary" onClick={onUpload}>
          Upload Brief
        </button>
        <button className="btn btn-outline" onClick={onDemo}>
          Try Demo
        </button>
      </div>
    </div>
  );
}
