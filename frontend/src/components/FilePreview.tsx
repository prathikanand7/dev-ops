import React from 'react';

interface FilePreviewProps {
  file: File;
}

const FilePreview: React.FC<FilePreviewProps> = ({ file }) => {
  const name = file.name.toLowerCase();

  if (name.endsWith('.ipynb')) {
    return <p className="dz-preview-note">📓 Notebook (.ipynb)</p>;
  }

  if (name.endsWith('.xlsx') || name.endsWith('.xls')) {
    return <p className="dz-preview-note">📊 Spreadsheet (.xlsx)</p>;
  }

  return null;
};

export default FilePreview;