import { useNavigate } from "@solidjs/router";
import { createSignal } from "solid-js";
import { apiFetch, ApiError } from "../shared/api";
import { setAuthToken } from "../shared/auth";
import type { LoginResponse, RegisterRequest } from "../shared/dto";

export function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = createSignal<"login" | "register">("login");

  const [login, setLogin] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [email, setEmail] = createSignal("");
  const [username, setUsername] = createSignal("");
  const [firstName, setFirstName] = createSignal("");
  const [lastName, setLastName] = createSignal("");
  const [displayName, setDisplayName] = createSignal("");
  const [error, setError] = createSignal<string | null>(null);
  const [submitting, setSubmitting] = createSignal(false);

  async function onSubmit(e: Event) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res =
        mode() === "login"
          ? await apiFetch<LoginResponse>("/api/auth/login", {
              method: "POST",
              body: JSON.stringify({ login: login(), password: password() }),
            })
          : await apiFetch<LoginResponse>("/api/auth/register", {
              method: "POST",
              body: JSON.stringify(buildRegisterRequest()),
            });
      if (res.token_type.toLowerCase() !== "bearer") {
        throw new Error("Неожиданный token_type.");
      }
      setAuthToken(res.access_token);
      navigate("/chat", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Неверный логин или пароль.");
      } else if (err instanceof ApiError && err.status === 409) {
        setError("Пользователь с таким email или username уже существует.");
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Неизвестная ошибка.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  function buildRegisterRequest(): RegisterRequest {
    const dn = displayName().trim();
    const finalDisplayName = dn !== "" ? dn : `${firstName().trim()} ${lastName().trim()}`.trim();
    if (finalDisplayName === "") {
      throw new Error("display_name обязателен.");
    }
    return {
      email: email().trim(),
      username: username().trim(),
      first_name: firstName().trim(),
      last_name: lastName().trim(),
      display_name: finalDisplayName,
      password: password(),
    };
  }

  return (
    <div class="h-full flex items-center justify-center p-6">
      <form
        class="glass glass-surface w-full max-w-md p-6"
        onSubmit={onSubmit}
      >
        <div class="flex items-center justify-between">
          <div class="text-xl font-semibold">{mode() === "login" ? "Вход" : "Регистрация"}</div>
          <button
            class="btn px-3 py-1 text-xs"
            type="button"
            onClick={() => {
              setError(null);
              setMode(mode() === "login" ? "register" : "login");
            }}
          >
            {mode() === "login" ? "Регистрация" : "Вход"}
          </button>
        </div>
        <div class="mt-4 space-y-3">
          {mode() === "register" && (
            <>
              <label class="block">
                <div class="label">Email</div>
                <input
                  class="input mt-1"
                  value={email()}
                  onInput={(e) => setEmail(e.currentTarget.value)}
                  autocomplete="email"
                  required
                />
              </label>
              <label class="block">
                <div class="label">Username</div>
                <input
                  class="input mt-1"
                  value={username()}
                  onInput={(e) => setUsername(e.currentTarget.value)}
                  autocomplete="username"
                  required
                />
              </label>
              <div class="grid grid-cols-2 gap-3">
                <label class="block">
                  <div class="label">Имя</div>
                  <input
                    class="input mt-1"
                    value={firstName()}
                    onInput={(e) => setFirstName(e.currentTarget.value)}
                    required
                  />
                </label>
                <label class="block">
                  <div class="label">Фамилия</div>
                  <input
                    class="input mt-1"
                    value={lastName()}
                    onInput={(e) => setLastName(e.currentTarget.value)}
                    required
                  />
                </label>
              </div>
              <label class="block">
                <div class="label">Display name (опционально)</div>
                <input
                  class="input mt-1"
                  value={displayName()}
                  onInput={(e) => setDisplayName(e.currentTarget.value)}
                />
              </label>
            </>
          )}
          {mode() === "login" && (
            <label class="block">
              <div class="label">Логин (email или username)</div>
              <input
                class="input mt-1"
                value={login()}
                onInput={(e) => setLogin(e.currentTarget.value)}
                autocomplete="username"
                required
              />
            </label>
          )}
          <label class="block">
            <div class="label">Пароль</div>
            <input
              class="input mt-1"
              type="password"
              value={password()}
              onInput={(e) => setPassword(e.currentTarget.value)}
              autocomplete="current-password"
              required
            />
          </label>
        </div>
        {error() && (
          <div class="mt-4 rounded-xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-100">
            {error()}
          </div>
        )}
        <button
          class="btn btn-primary mt-6 w-full disabled:opacity-50"
          type="submit"
          disabled={submitting()}
        >
          {submitting()
            ? mode() === "login"
              ? "Входим..."
              : "Создаём аккаунт..."
            : mode() === "login"
              ? "Войти"
              : "Зарегистрироваться"}
        </button>
      </form>
    </div>
  );
}

