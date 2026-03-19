import { For, Show } from "solid-js";
import type { ChannelRead, SpaceRead } from "../../shared/dto";

export function Sidebar(props: {
  spaces: SpaceRead[];
  spacesLoading: boolean;
  selectedSpaceId: string | null;
  onSelectSpace: (spaceId: string) => void;
  onOpenCreateSpace: () => void;

  channels: ChannelRead[];
  channelsLoading: boolean;
  selectedChannelId: string | null;
  onSelectChannel: (channel: ChannelRead) => void;
  onOpenCreateChannel: () => void;

  onLogout: () => void;
}) {
  return (
    <aside class="glass glass-surface overflow-hidden hidden lg:block">
      <div class="flex items-center justify-between px-4 py-3">
        <div class="text-sm font-semibold tracking-tight">Sync</div>
        <button class="btn px-3 py-1 text-xs" onClick={props.onLogout} type="button">
          Выйти
        </button>
      </div>

      <div class="px-4 pb-4">
        <div class="flex items-center justify-between">
          <div class="label">Пространства</div>
          <button class="btn px-3 py-1 text-xs" type="button" onClick={props.onOpenCreateSpace}>
            + Space
          </button>
        </div>
        <div class="mt-2 space-y-1 max-h-[50vh] overflow-auto pr-1">
          <Show when={props.spacesLoading}>
            <div class="text-sm muted">Загрузка...</div>
          </Show>
          <For each={props.spaces}>
            {(space) => (
              <button
                class={
                  "w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-white/8 " +
                  (space.id === props.selectedSpaceId ? "bg-white/10" : "bg-transparent")
                }
                onClick={() => props.onSelectSpace(space.id)}
                type="button"
              >
                {space.name}
              </button>
            )}
          </For>
        </div>
      </div>

      <div class="border-t border-white/10 px-4 py-4">
        <div class="flex items-center justify-between">
          <div class="label">Каналы</div>
          <button class="btn px-3 py-1 text-xs" type="button" onClick={props.onOpenCreateChannel}>
            + Channel
          </button>
        </div>
        <div class="mt-2 space-y-1">
          <Show when={props.channelsLoading}>
            <div class="text-sm muted">Загрузка...</div>
          </Show>
          <For each={props.channels}>
            {(channel) => (
              <button
                class={
                  "w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-white/8 " +
                  (channel.id === props.selectedChannelId ? "bg-white/10" : "bg-transparent")
                }
                onClick={() => props.onSelectChannel(channel)}
                type="button"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="truncate">{channel.name ?? channel.id}</div>
                  <div class="text-[10px] text-slate-200/50">{channel.type}</div>
                </div>
              </button>
            )}
          </For>
        </div>
      </div>
    </aside>
  );
}

export function MobileSidebar(props: {
  open: boolean;
  onClose: () => void;
  spaces: SpaceRead[];
  selectedSpaceId: string | null;
  onSelectSpace: (spaceId: string) => void;
  onOpenCreateSpace: () => void;
  channels: ChannelRead[];
  selectedChannelId: string | null;
  onSelectChannel: (channel: ChannelRead) => void;
  onOpenCreateChannel: () => void;
  onLogout: () => void;
}) {
  return (
    <>
      <Show when={props.open}>
        <div class="fixed inset-0 z-40 bg-black/40 lg:hidden" onClick={props.onClose} />
      </Show>
      <Show when={props.open}>
        <aside class="fixed left-4 right-4 top-4 z-50 max-h-[calc(100%-32px)] overflow-auto glass glass-surface lg:hidden">
          <div class="flex items-center justify-between px-4 py-3">
            <div class="text-sm font-semibold tracking-tight">Sync</div>
            <button class="btn px-3 py-1 text-xs" onClick={props.onClose} type="button">
              Закрыть
            </button>
          </div>

          <div class="px-4 pb-4">
            <div class="flex items-center justify-between">
              <div class="label">Пространства</div>
              <button class="btn px-3 py-1 text-xs" type="button" onClick={props.onOpenCreateSpace}>
                + Space
              </button>
            </div>
            <div class="mt-2 space-y-1 max-h-[50vh] overflow-auto pr-1">
              <For each={props.spaces}>
                {(space) => (
                  <button
                    class={
                      "w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-white/8 " +
                      (space.id === props.selectedSpaceId ? "bg-white/10" : "bg-transparent")
                    }
                    onClick={() => props.onSelectSpace(space.id)}
                    type="button"
                  >
                    {space.name}
                  </button>
                )}
              </For>
            </div>
          </div>

          <div class="border-t border-white/10 px-4 py-4">
            <div class="flex items-center justify-between">
              <div class="label">Каналы</div>
              <button class="btn px-3 py-1 text-xs" type="button" onClick={props.onOpenCreateChannel}>
                + Channel
              </button>
            </div>
            <div class="mt-2 space-y-1">
              <For each={props.channels}>
                {(channel) => (
                  <button
                    class={
                      "w-full rounded-xl px-3 py-2 text-left text-sm hover:bg-white/8 " +
                      (channel.id === props.selectedChannelId ? "bg-white/10" : "bg-transparent")
                    }
                    onClick={() => props.onSelectChannel(channel)}
                    type="button"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <div class="truncate">{channel.name ?? channel.id}</div>
                      <div class="text-[10px] text-slate-200/50">{channel.type}</div>
                    </div>
                  </button>
                )}
              </For>
            </div>
          </div>

          <div class="border-t border-white/10 px-4 py-4">
            <button class="btn w-full" onClick={props.onLogout} type="button">
              Выйти
            </button>
          </div>
        </aside>
      </Show>
    </>
  );
}

