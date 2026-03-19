import { createEffect, For, onCleanup, Show } from "solid-js";

export function MessageList(props: {
  loading: boolean;
  messages: any[];
  focusedThreadId: string | null;
  currentUserId: string | null;
  MessageBubble: (p: any) => any;
  onFocusThread: (threadId: string) => void;
}) {
  let scrollerRef: HTMLDivElement | undefined;
  let stickToBottom = true;

  function isNearBottom(el: HTMLDivElement): boolean {
    const thresholdPx = 40;
    const distance = el.scrollHeight - (el.scrollTop + el.clientHeight);
    return distance <= thresholdPx;
  }

  function scrollToBottom(el: HTMLDivElement): void {
    el.scrollTop = el.scrollHeight;
  }

  createEffect(() => {
    // Следим за изменениями списка сообщений/фокуса треда.
    // Если пользователь уже был внизу — держим внизу при приходе новых сообщений.
    void props.messages.length;
    void props.focusedThreadId;
    if (!scrollerRef) {
      return;
    }
    if (!stickToBottom) {
      return;
    }
    const el = scrollerRef;
    const id = window.requestAnimationFrame(() => scrollToBottom(el));
    onCleanup(() => window.cancelAnimationFrame(id));
  });

  return (
    <div
      ref={(el) => {
        scrollerRef = el;
        if (scrollerRef) {
          stickToBottom = isNearBottom(scrollerRef);
        }
      }}
      class="h-[calc(100%-56px-72px)] overflow-auto px-4 pb-4"
      onScroll={(e) => {
        const el = e.currentTarget as HTMLDivElement;
        stickToBottom = isNearBottom(el);
      }}
    >
      <Show when={props.loading}>
        <div class="text-sm muted py-4">Загрузка сообщений...</div>
      </Show>
      <Show when={!props.loading && props.messages.length === 0}>
        <div class="text-sm muted py-4">Сообщений пока нет.</div>
      </Show>

      <div class="space-y-3 pt-2">
        <For
          each={props.messages.filter((m) => {
            const ft = props.focusedThreadId;
            if (ft === null) {
              return true;
            }
            return m.thread_id === ft;
          })}
        >
          {(msg) => (
            <props.MessageBubble
              msg={msg}
              isOwn={props.currentUserId !== null && msg.sender.id === props.currentUserId}
              onFocusThread={() => {
                if (msg.thread_id === null) {
                  return;
                }
                props.onFocusThread(msg.thread_id);
              }}
              canFocusThread={props.focusedThreadId === null && msg.thread_id !== null}
            />
          )}
        </For>
      </div>
    </div>
  );
}

