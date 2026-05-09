"use client";

import { useState } from "react";
import { Trash2 } from "lucide-react";
import type { DocumentListItem } from "@/types";

interface DocumentCardProps {
  doc: DocumentListItem;
  onDelete: (id: string) => Promise<void>;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-600/20 text-gray-300",
  nlp_processing: "bg-blue-600/20 text-blue-300",
  distilling: "bg-purple-600/20 text-purple-300",
  complete: "bg-green-600/20 text-green-300",
  error: "bg-red-600/20 text-red-300",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  nlp_processing: "NLP Processing",
  distilling: "Distilling",
  complete: "Complete",
  error: "Error",
};

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function DocumentCard({ doc, onDelete }: DocumentCardProps) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    await onDelete(doc.id);
    setDeleting(false);
    setConfirming(false);
  }

  const statusClass = STATUS_STYLES[doc.status] ?? STATUS_STYLES.pending;
  const statusLabel = STATUS_LABELS[doc.status] ?? doc.status;

  return (
    <div className="flex items-center gap-4 bg-[#1A2540] border border-[#1E2D4A] rounded-md px-4 py-3">
      <div className="flex-1 min-w-0">
        <p className="text-sm text-[#F5F3EE] truncate font-medium">{doc.filename}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-xs text-[#64748B]">{doc.doc_type}</span>
          <span className="text-xs text-[#64748B]">·</span>
          <span className="text-xs text-[#64748B]">{relativeTime(doc.upload_date)}</span>
        </div>
      </div>

      <span className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${statusClass}`}>
        {statusLabel}
      </span>

      {confirming ? (
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="text-xs text-red-400 hover:text-red-300 font-medium"
          >
            {deleting ? "Deleting…" : "Confirm"}
          </button>
          <button
            onClick={() => setConfirming(false)}
            className="text-xs text-[#64748B] hover:text-[#8899BB]"
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={() => setConfirming(true)}
          className="text-[#64748B] hover:text-red-400 transition-colors shrink-0"
          aria-label="Delete document"
        >
          <Trash2 size={15} />
        </button>
      )}
    </div>
  );
}
