"use client";

import { useState } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { DropZone } from "@/components/upload/DropZone";
import { DocTypeSelector } from "@/components/upload/DocTypeSelector";
import { PipelineStatus } from "@/components/pipeline/PipelineStatus";

interface UploadResponse {
  id: string;
  job_id: string | null;
}

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [docType, setDocType] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeJob, setActiveJob] = useState<{ jobId: string; documentId: string } | null>(null);

  async function handleUpload() {
    if (!files[0] || !docType) return;
    setUploading(true);
    setUploadProgress(10);

    const formData = new FormData();
    formData.append("file", files[0]);
    formData.append("doc_type", docType);

    try {
      setUploadProgress(40);
      const result = await api.upload<UploadResponse>("/api/documents/upload", formData);
      setUploadProgress(100);
      if (result.job_id) {
        setActiveJob({ jobId: result.job_id, documentId: result.id });
      } else {
        toast.success("Document uploaded");
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Upload failed";
      toast.error(msg);
    } finally {
      setUploading(false);
    }
  }

  function handleComplete() {
    setFiles([]);
    setDocType("");
    setActiveJob(null);
  }

  const canUpload = files.length > 0 && docType && !uploading && !activeJob;

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE] mb-2">
          Upload Documents
        </h1>
        <p className="text-[#64748B]">
          Add master agreements and compliance documents to build your org&apos;s knowledge base
        </p>
      </div>

      {activeJob ? (
        <PipelineStatus
          jobId={activeJob.jobId}
          documentId={activeJob.documentId}
          onComplete={handleComplete}
        />
      ) : (
        <div className="space-y-4">
          <DropZone
            onFiles={setFiles}
            uploading={uploading}
            uploadProgress={uploadProgress}
            uploadingFileName={files[0]?.name}
          />

          {files.length > 0 && (
            <DocTypeSelector value={docType} onChange={setDocType} />
          )}

          <button
            onClick={handleUpload}
            disabled={!canUpload}
            className={[
              "w-full py-3 rounded-md font-medium transition-colors",
              canUpload
                ? "bg-[#C9A84C] text-[#0F1729] hover:bg-[#B8963E]"
                : "bg-[#1E2D4A] text-[#64748B] cursor-not-allowed",
            ].join(" ")}
          >
            {uploading ? "Uploading…" : "Upload & Process"}
          </button>
        </div>
      )}
    </div>
  );
}
