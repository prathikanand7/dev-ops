import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useDropzone, type FileRejection, type DropzoneOptions, type FileError } from 'react-dropzone';
import FilePreview from './FilePreview';

export interface FileWithPreview extends File {
  preview: string;
}

interface DropZoneProps {
  label?: string;
  onFilesChange?: (files: File[]) => void;
}

export const DropZone: React.FC<DropZoneProps> = ({ label, onFilesChange }) => {
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [rejected, setRejected] = useState<FileRejection[]>([]);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    if (acceptedFiles.length) {
      const mappedFiles = acceptedFiles.map((file) =>
        Object.assign(file, { preview: URL.createObjectURL(file) }),
      );
      setFiles((prev: FileWithPreview[]) => [...prev, ...mappedFiles]);
    }
    if (rejectedFiles.length) {
      setRejected(() => [...rejectedFiles]);
    }
  }, []);

  const duplicateValidator = useCallback(
    (file: File): FileError | null => {
      const isDuplicate = files.some((existing) => existing.name === file.name);
      if (isDuplicate) {
        return {
          code: 'duplicate-file',
          message: 'Duplicate file detected. Multiple files with the same name are not allowed.',
        };
      }
      return null;
    },
    [files],
  );

  const dropzoneOptions: DropzoneOptions = {
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/x-ipynb+json': ['.ipynb'],
      'application/json': ['.ipynb'],
    },
    multiple: true,
    validator: duplicateValidator,
  };

  const { getRootProps, getInputProps, isFocused, isDragAccept, isDragReject, isDragActive } =
    useDropzone(dropzoneOptions);

  useEffect(() => {
    return () => {
      files.forEach((file) => URL.revokeObjectURL(file.preview));
    };
  }, [files]);

  useEffect(() => {
    if (onFilesChange) onFilesChange(files);
  }, [files, onFilesChange]);

  const removeFile = (name: string): void => {
    setFiles((prev) => prev.filter((file) => file.name !== name));
  };

  const removeRejected = (name: string): void => {
    setRejected((prev) => prev.filter(({ file }) => file.name !== name));
  };

  const removeAll = (): void => {
    setFiles([]);
    setRejected([]);
  };

  const dropMessage = useMemo(() => {
    if (isDragReject) return 'Files will be rejected — only .xlsx, .xls and .ipynb allowed';
    if (isDragAccept) return '✓ All files look good — drop them here';
    if (isDragActive) return 'Drop the files here…';
    return 'Drag & drop .xlsx / .ipynb files here, or click to select';
  }, [isDragActive, isDragAccept, isDragReject]);

  const zoneClass = [
    'dz-zone',
    isFocused ? 'dz-zone-focused' : '',
    isDragAccept ? 'dz-zone-accept' : '',
    isDragReject ? 'dz-zone-reject' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="dz-root">
      {label && <span className="dz-label-styled">{label}</span>}

      <div {...getRootProps({ className: zoneClass })}>
        <input {...getInputProps()} />
        <div className="dz-icon">
          {isDragAccept ? '✅' : isDragReject ? '❌' : '📂'}
        </div>
        <span className="dz-message-text">{dropMessage}</span>
      </div>

      {(files.length > 0 || rejected.length > 0) && (
        <div className="dz-lists">
          {files.length > 0 && (
            <div>
              <p className="dz-list-title">Selected files</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {files.map((file) => (
                  <div key={file.name} className="dz-file-row">
                    <div>
                      <div className="dz-file-name">{file.name}</div>
                      <div className="dz-file-size">{(file.size / 1024).toFixed(1)} KB</div>
                      <FilePreview file={file} />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(file.name)}
                      className="dz-remove-btn"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {rejected.length > 0 && (
            <div>
              <p className="dz-list-title" style={{ color: 'var(--red)' }}>Rejected files</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {rejected.map(({ file, errors }) => (
                  <div key={file.name} className="dz-file-row" style={{ borderColor: 'rgba(255,77,106,0.2)' }}>
                    <div>
                      <div className="dz-file-name">{file.name}</div>
                      <div className="dz-file-size">{(file.size / 1024).toFixed(1)} KB</div>
                      <ul className="dz-errors">
                        {errors.map((error) => (
                          <li key={error.code}>{error.message}</li>
                        ))}
                      </ul>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeRejected(file.name)}
                      className="dz-remove-btn"
                    >
                      Dismiss
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(files.length > 0 || rejected.length > 0) && (
            <button type="button" onClick={removeAll} className="dz-remove-all-btn">
              Clear all
            </button>
          )}
        </div>
      )}
    </div>
  );
};
