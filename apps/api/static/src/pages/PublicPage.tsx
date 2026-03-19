import { useNavigate } from "@solidjs/router";
import { createEffect } from "solid-js";
import { getAuthToken } from "../shared/auth";

export function PublicPage() {
  const navigate = useNavigate();

  createEffect(() => {
    if (getAuthToken() !== null) {
      navigate("/chat", { replace: true });
    }
  });

  return (
    <div class="h-full flex items-center justify-center p-6">
      <div class="glass glass-surface w-full max-w-lg p-6">
        <div class="flex items-center justify-between">
          <div class="text-xl font-semibold tracking-tight">Sync</div>
          <div class="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200/80">
            Preview
          </div>
        </div>
        <div class="mt-3 text-sm muted">
          Инженерный чат: пространства, каналы, треды, полиморфные сообщения и GitLab‑интеграции.
        </div>
        <div class="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <button class="btn btn-primary" onClick={() => navigate("/auth")}>
            Войти
          </button>
          <button class="btn" onClick={() => navigate("/auth")}>
            Создать аккаунт
          </button>
        </div>
        <div class="mt-6 text-xs text-slate-200/55">
          UI в стиле Liquid Glass: стекло, глубина, мягкий контраст.
        </div>
      </div>
    </div>
  );
}

