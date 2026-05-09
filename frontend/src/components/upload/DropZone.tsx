"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload } from "lucide-react";

interface DropZoneProps {
  onFiles: (files: File[]) => void;
  uploading?: boolean;
  uploadProgress?: number;
  uploadingFileName?: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileTypeBadge(file: File): string {
  return file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "DOCX";
}

export function DropZone({ onFiles, uploading, uploadProgress, uploadingFileName }: DropZoneProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const onDrop = useCallback(
    (accepted: File[]) => {
      setSelectedFiles(accepted);
      onFiles(accepted);
    },
    [onFiles],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    maxSize: 50 * 1024 * 1024,
    disabled: uploading,
  });

  if (uploading && uploadingFileName !== undefined) {
    return (
      <div className="border border-[#1E2D4A] rounded-lg p-8 bg-[#0D1829]">
        <p className="text-sm text-[#8899BB] mb-2 truncate">{uploadingFileName}</p>
        <div className="h-2 bg-[#1E2D4A] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#C9A84C] transition-all duration-300"
            style={{ width: `${uploadProgress ?? 0}%` }}
          />
        </div>
        <p className="text-xs text-[#64748B] mt-1">{uploadProgress ?? 0}%</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={[
          "border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all",
          isDragActive
            ? "border-[#C9A84C] bg-[#C9A84C]/5 shadow-[0_0_20px_rgba(201,168,76,0.15)]"
            : "border-[#1E2D4A] hover:border-[#C9A84C]/50 bg-[#0D1829]",
        ].join(" ")}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto mb-4 text-[#64748B]" size={40} />
        <p className="text-[#F5F3EE] font-medium mb-1">
          Drop contracts here or click to browse
        </p>
        <p className="text-sm text-[#64748B]">PDF and DOCX up to 50MB</p>
      </div>

      {selectedFiles.length > 0 && (
        <ul className="space-y-2">
          {selectedFiles.map((f, i) => (
            <li key={i} className="flex items-center gap-3 bg-[#0D1829] border border-[#1E2D4A] rounded-md px-4 py-2">
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-[#1E2D4A] text-[#C9A84C] uppercase tracking-wider">
                {fileTypeBadge(f)}
              </span>
              <span className="flex-1 text-sm text-[#F5F3EE] truncate">{f.name}</span>
              <span className="text-xs text-[#64748B] shrink-0">{formatBytes(f.size)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
