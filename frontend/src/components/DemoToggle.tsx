interface DemoToggleProps {
  isDemo: boolean;
  onToggle: () => void;
}

export function DemoToggle({ isDemo, onToggle }: DemoToggleProps) {
  return (
    <div className="demo-toggle">
      <span>Live</span>
      <div
        className={`toggle-pill ${isDemo ? 'active' : ''}`}
        onClick={onToggle}
      />
      <span>Demo</span>
    </div>
  );
}
