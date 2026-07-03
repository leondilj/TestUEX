"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type DragEvent } from "react";

import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api-client";
import { taskKeys } from "@/lib/query-keys";
import type { Attachment, Task } from "@/lib/types";

// Copy exata da T27 §4 — não parafrasear
const RESTRICTIONS = "PNG, JPG, GIF, WebP, PDF, DOC, TXT — até 10MB cada";
const TYPE_ERROR = "Tipo de arquivo não permitido.";
const SIZE_ERROR = "Arquivo acima de 10MB.";
const UPLOAD_ERROR = "Falha no envio.";
const REMOVE_ERROR = "Não foi possível excluir. Tente novamente.";

// Espelha api/app/config.py (allowed_upload_types / max_upload_bytes) —
// validação client-side antes de qualquer request (T27 §4)
const MAX_BYTES = 10 * 1024 * 1024;
const ALLOWED_MIME = new Set([
  "image/png",
  "image/jpeg",
  "image/gif",
  "image/webp",
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
]);
// fallback por extensão quando o browser não informa o MIME
const ALLOWED_EXTENSIONS = new Set([
  "png", "jpg", "jpeg", "gif", "webp", "pdf", "doc", "docx", "txt",
]);
const ACCEPT = ".png,.jpg,.jpeg,.gif,.webp,.pdf,.doc,.docx,.txt";

type UploadStatus = "waiting" | "uploading" | "error";

interface UploadEntry {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number; // 0..1, só relevante em "uploading"
  error?: string;
  // erro de validação (tipo/tamanho) não é retentável; falha de rede é
  retryable?: boolean;
}

function validationError(file: File): string | null {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  const typeAllowed = file.type
    ? ALLOWED_MIME.has(file.type)
    : ALLOWED_EXTENSIONS.has(extension);
  if (!typeAllowed) return TYPE_ERROR;
  if (file.size > MAX_BYTES) return SIZE_ERROR;
  return null;
}

