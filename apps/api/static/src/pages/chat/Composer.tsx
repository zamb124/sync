import { For, Show } from "solid-js";

export function Composer(props: {
  composerText: string;
  onComposerText: (next: string) => void;
  emojiOpen: boolean;
  setEmojiOpen: (next: boolean) => void;
  onInsertEmoji: (em: string) => void;
  onSendText: () => void;
  onPickImage: (e: Event) => void;
  setFileInputRef: (el: HTMLInputElement) => void;
  PaperclipIcon: () => any;
  EmojiIcon: () => any;
  SendIcon: () => any;
  focusedThreadId: string | null;
}) {
  return (
    <div class="border-t border-white/10 p-3">
      <div class="relative">
        <div class="flex items-center gap-2">
          <button
            class="btn h-11 w-11 p-0"
            type="button"
            onClick={() => (document.getElementById("composer-file-input") as HTMLInputElement | null)?.click()}
            title="Прикрепить изображение"
          >
            <props.PaperclipIcon />
          </button>
          <input
            id="composer-file-input"
            ref={(el) => props.setFileInputRef(el)}
            class="hidden"
            type="file"
            accept="image/*"
            onChange={props.onPickImage}
          />

          <textarea
            class="input min-h-[44px] resize-none"
            rows={1}
            placeholder="Сообщение..."
            value={props.composerText}
            onInput={(e) => props.onComposerText(e.currentTarget.value)}
            onKeyDown={(e) => {
              if (e.key !== "Enter") {
                return;
              }
              if (e.shiftKey) {
                return;
              }
              e.preventDefault();
              props.onSendText();
            }}
          />

          <button
            class="btn h-11 w-11 p-0"
            type="button"
            onClick={() => props.setEmojiOpen(!props.emojiOpen)}
            title="Эмодзи"
          >
            <props.EmojiIcon />
          </button>

          <button class="btn btn-primary h-11 w-11 p-0" type="button" onClick={props.onSendText} title="Отправить">
            <props.SendIcon />
          </button>
        </div>

        <Show when={props.emojiOpen}>
          <div class="absolute bottom-[56px] right-0 w-56 rounded-2xl border border-white/10 bg-black/30 p-2 backdrop-blur-2xl">
            <div class="grid grid-cols-8 gap-1 text-lg">
              <For each={["😀", "😅", "😉", "😍", "🤝", "🔥", "✅", "💡", "🧠", "🚀", "📌", "🧩", "⚠️", "❌", "👍", "👀"]}>
                {(em) => (
                  <button
                    class="rounded-xl hover:bg-white/10 active:bg-white/20"
                    type="button"
                    onClick={() => props.onInsertEmoji(em)}
                  >
                    {em}
                  </button>
                )}
              </For>
            </div>
          </div>
        </Show>
      </div>
      <Show when={props.focusedThreadId !== null}>
        <div class="mt-2 text-xs text-slate-200/55">Фокус на тред: новые сообщения уйдут в выбранный `thread_id`.</div>
      </Show>
    </div>
  );
}

