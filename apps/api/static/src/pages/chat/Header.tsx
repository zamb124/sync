import { Show } from "solid-js";

export function ChatHeader(props: {
  title: string;
  subtitle: string;
  showMobileMenuButton: boolean;
  onOpenMobileMenu: () => void;
  canOpenThreadDrawer: boolean;
  onOpenThreadDrawer: () => void;
  showBackButton: boolean;
  onBack: () => void;
}) {
  return (
    <div class="flex items-center justify-between px-4 py-3">
      <div>
        <div class="text-sm font-semibold tracking-tight">{props.title}</div>
        <div class="mt-1 text-xs text-slate-200/60">{props.subtitle}</div>
      </div>
      <div class="flex items-center gap-2">
        <Show when={props.showMobileMenuButton}>
          <button class="btn px-3 py-1 text-xs lg:hidden" type="button" onClick={props.onOpenMobileMenu}>
            Меню
          </button>
        </Show>
        <Show when={!props.showBackButton}>
          <button class="btn px-3 py-1 text-xs" type="button" onClick={props.onOpenThreadDrawer} disabled={!props.canOpenThreadDrawer}>
            Треды
          </button>
        </Show>
        <Show when={props.showBackButton}>
          <button class="btn px-3 py-1 text-xs" type="button" onClick={props.onBack}>
            Назад
          </button>
        </Show>
      </div>
    </div>
  );
}

