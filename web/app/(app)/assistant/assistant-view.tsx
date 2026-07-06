"use client";

import { useMutation } from "@tanstack/react-query";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type SubmitEvent,
} from "react";

import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api-client";
import type { AssistantToolCall } from "@/lib/types";

// Rótulos amigáveis para transparência de tool_calls (T49) — o nome cru da
// tool aparece de todo jeito ao lado (spec/architecture.md: nunca esconder a
// ação do usuário), isso só torna a leitura mais rápida.
const TOOL_LABELS: Record<string, string> = {
  list_projects: "Listou seus projetos",
  list_tasks: "Listou tarefas",
  create_task: "Criou uma tarefa",
  update_task_status: "Atualizou o status de uma tarefa",
};

const GENERIC_ERROR = "Não foi possível enviar sua mensagem. Tente novamente.";
const UNAVAILABLE_ERROR =
  "O assistente está indisponível no momento. Tente novamente em instantes.";

type ChatMessage =
  | { id: string; role: "user"; content: string }
  | {
      id: string;
      role: "assistant";
      content: string;
      toolCalls: AssistantToolCall[];
    }
  | { id: string; role: "system-error"; content: string };

function errorMessage(error: unknown): string {
  // 502 = falha ao chamar a API da Anthropic (spec/api.md); 401 é tratado
  // globalmente (Providers redireciona para /login) e nunca chega aqui
  if (error instanceof ApiError && error.status === 502) return UNAVAILABLE_ERROR;
  return GENERIC_ERROR;
}

export function AssistantView() {
  const fieldId = useId();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [announcement, setAnnouncement] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const chat = useMutation({
    mutationFn: (message: string) =>
      api.assistant.chat({ message, conversation_id: conversationId }),
    onSuccess: (data) => {
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.reply,
          toolCalls: data.tool_calls,
        },
      ]);
      setAnnouncement(data.reply);
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 401) return;
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "system-error",
          content: errorMessage(error),
        },
      ]);
    },
  });

  function send() {
    const trimmed = input.trim();
    if (!trimmed || chat.isPending) return;
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: trimmed },
    ]);
    setInput("");
    chat.mutate(trimmed);
  }

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    send();
  }

  // Enter envia, Shift+Enter quebra linha (convenção padrão de chat)
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      formRef.current?.requestSubmit();
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-display text-2xl font-semibold">Assistente</h1>

      <div className="flex h-[70vh] min-h-[420px] flex-col rounded-[10px] border border-line bg-surface">
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-4 py-4 sm:px-6"
        >
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
              <p className="font-display text-lg font-semibold">
                Pergunte sobre seus projetos e tarefas
              </p>
              <p className="max-w-sm text-sm text-ink-muted">
                O assistente pode listar projetos e tarefas, criar uma tarefa
                nova e atualizar o status de uma tarefa existente.
              </p>
            </div>
          ) : (
            <ul className="flex flex-col gap-3">
              {messages.map((message) => (
                <li key={message.id}>
                  <ChatBubble message={message} />
                </li>
              ))}
              {chat.isPending && (
                <li aria-hidden="true">
                  <div className="mr-auto flex max-w-[80%] items-center gap-1 rounded-lg border border-line bg-surface px-4 py-3">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted" />
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted [animation-delay:150ms]" />
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted [animation-delay:300ms]" />
                  </div>
                </li>
              )}
            </ul>
          )}
        </div>

        <form
          ref={formRef}
          onSubmit={handleSubmit}
          className="border-t border-line p-4"
        >
          <div className="flex items-end gap-2">
            <label htmlFor={fieldId} className="sr-only">
              Mensagem para o assistente
            </label>
            <textarea
              id={fieldId}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={2}
              placeholder="Pergunte algo ou peça para criar uma tarefa..."
              className="flex-1 resize-none rounded-lg border border-line bg-surface px-3 py-2 text-sm placeholder:text-ink-muted"
            />
            <Button
              type="submit"
              loading={chat.isPending}
              disabled={!input.trim()}
            >
              Enviar
            </Button>
          </div>
        </form>
      </div>

      <div aria-live="polite" className="sr-only">
        {announcement}
      </div>
    </div>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="ml-auto max-w-[80%] rounded-lg bg-accent px-4 py-2 text-sm text-white">
        {message.content}
      </div>
    );
  }

  if (message.role === "system-error") {
    return (
      <div className="mr-auto max-w-[80%] rounded-lg border border-danger/30 bg-danger/5 px-4 py-2 text-sm text-danger">
        {message.content}
      </div>
    );
  }

  return (
    <div className="mr-auto max-w-[80%] rounded-lg border border-line bg-surface px-4 py-2 text-sm">
      <p className="whitespace-pre-wrap">{message.content}</p>
      {message.toolCalls.length > 0 && (
        <details className="mt-2 text-xs text-ink-muted">
          <summary className="cursor-pointer font-medium text-ink-muted hover:text-ink">
            {message.toolCalls.length === 1
              ? "1 ferramenta usada"
              : `${message.toolCalls.length} ferramentas usadas`}
          </summary>
          <ul className="mt-2 flex flex-col gap-1.5">
            {message.toolCalls.map((call, index) => (
              <li key={index} className="rounded bg-paper px-2 py-1.5">
                <span className="font-medium text-ink">
                  {TOOL_LABELS[call.tool] ?? call.tool}
                </span>
                <code className="ml-1.5 break-all font-mono text-[11px] text-ink-muted">
                  {JSON.stringify(call.input)}
                </code>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
