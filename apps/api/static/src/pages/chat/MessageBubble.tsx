import { createSignal, For, Show } from "solid-js";
import type { MessageRead } from "../../shared/dto";

type UiMessage = Omit<MessageRead, "status"> & { status: MessageRead["status"] | "pending" };

function toShortUsername(displayName: string): string {
  const raw = displayName.trim();
  if (raw === "") {
    return "Пользователь";
  }
  const parts = raw.split(/\s+/g).filter((p) => p.trim() !== "");
  const nonEmail = parts.filter((p) => !p.includes("@"));
  if (nonEmail.length > 0) {
    return nonEmail.join(" ");
  }
  const first = parts[0] ?? raw;
  if (first.includes("@")) {
    return first.split("@")[0] || first;
  }
  return raw;
}

function UserInfoModal(props: {
  open: boolean;
  onClose: () => void;
  sender: { id: string; display_name: string; avatar_url: string | null };
}) {
  return (
    <Show when={props.open}>
      <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6" onClick={props.onClose}>
        <div class="glass glass-surface w-full max-w-md p-5" onClick={(e) => e.stopPropagation()}>
          <div class="flex items-center justify-between gap-3">
            <div class="text-sm font-semibold tracking-tight">Профиль</div>
            <button class="btn px-3 py-1 text-xs" type="button" onClick={props.onClose}>
              Закрыть
            </button>
          </div>
          <div class="mt-4 space-y-3 text-sm">
            <div>
              <div class="label">Username</div>
              <div class="mt-1">{toShortUsername(props.sender.display_name)}</div>
            </div>
            <div>
              <div class="label">display_name</div>
              <div class="mt-1 break-all text-slate-100/90">{props.sender.display_name}</div>
            </div>
            <div>
              <div class="label">user_id</div>
              <div class="mt-1 break-all text-slate-100/90">{props.sender.id}</div>
            </div>
            <Show when={props.sender.avatar_url !== null}>
              <div>
                <div class="label">avatar_url</div>
                <div class="mt-1 break-all text-slate-100/90">{props.sender.avatar_url}</div>
              </div>
            </Show>
          </div>
        </div>
      </div>
    </Show>
  );
}

function MessageContentView(props: { content: MessageRead["contents"][number] }) {
  const { content } = props;
  if (content.type === "text/plain") {
    const body = content.data["body"];
    if (typeof body !== "string") {
      throw new Error("Некорректный text/plain контент.");
    }
    return <div class="whitespace-pre-wrap text-[15px] text-slate-100 leading-relaxed">{body}</div>;
  }
  if (content.type === "code/block") {
    const language = content.data["language"];
    const source = content.data["source"];
    if (typeof language !== "string" || typeof source !== "string") {
      throw new Error("Некорректный code/block контент.");
    }
    return (
      <div class="rounded-2xl border border-white/10 bg-black/20 px-3 py-2 backdrop-blur-xl">
        <div class="text-xs text-slate-200/55">{language}</div>
        <pre class="mt-2 overflow-auto text-xs text-slate-100/90">
          <code>{source}</code>
        </pre>
      </div>
    );
  }
  if (content.type === "mock/image") {
    const fileId = content.data["file_id"];
    if (typeof fileId !== "string") {
      throw new Error("Некорректный mock/image контент.");
    }
    return <div class="text-[15px] text-slate-200/85">Изображение: {fileId}</div>;
  }
  if (content.type === "git/reference") {
    const gitRefId = content.data["git_ref_id"];
    if (typeof gitRefId !== "string") {
      throw new Error("Некорректный git/reference контент.");
    }
    return <div class="text-[15px] text-slate-200/85">Git: {gitRefId}</div>;
  }
  if (content.type === "custom_tool_response") {
    const toolName = content.data["tool_name"];
    if (typeof toolName !== "string") {
      throw new Error("Некорректный custom_tool_response контент.");
    }
    return <div class="text-[15px] text-slate-200/85">Tool: {toolName}</div>;
  }
  throw new Error("Неподдерживаемый тип контента.");
}

export function MessageBubble(props: {
  msg: UiMessage;
  isOwn: boolean;
  canFocusThread: boolean;
  onFocusThread: () => void;
}) {
  const { msg } = props;
  const [userModalOpen, setUserModalOpen] = createSignal(false);
  return (
    <div class={"flex " + (props.isOwn ? "justify-end" : "justify-start")}>
      <div
        class={
          "max-w-[min(720px,90%)] rounded-2xl px-4 py-3 " +
          (props.isOwn ? "border border-sky-400/20 bg-sky-500/15" : "border border-white/10 bg-white/5")
        }
      >
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <Show when={!props.isOwn}>
              <button
                type="button"
                class="text-sm font-medium text-slate-100 hover:underline underline-offset-4"
                onClick={() => setUserModalOpen(true)}
                title="Открыть профиль"
              >
                {toShortUsername(msg.sender.display_name)}
              </button>
            </Show>
            <div class="text-xs text-slate-200/50">
              {msg.status === "pending" ? "Отправка..." : new Date(msg.sent_at).toLocaleString()}
            </div>
          </div>
          <Show when={props.canFocusThread}>
            <button class="btn px-3 py-1 text-xs" type="button" onClick={props.onFocusThread}>
              Тред
            </button>
          </Show>
        </div>
        <div class="mt-3 space-y-2">
          <For each={[...msg.contents].sort((a, b) => a.order - b.order)}>
            {(content) => <MessageContentView content={content} />}
          </For>
        </div>
      </div>
      <UserInfoModal
        open={userModalOpen()}
        onClose={() => setUserModalOpen(false)}
        sender={msg.sender}
      />
    </div>
  );
}

