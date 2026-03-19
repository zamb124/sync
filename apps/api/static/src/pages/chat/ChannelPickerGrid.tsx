import { For, Show } from "solid-js";
import type { ChannelRead } from "../../shared/dto";

export function ChannelPickerGrid(props: { channels: ChannelRead[]; loading: boolean; onPick: (c: ChannelRead) => void }) {
  return (
    <div class="h-[calc(100%-56px)] overflow-auto px-4 pb-4">
      <div class="text-sm muted pt-4">Выбери канал в пространстве.</div>
      <div class="grid grid-cols-2 gap-3 pt-4 sm:grid-cols-3 lg:grid-cols-3">
        <For each={props.channels}>
          {(channel) => (
            <button
              type="button"
              class="glass glass-surface rounded-2xl p-4 text-left hover:bg-white/8"
              onClick={() => props.onPick(channel)}
            >
              <div class="text-sm font-semibold truncate">{channel.name ?? channel.id}</div>
              <div class="mt-2 text-xs text-slate-200/60 truncate">{channel.type}</div>
            </button>
          )}
        </For>
      </div>
      <Show when={!props.loading && props.channels.length === 0}>
        <div class="text-sm muted py-4">В этом пространстве пока нет каналов.</div>
      </Show>
    </div>
  );
}

