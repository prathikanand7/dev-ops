import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useDropzone, type FileRejection, type DropzoneOptions, type FileError } from 'react-dropzone';
import { FiUploadCloud, FiCheckCircle, FiXCircle, FiFolder } from 'react-icons/fi';
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
      const mapped = acceptedFiles.map((file) => Object.assign(file, { preview: URL.createObjectURL(file) }));
      setFiles((prev) => [...prev, ...mapped]);
    }
    if (rejectedFiles.length) setRejected(() => [...rejectedFiles]);
  }, []);

  const duplicateValidator = useCallback(
    (file: File): FileError | null => {
      if (files.some((f) => f.name === file.name)) {
        return { code: 'duplicate-file', message: 'Duplicate file detected. Multiple files with the same name are not allowed.' };
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
      'text/yaml': ['.yaml', '.yml'],
      'application/x-yaml': ['.yaml', '.yml'],
      'text/plain': ['.txt'],
    },
    multiple: true,
    validator: duplicateValidator,
  };

  const { getRootProps, getInputProps, isFocused, isDragAccept, isDragReject, isDragActive } =
    useDropzone(dropzoneOptions);

  useEffect(() => { return () => { files.forEach((f) => URL.revokeObjectURL(f.preview)); }; }, [files]);
  useEffect(() => { if (onFilesChange) onFilesChange(files); }, [files, onFilesChange]);

  const removeFile = (name: string) => setFiles((p) => p.filter((f) => f.name !== name));
  const removeRejected = (name: string) => setRejected((p) => p.filter(({ file }) => file.name !== name));
  const removeAll = () => { setFiles([]); setRejected([]); };

  const dropMessage = useMemo(() => {
    if (isDragReject) return 'Files will be rejected — only .xlsx, .xls, .ipynb, .yaml, .yml, and .txt allowed';
    if (isDragAccept) return 'All files look good — drop them here';
    if (isDragActive) return 'Drop the files here…';
    return 'Drag & drop only (.xlsx / .xls / .ipynb / .yaml / .txt) files here, or click to select';
  }, [isDragActive, isDragAccept, isDragReject]);

  const dropIcon = useMemo(() => {
    if (isDragAccept) return <FiCheckCircle size={22} style={{ color: 'var(--accent)' }} />;
    if (isDragReject) return <FiXCircle size={22} style={{ color: 'var(--red)' }} />;
    if (isDragActive) return <FiFolder size={22} />;
    return <FiUploadCloud size={22} />;
  }, [isDragActive, isDragAccept, isDragReject]);

  const zoneClass = ['dz-zone', isFocused ? 'dz-zone-focused' : '', isDragAccept ? 'dz-zone-accept' : '', isDragReject ? 'dz-zone-reject' : ''].filter(Boolean).join(' ');

  return (
    <div className="dz-root">
      {label && <span className="dz-label-styled">{label}</span>}

      <div {...getRootProps({ className: zoneClass })}>
        <input {...getInputProps()} />
        <div className="dz-icon">{dropIcon}</div>
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
                    <button type="button" onClick={() => removeFile(file.name)} className="dz-remove-btn">Remove</button>
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
                  <div key={file.name} className="dz-file-row" style={{ borderColor: 'rgba(255,85,119,0.2)' }}>
                    <div>
                      <div className="dz-file-name">{file.name}</div>
                      <div className="dz-file-size">{(file.size / 1024).toFixed(1)} KB</div>
                      <ul className="dz-errors">{errors.map((err) => <li key={err.code}>{err.message}</li>)}</ul>
                    </div>
                    <button type="button" onClick={() => removeRejected(file.name)} className="dz-remove-btn">Dismiss</button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(files.length > 0 || rejected.length > 0) && (
            <button type="button" onClick={removeAll} className="dz-remove-all-btn">Clear all</button>
          )}
        </div>
      )}
    </div>
  );
};