import { useNavigate } from "@solidjs/router";
import { createEffect, createMemo, createResource, createSignal, For, onCleanup, Show } from "solid-js";
import { apiFetch, ApiError } from "../shared/api";
import { getAuthToken, getCurrentUserId, setAuthToken } from "../shared/auth";
import { createReliableWs } from "../shared/ws";
import { ChannelPickerGrid } from "./chat/ChannelPickerGrid";
import { Composer } from "./chat/Composer";
import { ChatHeader } from "./chat/Header";
import { MessageList } from "./chat/MessageList";
import { MessageBubble } from "./chat/MessageBubble";
import { MobileSidebar, Sidebar } from "./chat/Sidebar";
import type {
  ChannelCreate,
  ChannelRead,
  MessageCreate,
  MessageRead,
  PaginationResponse,
  SpaceCreate,
  SpaceRead,
} from "../shared/dto";

type UiMessage = Omit<MessageRead, "status"> & { status: MessageRead["status"] | "pending" };

export function ChatPage() {
  const navigate = useNavigate();
  const [selectedSpaceId, setSelectedSpaceId] = createSignal<string | null>(null);
  const [selectedChannelId, setSelectedChannelId] = createSignal<string | null>(null);
  const [focusedThreadId, setFocusedThreadId] = createSignal<string | null>(null);
  const [didRestoreSelection, setDidRestoreSelection] = createSignal(false);
  const [channelPickerOpen, setChannelPickerOpen] = createSignal(false);
  const [composerText, setComposerText] = createSignal("");
  const [emojiOpen, setEmojiOpen] = createSignal(false);
  let fileInputRef: HTMLInputElement | undefined;

  const [mobileSidebarOpen, setMobileSidebarOpen] = createSignal(false);
  const [threadDrawerOpen, setThreadDrawerOpen] = createSignal(false);

  const [showCreateSpace, setShowCreateSpace] = createSignal(false);
  const [newSpaceName, setNewSpaceName] = createSignal("");
  const [newSpaceDescription, setNewSpaceDescription] = createSignal("");

  const [showCreateChannel, setShowCreateChannel] = createSignal(false);
  const [newChannelName, setNewChannelName] = createSignal("");
  const [createChannelError, setCreateChannelError] = createSignal<string | null>(null);
  const [creating, setCreating] = createSignal(false);

  const [ws, setWs] = createSignal<WebSocket | null>(null);
  const [pendingByCommandId, setPendingByCommandId] = createSignal<Map<string, UiMessage>>(new Map());
  const [liveMessages, setLiveMessages] = createSignal<UiMessage[]>([]);
  const [wsState, setWsState] = createSignal<"connecting" | "open" | "closed">("closed");
  let wsClient: ReturnType<typeof createReliableWs> | null = null;

  function upsertLiveMessage(message: UiMessage) {
    setLiveMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === message.id);
      if (idx === -1) {
        return [...prev, message];
      }
      const next = prev.slice();
      next[idx] = message;
      return next;
    });
  }

  createEffect(() => {
    if (getAuthToken() === null) {
      navigate("/auth", { replace: true });
    }
  });

  createEffect(() => {
    if (didRestoreSelection()) {
      return;
    }
    const userId = getCurrentUserId();
    if (userId === null) {
      return;
    }
    const list = channels()?.items;
    if (!list || list.length === 0) {
      return;
    }
    const savedChannelId = localStorage.getItem(`sync.chat.lastChannelId.${userId}`);
    if (savedChannelId !== null && savedChannelId.trim() !== "") {
      const found = list.find((c) => c.id === savedChannelId) ?? null;
      if (found) {
        setSelectedSpaceId(found.space_id);
        setSelectedChannelId(found.id);
        setChannelPickerOpen(false);
      }
    }
    setDidRestoreSelection(true);
  });

  createEffect(() => {
    const userId = getCurrentUserId();
    if (userId === null) {
      return;
    }
    const channelId = selectedChannelId();
    if (channelId === null) {
      localStorage.removeItem(`sync.chat.lastChannelId.${userId}`);
      return;
    }
    localStorage.setItem(`sync.chat.lastChannelId.${userId}`, channelId);
  });

  createEffect(() => {
    const userId = getCurrentUserId();
    if (userId === null) {
      return;
    }
    const spaceId = selectedSpaceId();
    if (spaceId === null) {
      localStorage.removeItem(`sync.chat.lastSpaceId.${userId}`);
      return;
    }
    localStorage.setItem(`sync.chat.lastSpaceId.${userId}`, spaceId);
  });

  createEffect(() => {
    const token = getAuthToken();
    if (token === null) {
      return;
    }
    if (wsClient !== null) {
      return;
    }
    setWsState("connecting");
    const client = createReliableWs({
      token,
      onOpen: () => {
        setWsState("open");
        // В этом файле `ws()` используется только как "подключен/не подключен".
        // Реальная отправка идёт через wsClient.
        setWs({} as unknown as WebSocket);
      },
      onClose: () => {
        setWsState("closed");
        setWs(null);
      },
      onError: () => {
        setWsState("closed");
        setWs(null);
        setPendingByCommandId((prev) => {
          const next = new Map(prev);
          for (const [id, pending] of next.entries()) {
            next.set(id, { ...pending, status: "failed" });
          }
          return next;
        });
      },
      onMessage: (data) => {
        const msg = JSON.parse(data);
        if (msg && typeof msg.ok === "boolean" && typeof msg.id === "string") {
          if (msg.ok === true && msg.result) {
            setPendingByCommandId((prev) => {
              const next = new Map(prev);
              next.delete(msg.id);
              return next;
            });
            if (msg.result && typeof msg.result.channel_id === "string") {
              const currentChannel = selectedChannelId();
              if (currentChannel !== null && msg.result.channel_id === currentChannel) {
                upsertLiveMessage(msg.result as UiMessage);
              }
            }
          } else {
            setPendingByCommandId((prev) => {
              const next = new Map(prev);
              const pending = next.get(msg.id);
              if (pending) {
                next.set(msg.id, { ...pending, status: "failed" });
              }
              return next;
            });
          }
          return;
        }
        if (msg && typeof msg.type === "string") {
          if (msg.type === "message.created" && msg.payload) {
            const currentChannel = selectedChannelId();
            if (currentChannel !== null && msg.payload.channel_id === currentChannel) {
              upsertLiveMessage(msg.payload as UiMessage);
            }
          }
        }
      },
    });
    wsClient = client;
    onCleanup(() => {
      wsClient?.close();
      wsClient = null;
      setWs(null);
      setWsState("closed");
    });
  });

  const [spaces, { refetch: refetchSpaces }] = createResource(async () => {
    return await apiFetch<PaginationResponse<SpaceRead>>("/api/spaces/?limit=50");
  });

  const [channels, { refetch: refetchChannels }] = createResource(async () => {
    return await apiFetch<PaginationResponse<ChannelRead>>("/api/channels/?limit=200");
  });

  const selectedChannel = createMemo(() => {
    const id = selectedChannelId();
    if (id === null) {
      return null;
    }
    return (channels()?.items ?? []).find((c) => c.id === id) ?? null;
  });

  const currentUserId = createMemo(() => getCurrentUserId());

  const channelsForSelectedSpace = createMemo(() => {
    const sid = selectedSpaceId();
    const all = channels()?.items ?? [];
    if (sid === null) {
      return all;
    }
    return all.filter((c) => c.space_id === sid);
  });

  const [messages, { refetch: refetchMessages }] = createResource(
    () => selectedChannelId(),
    async (channelId) => {
      if (channelId === null) {
        throw new Error("channelId обязателен для загрузки сообщений.");
      }
      return await apiFetch<PaginationResponse<MessageRead>>(
        `/api/channels/${channelId}/messages?limit=100`,
      );
    },
  );

  createEffect(() => {
    const channelId = selectedChannelId();
    if (channelId === null) {
      return;
    }
    setFocusedThreadId(null);
    setLiveMessages([]);
    setPendingByCommandId(new Map());
  });

  createEffect(() => {
    const items = messages()?.items;
    if (!items) {
      return;
    }
    setLiveMessages(items as UiMessage[]);
    setPendingByCommandId(new Map());
  });

  const displayMessages = createMemo(() => {
    const pending = Array.from(pendingByCommandId().values());
    const merged = [...liveMessages(), ...pending];
    merged.sort((a, b) => a.sent_at.localeCompare(b.sent_at));
    return merged;
  });

  const threadIdsInChannel = createMemo(() => {
    const items = displayMessages();
    const set = new Set<string>();
    for (const m of items) {
      if (m.thread_id !== null) {
        set.add(m.thread_id);
      }
    }
    return Array.from(set.values());
  });

  function logout() {
    setAuthToken(null);
    navigate("/", { replace: true });
  }

  async function createSpace() {
    const name = newSpaceName().trim();
    if (name === "") {
      throw new Error("Название пространства обязательно.");
    }
    const payload: SpaceCreate = {
      name,
      description: newSpaceDescription().trim() === "" ? null : newSpaceDescription().trim(),
    };
    setCreating(true);
    try {
      const created = await apiFetch<SpaceRead>("/api/spaces/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setShowCreateSpace(false);
      setNewSpaceName("");
      setNewSpaceDescription("");
      setSelectedSpaceId(created.id);
      await refetchSpaces();
    } finally {
      setCreating(false);
    }
  }

  async function createChannel() {
    setCreateChannelError(null);
    const spaceId = selectedSpaceId();
    if (spaceId === null) {
      setCreateChannelError("Сначала выбери пространство.");
      return;
    }
    const name = newChannelName().trim();
    if (name === "") {
      setCreateChannelError("Название канала обязательно.");
      return;
    }
    const payload: ChannelCreate = {
      space_id: spaceId,
      type: "topic",
      name,
      is_private: false,
      member_ids: null,
    };
    setCreating(true);
    try {
      const created = await apiFetch<ChannelRead>("/api/channels/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setShowCreateChannel(false);
      setNewChannelName("");
      setSelectedChannelId(created.id);
      setMobileSidebarOpen(false);
      await refetchChannels();
    } finally {
      setCreating(false);
    }
  }

  function openCreateChannel() {
    setCreateChannelError(null);
    const spaceId = selectedSpaceId();
    if (spaceId !== null) {
      setShowCreateChannel(true);
      return;
    }

    const items = spaces()?.items;
    if (items && items.length > 0) {
      setSelectedSpaceId(items[0].id);
      setShowCreateChannel(true);
      return;
    }

    setShowCreateSpace(true);
  }

  async function sendTextMessage() {
    const channelId = selectedChannelId();
    if (channelId === null) {
      throw new Error("Выбери канал.");
    }
    const body = composerText().trim();
    if (body === "") {
      return;
    }
    const payload: MessageCreate = {
      thread_id: focusedThreadId(),
      parent_message_id: null,
      contents: [{ type: "text/plain", data: { body }, order: 0 }],
    };
    setComposerText("");
    const client = wsClient;
    if (client === null) {
      throw new Error("WebSocket не подключен.");
    }
    const commandId = crypto.randomUUID();
    const currentUser = getCurrentUserId();
    if (currentUser === null) {
      throw new Error("Не удалось определить user_id из JWT.");
    }
    const pending: UiMessage = {
      id: `pending:${commandId}`,
      channel_id: channelId,
      thread_id: payload.thread_id,
      parent_message_id: payload.parent_message_id,
      sender: { id: currentUser, display_name: "Вы", avatar_url: null },
      status: "pending",
      sent_at: new Date().toISOString(),
      edited_at: null,
      contents: payload.contents as any,
    };
    setPendingByCommandId((prev) => {
      const next = new Map(prev);
      next.set(commandId, pending);
      return next;
    });
    try {
      client.sendJson({
        id: commandId,
        type: "messages.send",
        payload: { channel_id: channelId, body: payload },
      });
    } catch (e) {
      setPendingByCommandId((prev) => {
        const next = new Map(prev);
        const cur = next.get(commandId);
        if (cur) {
          next.set(commandId, { ...cur, status: "failed" });
        }
        return next;
      });
      throw e;
    }
  }

  async function uploadImage(file: File): Promise<string> {
    if (!file.type.startsWith("image/")) {
      throw new Error("Можно прикреплять только изображения.");
    }
    const fd = new FormData();
    fd.append("file", file);
    const res = await apiFetch<{ file: { id: string } }>("/api/files/", {
      method: "POST",
      body: fd,
    });
    if (!res.file || typeof res.file.id !== "string" || res.file.id.trim() === "") {
      throw new Error("Некорректный ответ загрузки файла.");
    }
    return res.file.id;
  }

  async function onPickImage(e: Event) {
    const input = e.currentTarget;
    if (!(input instanceof HTMLInputElement)) {
      throw new Error("Некорректный input.");
    }
    const files = input.files;
    if (!files || files.length === 0) {
      return;
    }
    const channelId = selectedChannelId();
    if (channelId === null) {
      throw new Error("Выбери канал.");
    }
    const file = files[0];
    input.value = "";
    const fileId = await uploadImage(file);
    const payload: MessageCreate = {
      thread_id: focusedThreadId(),
      parent_message_id: null,
      contents: [{ type: "mock/image", data: { file_id: fileId, alt_text: null }, order: 0 }],
    };
    await apiFetch<MessageRead>(`/api/channels/${channelId}/messages`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await refetchMessages();
  }

  function insertEmoji(char: string) {
    if (char.trim() === "") {
      throw new Error("emoji обязателен.");
    }
    setComposerText((prev) => prev + char);
    setEmojiOpen(false);
  }

  createEffect(() => {
    const items = spaces()?.items;
    if (!items || items.length === 0) {
      return;
    }
    if (selectedSpaceId() === null) {
      setSelectedSpaceId(items[0].id);
    }
  });

  createEffect(() => {
    const sid = selectedSpaceId();
    const list = channels()?.items;
    if (!list || list.length === 0) {
      return;
    }
    if (channelPickerOpen()) {
      return;
    }
    const currentChannelId = selectedChannelId();
    if (sid === null) {
      if (currentChannelId !== null) {
        const exists = list.some((c) => c.id === currentChannelId);
        if (exists) {
          return;
        }
      }
      setFocusedThreadId(null);
      setSelectedChannelId(list[0].id);
      return;
    }

    const stillInSpace =
      currentChannelId !== null && list.some((c) => c.id === currentChannelId && c.space_id === sid);
    if (stillInSpace) {
      return;
    }

    const firstInSpace = list.find((c) => c.space_id === sid) ?? null;
    setFocusedThreadId(null);
    setSelectedChannelId(firstInSpace ? firstInSpace.id : null);
  });

  createEffect(() => {
    const err = spaces.error;
    if (!(err instanceof ApiError) || err.status !== 401) {
      return;
    }
    setAuthToken(null);
    navigate("/auth", { replace: true });
  });

  createEffect(() => {
    const err = channels.error;
    if (!(err instanceof ApiError) || err.status !== 401) {
      return;
    }
    setAuthToken(null);
    navigate("/auth", { replace: true });
  });

  createEffect(() => {
    const err = messages.error;
    if (!(err instanceof ApiError) || err.status !== 401) {
      return;
    }
    setAuthToken(null);
    navigate("/auth", { replace: true });
  });

  return (
    <div class="h-full p-4 sm:p-6">
      <div
        class={
          "h-full grid gap-4 " +
          (focusedThreadId() === null ? "grid-cols-1 lg:grid-cols-[320px_1fr]" : "grid-cols-1")
        }
      >
        <Show when={focusedThreadId() === null}>
          <Sidebar
            spaces={spaces()?.items ?? []}
            spacesLoading={spaces.loading}
            selectedSpaceId={selectedSpaceId()}
            onSelectSpace={(spaceId) => {
              setSelectedSpaceId(spaceId);
              setSelectedChannelId(null);
              setChannelPickerOpen(true);
            }}
            onOpenCreateSpace={() => setShowCreateSpace(true)}
            channels={channelsForSelectedSpace()}
            channelsLoading={channels.loading}
            selectedChannelId={selectedChannelId()}
            onSelectChannel={(channel) => {
              setSelectedSpaceId(channel.space_id);
              setSelectedChannelId(channel.id);
              setChannelPickerOpen(false);
            }}
            onOpenCreateChannel={openCreateChannel}
            onLogout={logout}
          />
        </Show>

        <Show when={focusedThreadId() === null}>
          <MobileSidebar
            open={mobileSidebarOpen()}
            onClose={() => setMobileSidebarOpen(false)}
            spaces={spaces()?.items ?? []}
            selectedSpaceId={selectedSpaceId()}
            onSelectSpace={(spaceId) => {
              setSelectedSpaceId(spaceId);
              setSelectedChannelId(null);
              setChannelPickerOpen(true);
            }}
            onOpenCreateSpace={() => setShowCreateSpace(true)}
            channels={channelsForSelectedSpace()}
            selectedChannelId={selectedChannelId()}
            onSelectChannel={(channel) => {
              setSelectedSpaceId(channel.space_id);
              setSelectedChannelId(channel.id);
              setChannelPickerOpen(false);
              setMobileSidebarOpen(false);
            }}
            onOpenCreateChannel={openCreateChannel}
            onLogout={logout}
          />
        </Show>

        <main class="glass glass-surface overflow-hidden">
          <ChatHeader
            title={focusedThreadId() === null ? (selectedChannelId() === null ? "Выбор канала" : "Канал") : "Тред"}
            subtitle={`Канал: ${selectedChannel()?.name ?? selectedChannelId() ?? "—"}${focusedThreadId() !== null ? ` • thread_id: ${focusedThreadId()}` : ""}`}
            showMobileMenuButton={focusedThreadId() === null}
            onOpenMobileMenu={() => setMobileSidebarOpen(true)}
            canOpenThreadDrawer={threadIdsInChannel().length > 0}
            onOpenThreadDrawer={() => setThreadDrawerOpen(true)}
            showBackButton={focusedThreadId() !== null}
            onBack={() => setFocusedThreadId(null)}
          />

          <Show when={selectedChannelId() === null}>
            <ChannelPickerGrid
              channels={channelsForSelectedSpace()}
              loading={channels.loading}
              onPick={(channel) => {
                setSelectedSpaceId(channel.space_id);
                setSelectedChannelId(channel.id);
                setChannelPickerOpen(false);
              }}
            />
          </Show>

          <Show when={selectedChannelId() !== null}>
            <MessageList
              loading={messages.loading}
              messages={displayMessages()}
              focusedThreadId={focusedThreadId()}
              currentUserId={currentUserId()}
              MessageBubble={MessageBubble}
              onFocusThread={(tid) => setFocusedThreadId(tid)}
            />

            <Composer
              composerText={composerText()}
              onComposerText={(next) => setComposerText(next)}
              emojiOpen={emojiOpen()}
              setEmojiOpen={(next) => setEmojiOpen(next)}
              onInsertEmoji={(em) => insertEmoji(em)}
              onSendText={() => void sendTextMessage()}
              onPickImage={onPickImage}
              setFileInputRef={(el) => {
                fileInputRef = el;
              }}
              PaperclipIcon={PaperclipIcon}
              EmojiIcon={EmojiIcon}
              SendIcon={SendIcon}
              focusedThreadId={focusedThreadId()}
            />
          </Show>
        </main>
      </div>

      <Show when={focusedThreadId() === null && threadDrawerOpen()}>
        <div class="fixed inset-0 z-40 bg-black/40" onClick={() => setThreadDrawerOpen(false)} />
      </Show>
      <Show when={focusedThreadId() === null && threadDrawerOpen()}>
        <aside class="fixed right-4 top-4 z-50 w-[min(420px,calc(100%-32px))] glass glass-surface overflow-hidden">
          <div class="flex items-center justify-between px-4 py-3">
            <div class="text-sm font-semibold tracking-tight">Треды</div>
            <button class="btn px-3 py-1 text-xs" type="button" onClick={() => setThreadDrawerOpen(false)}>
              Закрыть
            </button>
          </div>
          <div class="border-t border-white/10 px-4 py-4">
            <Show when={threadIdsInChannel().length === 0}>
              <div class="text-sm muted">Тредов пока нет.</div>
            </Show>
            <div class="space-y-2">
              <For each={threadIdsInChannel()}>
                {(tid) => (
                  <button
                    class="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left text-sm hover:bg-white/10"
                    type="button"
                    onClick={() => {
                      setFocusedThreadId(tid);
                      setThreadDrawerOpen(false);
                    }}
                  >
                    {tid}
                  </button>
                )}
              </For>
            </div>
          </div>
        </aside>
      </Show>

      <Show when={showCreateSpace()}>
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
          <div class="glass glass-surface w-full max-w-md p-5">
            <div class="text-sm font-semibold tracking-tight">Создать пространство</div>
            <div class="mt-4 space-y-3">
              <label class="block">
                <div class="label">Название</div>
                <input class="input mt-1" value={newSpaceName()} onInput={(e) => setNewSpaceName(e.currentTarget.value)} />
              </label>
              <label class="block">
                <div class="label">Описание (опционально)</div>
                <input
                  class="input mt-1"
                  value={newSpaceDescription()}
                  onInput={(e) => setNewSpaceDescription(e.currentTarget.value)}
                />
              </label>
            </div>
            <div class="mt-5 flex justify-end gap-2">
              <button class="btn" type="button" onClick={() => setShowCreateSpace(false)}>
                Отмена
              </button>
              <button class="btn btn-primary" type="button" disabled={creating()} onClick={createSpace}>
                Создать
              </button>
            </div>
          </div>
        </div>
      </Show>

      <Show when={showCreateChannel()}>
        <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6">
          <div class="glass glass-surface w-full max-w-md p-5">
            <div class="text-sm font-semibold tracking-tight">Создать канал</div>
            <div class="mt-4 space-y-3">
              <div class="text-xs text-slate-200/60">
                Пространство: {selectedSpaceId() ?? "— (выбери пространство слева)"}
              </div>
              <label class="block">
                <div class="label">Название</div>
                <input class="input mt-1" value={newChannelName()} onInput={(e) => setNewChannelName(e.currentTarget.value)} />
              </label>
              <Show when={createChannelError() !== null}>
                <div class="rounded-xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-100">
                  {createChannelError()}
                </div>
              </Show>
            </div>
            <div class="mt-5 flex justify-end gap-2">
              <button class="btn" type="button" onClick={() => setShowCreateChannel(false)}>
                Отмена
              </button>
              <button class="btn btn-primary" type="button" disabled={creating()} onClick={createChannel}>
                Создать
              </button>
            </div>
          </div>
        </div>
      </Show>
    </div>
  );
}

function PaperclipIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M12.5 6.5L6.4 12.6a4 4 0 105.7 5.7l7.1-7.1a6 6 0 10-8.5-8.5l-7.1 7.1"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  );
}

function EmojiIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M12 22a10 10 0 110-20 10 10 0 010 20z"
        stroke="currentColor"
        stroke-width="1.8"
      />
      <path
        d="M8.5 10.2h.01M15.5 10.2h.01"
        stroke="currentColor"
        stroke-width="2.6"
        stroke-linecap="round"
      />
      <path
        d="M8.2 14.2c1.1 1.3 2.4 2 3.8 2s2.7-.7 3.8-2"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
      <path
        d="M21.2 3.6L10.1 14.7"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        d="M21.2 3.6l-7.2 19.2-3.3-7.7-7.7-3.3 18.2-8.2z"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  );
}

