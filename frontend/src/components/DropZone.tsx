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
        Object.assign(file, {
          preview: URL.createObjectURL(file),
        }),
      );

      setFiles((prev: FileWithPreview[]) => [...prev, ...mappedFiles]);
    }

    if (rejectedFiles.length) {
      setRejected((prev) => [...rejectedFiles]);
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
    if (onFilesChange) {
      onFilesChange(files);
    }
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
    if (isDragReject) {
      return 'Files will be rejected (only .xlsx, .xls and .ipynb allowed)';
    }

    if (isDragAccept) {
      return 'All files look good – drop them here';
    }

    if (isDragActive) {
      return 'Drop the files here…';
    }

    return 'Drag & drop .xlsx / .ipynb files here, or click to select';
  }, [isDragActive, isDragAccept, isDragReject]);

  const baseStyle: React.CSSProperties = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '18px',
    borderWidth: 2,
    borderRadius: 10,
    borderColor: '#1f2937',
    borderStyle: 'dashed',
    backgroundColor: '#b9bcc1',
    color: ' #000000',
    outline: 'none',
    transition: 'border .24s ease-in-out, background-color .24s ease-in-out',
  };

  const style = useMemo<React.CSSProperties>(
    () => ({
      ...baseStyle,
      ...(isFocused ? { borderColor: '#38bdf8' } : {}),
      ...(isDragAccept ? { borderColor: '#22c55e', backgroundColor: '#022c22' } : {}),
      ...(isDragReject ? { borderColor: '#f97373', backgroundColor: '#3b0f0f' } : {}),
    }),
    [isFocused, isDragAccept, isDragReject],
  );

  return (
    <div className="dz-root">
      {label && <p className="dz-label">{label}</p>}

      <div {...getRootProps({ style })}>
        <input {...getInputProps()} />
        <span className="dz-message">{dropMessage}</span>
      </div>

      {(files.length > 0 || rejected.length > 0) && (
        <div className="dz-lists">
          {files.length > 0 && (
            <div className="dz-list">
              <h4>Selected files</h4>
              <ul>
                {files.map((file) => (
                  <li key={file.name}>
                    <div className="dz-file-row">
                      <div>
                        <div className="dz-file-name">{file.name}</div>
                        <div className="dz-file-size">{file.size} bytes</div>
                        <FilePreview file={file} />
                      </div>
                      <button type="button" onClick={() => removeFile(file.name)} className="dz-remove-btn">
                        Remove
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {rejected.length > 0 && (
            <div className="dz-list dz-list-rejected">
              <h4>Rejected files</h4>
              <ul>
                {rejected.map(({ file, errors }) => (
                  <li key={file.name}>
                    <div className="dz-file-row">
                      <div>
                        <div className="dz-file-name">{file.name}</div>
                        <div className="dz-file-size">{file.size} bytes</div>
                        <ul className="dz-errors">
                          {errors.map((error) => (
                            <li key={error.code}>{error.message}</li>
                          ))}
                        </ul>
                      </div>
                      <button type="button" onClick={() => removeRejected(file.name)} className="dz-remove-btn">
                        Dismiss
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
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