// ellipsis no meio preservando a extensão (T27 §4)
function truncateMiddle(name: string, max = 36): string {
  if (name.length <= max) return name;
  const tail = name.slice(-12);
  return `${name.slice(0, max - 13)}…${tail}`;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`;
}

// rótulo do ícone genérico por tipo (thumbnail real só para imagens)
function typeBadge(contentType: string, filename: string): string {
  if (contentType.startsWith("image/")) return "IMG";
  if (contentType === "application/pdf") return "PDF";
  if (contentType === "text/plain") return "TXT";
  const extension = filename.split(".").pop()?.toUpperCase() ?? "";
  return extension === "DOCX" ? "DOC" : extension || "DOC";
}

interface AttachmentsSectionProps {
  taskId: string;
  attachments: Attachment[];
  announce: (message: string) => void;
  onError: (message: string) => void;
}

// Seção "Anexos" do drawer (T34/T27 §4) — só em modo edição (a tarefa
// precisa de id). Uploads sequenciais (1 multipart por arquivo, contrato da
// API); erros por arquivo não bloqueiam a fila. A lista de anexos persistidos
// vem do cache do detalhe da tarefa (taskKeys.detail), atualizado aqui.
export function AttachmentsSection({
  taskId,
  attachments,
  announce,
  onError,
}: AttachmentsSectionProps) {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploads, setUploads] = useState<UploadEntry[]>([]);
  const [dragging, setDragging] = useState(false);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  // ids já disparados — evita upload duplo (StrictMode roda o effect 2x)
  const startedRef = useRef(new Set<string>());

  function appendToCache(attachment: Attachment) {
    queryClient.setQueryData<Task>(taskKeys.detail(taskId), (old) =>
      old ? { ...old, attachments: [...old.attachments, attachment] } : old,
    );
  }

  // bomba da fila: sem ninguém enviando, dispara o próximo "waiting".
  // Reexecuta a cada mudança em uploads — o próprio setUploads realimenta.
  useEffect(() => {
    if (uploads.some((u) => u.status === "uploading")) return;
    const next = uploads.find((u) => u.status === "waiting");
    if (!next || startedRef.current.has(next.id)) return;
    startedRef.current.add(next.id);

    setUploads((all) =>
      all.map((u) =>
        u.id === next.id ? { ...u, status: "uploading" as const } : u,
      ),
    );
    api.attachments
      .upload(taskId, next.file, (fraction) => {
        setUploads((all) =>
          all.map((u) =>
            u.id === next.id ? { ...u, progress: fraction } : u,
          ),
        );
      })
      .then((attachment) => {
        setUploads((all) => all.filter((u) => u.id !== next.id));
        appendToCache(attachment);
        announce(`${attachment.filename} anexado`);
      })
      .catch((error: unknown) => {
        // 400 = validação do servidor (tipo/tamanho) — não retentável
        const rejected = error instanceof ApiError && error.status === 400;
        const message = rejected
          ? typeof error.detail === "string" && error.detail.includes("10")
            ? SIZE_ERROR
            : TYPE_ERROR
          : UPLOAD_ERROR;
        setUploads((all) =>
          all.map((u) =>
            u.id === next.id
              ? { ...u, status: "error" as const, error: message, retryable: !rejected }
              : u,
          ),
        );
      });
    // appendToCache/announce são estáveis o bastante para este fluxo
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uploads, taskId]);

  function enqueue(files: FileList | File[]) {
    const entries: UploadEntry[] = Array.from(files).map((file) => {
      const error = validationError(file);
      return {
        id: crypto.randomUUID(),
        file,
        status: error ? ("error" as const) : ("waiting" as const),
        progress: 0,
        error: error ?? undefined,
        retryable: false,
      };
    });
    if (entries.length > 0) setUploads((all) => [...all, ...entries]);
  }

  function retry(entry: UploadEntry) {
    // novo id = novo disparo (startedRef guarda os já iniciados)
    setUploads((all) =>
      all.map((u) =>
        u.id === entry.id
          ? {
              ...u,
              id: crypto.randomUUID(),
              status: "waiting" as const,
              progress: 0,
              error: undefined,
            }
          : u,
      ),
    );
  }

  function handleDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setDragging(false);
    if (event.dataTransfer.files.length > 0) enqueue(event.dataTransfer.files);
  }

  const remove = useMutation({
    mutationFn: (attachment: Attachment) =>
      api.attachments.remove(attachment.id),
    // remoção otimista: item some na hora; falha → item volta + toast (T27 §4)
    onMutate: (attachment) => {
      const key = taskKeys.detail(taskId);
      const previous = queryClient.getQueryData<Task>(key);
      queryClient.setQueryData<Task>(key, (old) =>
        old
          ? {
              ...old,
              attachments: old.attachments.filter(
                (a) => a.id !== attachment.id,
              ),
            }
          : old,
      );
      setConfirmingId(null);
      return { previous };
    },
    onError: (_error, _attachment, context) => {
      if (context?.previous) {
        queryClient.setQueryData(taskKeys.detail(taskId), context.previous);
      }
      onError(REMOVE_ERROR);
    },
    onSuccess: (_data, attachment) =>
      announce(`${attachment.filename} removido`),
  });

  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-sm font-medium">Anexos</span>

      <button
        type="button"
        aria-describedby={`${taskId}-restrictions`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className={`flex flex-col items-center gap-1 rounded-[10px] border border-dashed px-4 py-5 text-sm transition-colors ${
          dragging
            ? "border-accent bg-accent/5"
            : "border-line hover:border-accent hover:bg-accent/5"
        }`}
      >
        <span>
          <span aria-hidden="true">⬆ </span>
          Arraste arquivos ou clique para selecionar
        </span>
        {/* restrições sempre visíveis — o usuário não descobre o limite pelo erro */}
        <span id={`${taskId}-restrictions`} className="text-xs text-ink-muted">
          {RESTRICTIONS}
        </span>
      </button>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPT}
        className="hidden"
        onChange={(event) => {
          if (event.target.files) enqueue(event.target.files);
          // permite re-selecionar o mesmo arquivo depois de um erro
          event.target.value = "";
        }}
      />

      {(attachments.length > 0 || uploads.length > 0) && (
        <ul className="flex flex-col divide-y divide-line rounded-[10px] border border-line">
          {attachments.map((attachment) => (
            <li
              key={attachment.id}
              className="flex items-center gap-3 px-3 py-2"
            >
              <FileIcon attachment={attachment} />
              <span className="min-w-0 flex-1 truncate text-sm">
                {truncateMiddle(attachment.filename)}
              </span>
              {confirmingId === attachment.id ? (
                // confirmação compacta inline — anexo não merece modal (T27 §4)
                <span className="flex items-center gap-2 text-sm">
                  Remover?
                  <Button
                    type="button"
                    variant="danger-text"
                    className="!px-1 !py-0"
                    onClick={() => remove.mutate(attachment)}
                  >
                    Sim
                  </Button>
                  <Button
                    type="button"
                    variant="text"
                    className="!px-1 !py-0"
                    onClick={() => setConfirmingId(null)}
                  >
                    Não
                  </Button>
                </span>
              ) : (
                <>
                  <span className="whitespace-nowrap text-xs text-ink-muted">
                    {formatBytes(attachment.size_bytes)}
                  </span>
                  <a
                    href={api.attachments.downloadUrl(attachment.id)}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Baixar ${attachment.filename}`}
                    className="rounded p-1 text-ink-muted transition-colors hover:bg-paper hover:text-ink"
                  >
                    ⬇
                  </a>
                  <button
                    type="button"
                    aria-label={`Remover ${attachment.filename}`}
                    onClick={() => setConfirmingId(attachment.id)}
                    className="rounded p-1 text-ink-muted transition-colors hover:bg-paper hover:text-danger"
                  >
                    ✕
                  </button>
                </>
              )}
            </li>
          ))}

          {uploads.map((entry) => (
            <li key={entry.id} className="flex items-center gap-3 px-3 py-2">
              <span
                aria-hidden="true"
                className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-paper text-[10px] font-semibold text-ink-muted"
              >
                {typeBadge(entry.file.type, entry.file.name)}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm">
                  {truncateMiddle(entry.file.name)}
                </span>
                {entry.status === "error" ? (
                  <span role="alert" className="text-xs text-danger">
                    {entry.error}
                  </span>
                ) : entry.status === "uploading" ? (
                  <span
                    role="progressbar"
                    aria-label={`Enviando ${entry.file.name}`}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.round(entry.progress * 100)}
                    className="mt-1 block h-1 w-full overflow-hidden rounded-full bg-paper"
                  >
                    <span
                      className="block h-full rounded-full bg-accent transition-[width]"
                      style={{ width: `${Math.round(entry.progress * 100)}%` }}
                    />
                  </span>
                ) : (
                  <span className="text-xs text-ink-muted">Aguardando…</span>
                )}
              </span>
              {entry.status === "error" && entry.retryable && (
                <Button
                  type="button"
                  variant="text"
                  className="!px-1 !py-0"
                  onClick={() => retry(entry)}
                >
                  Tentar de novo
                </Button>
              )}
              {entry.status === "error" && (
                <button
                  type="button"
                  aria-label={`Dispensar ${entry.file.name}`}
                  onClick={() =>
                    setUploads((all) => all.filter((u) => u.id !== entry.id))
                  }
                  className="rounded p-1 text-ink-muted transition-colors hover:bg-paper hover:text-ink"
                >
                  ✕
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// Thumbnail 40×40 para imagens (o próprio endpoint de download serve como
// src — cookie segue junto por ser same-site); degrada para o badge genérico
// se a imagem não carregar (open question 1 da T27).
function FileIcon({ attachment }: { attachment: Attachment }) {
  const [broken, setBroken] = useState(false);
  const isImage = attachment.content_type.startsWith("image/") && !broken;

  if (isImage) {
    return (
      /* eslint-disable-next-line @next/next/no-img-element -- src autenticado
         por cookie fora do domínio do otimizador do Next */
      <img
        src={api.attachments.downloadUrl(attachment.id)}
        alt=""
        width={40}
        height={40}
        onError={() => setBroken(true)}
        className="size-10 shrink-0 rounded-lg border border-line object-cover"
      />
    );
  }
  return (
    <span
      aria-hidden="true"
      className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-paper text-[10px] font-semibold text-ink-muted"
    >
      {typeBadge(attachment.content_type, attachment.filename)}
    </span>
  );
}
