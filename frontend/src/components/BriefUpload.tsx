import { useCallback, useRef, useState } from 'react';

interface BriefUploadProps {
  onSubmitText: (text: string) => void;
  onSubmitFile: (file: File) => void;
  onCancel: () => void;
  isLoading: boolean;
}

export function BriefUpload({ onSubmitText, onSubmitFile, onCancel, isLoading }: BriefUploadProps) {
  const [text, setText] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) onSubmitFile(file);
    },
    [onSubmitFile]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onSubmitFile(file);
    },
    [onSubmitFile]
  );

  return (
    <div className="upload-section">
      <h3>Upload Campaign Brief</h3>

      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <p>Drop PDF or TXT file here</p>
        <span>or click to browse — max 10MB</span>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </div>

      <div className="divider">or paste text</div>

      <textarea
        className="text-area"
        placeholder="Paste your campaign brief here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      <div className="upload-actions">
        <button className="btn btn-outline" onClick={onCancel} disabled={isLoading}>
          Back
        </button>
        <button
          className="btn btn-primary"
          onClick={() => onSubmitText(text)}
          disabled={isLoading || text.trim().length < 10}
        >
          {isLoading ? 'Starting...' : 'Run Pipeline'}
        </button>
      </div>
    </div>
  );
}
