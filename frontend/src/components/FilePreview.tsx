import React from 'react';
import { FiBook, FiGrid, FiFileText } from 'react-icons/fi';

interface FilePreviewProps { file: File; }

const FilePreview: React.FC<FilePreviewProps> = ({ file }) => {
  const name = file.name.toLowerCase();
  if (name.endsWith('.ipynb')) return <p className="dz-preview-note"><FiBook size={10} />Notebook (.ipynb)</p>;
  if (name.endsWith('.xlsx') || name.endsWith('.xls')) return <p className="dz-preview-note"><FiGrid size={10} />Spreadsheet (.xlsx)</p>;
  if (name.endsWith('.yaml') || name.endsWith('.yml') || name.endsWith('.txt')) return <p className="dz-preview-note"><FiFileText size={10} />Environment file (.yaml/.yml/.txt)</p>;
  return null;
};

export default FilePreview;