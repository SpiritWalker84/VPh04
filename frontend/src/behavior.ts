/**
 * Метрики лендинга: клики, последняя позиция курсора, время на странице.
 * Отправка на бэкенд каждую секунду (без привязки к application_id).
 */

const STORAGE_KEY_VISITS = "vph04:landing:visit_count";
const MAX_CLICK_KEY_LEN = 120;

export type ClickEvent = { t: number; tag: string; id?: string; text?: string };

export class BehaviorCollector {
  private readonly startedAt = performance.now();
  private readonly returnVisits: number;
  private readonly clicks: ClickEvent[] = [];
  /** Счётчики нажатий по ключу (id элемента или tag+текст). */
  private readonly clickCounts = new Map<string, number>();
  private lastCursor = { x: 0, y: 0 };
  private moveHandler: ((e: MouseEvent) => void) | null = null;
  private clickHandler: ((e: MouseEvent) => void) | null = null;
  private flushTimer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    const prev = BehaviorCollector.readVisitCount();
    this.returnVisits = Math.max(0, prev);
    BehaviorCollector.writeVisitCount(prev + 1);
  }

  start(root: HTMLElement = document.body): void {
    this.clickHandler = (e: MouseEvent) => this.onClick(e);
    root.addEventListener("click", this.clickHandler, { capture: true });

    this.moveHandler = (e: MouseEvent) => this.onMove(e);
    root.addEventListener("mousemove", this.moveHandler, { passive: true, capture: true });
  }

  stop(root: HTMLElement = document.body): void {
    if (this.clickHandler) root.removeEventListener("click", this.clickHandler, { capture: true });
    if (this.moveHandler) root.removeEventListener("mousemove", this.moveHandler, { capture: true });
    this.clickHandler = null;
    this.moveHandler = null;
    this.stopPeriodicFlush();
  }

  /** Раз в `intervalMs` вызывает sender с накопленным снимком (ошибки игнорируются). */
  startPeriodicFlush(sender: () => Promise<void>, intervalMs = 1000): void {
    this.stopPeriodicFlush();
    this.flushTimer = setInterval(() => {
      void sender().catch((err) => console.warn("behavior flush", err));
    }, intervalMs);
  }

  stopPeriodicFlush(): void {
    if (this.flushTimer !== null) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  getElapsedSeconds(): number {
    return Math.max(0, Math.round((performance.now() - this.startedAt) / 1000));
  }

  getReturnVisits(): number {
    return this.returnVisits;
  }

  /**
   * JSON-строка последней позиции курсора (раз в секунду одна точка для хитмапа).
   */
  getLastCursorJson(): string {
    return JSON.stringify({ x: this.lastCursor.x, y: this.lastCursor.y });
  }

  /** JSON-строка: объект { ключ_кнопки: число_кликов }. */
  getButtonsClickedJson(): string {
    return JSON.stringify(Object.fromEntries(this.clickCounts));
  }

  /** Снимок для финальной отправки с заявкой (как раньше). */
  snapshot(): {
    time_on_page_seconds: number;
    return_visits: number;
    button_events: { events: ClickEvent[] };
    cursor_metrics: { samples: Array<{ x: number; y: number; t: number }> };
    raw_payload: Record<string, unknown>;
  } {
    return {
      time_on_page_seconds: this.getElapsedSeconds(),
      return_visits: this.returnVisits,
      button_events: { events: [...this.clicks] },
      cursor_metrics: {
        samples: [{ x: this.lastCursor.x, y: this.lastCursor.y, t: this.getElapsedSeconds() }],
      },
      raw_payload: {
        viewport: { w: globalThis.innerWidth, h: globalThis.innerHeight },
        dpr: globalThis.devicePixelRatio ?? 1,
        lang: navigator.language,
      },
    };
  }

  private static readVisitCount(): number {
    try {
      const raw = globalThis.localStorage?.getItem(STORAGE_KEY_VISITS);
      if (!raw) return 0;
      const n = Number.parseInt(raw, 10);
      return Number.isFinite(n) ? n : 0;
    } catch {
      return 0;
    }
  }

  private static writeVisitCount(n: number): void {
    try {
      globalThis.localStorage?.setItem(STORAGE_KEY_VISITS, String(n));
    } catch {
      /* приватный режим */
    }
  }

  private clickKey(el: Element): string {
    if (el instanceof HTMLElement && el.id) return `#${el.id}`;
    const tag = el instanceof HTMLElement ? el.tagName.toLowerCase() : "node";
    const t = (el.textContent ?? "").trim().slice(0, 48);
    return t ? `${tag}:${t}` : tag;
  }

  private onClick(e: MouseEvent): void {
    if (this.clicks.length < 500) {
      const target = e.target;
      if (!(target instanceof Element)) return;
      const interactive = target.closest("button,a,input,select,textarea,[data-track='1']");
      const el = interactive ?? target;
      this.clicks.push({
        t: Math.round(performance.now() - this.startedAt),
        tag: el instanceof HTMLElement ? el.tagName.toLowerCase() : "node",
        id: el instanceof HTMLElement && el.id ? el.id : undefined,
        text: el.textContent?.trim().slice(0, 80) || undefined,
      });
    }
    const target = e.target;
    if (!(target instanceof Element)) return;
    const interactive = target.closest("button,a,[data-track='1']");
    const el = interactive ?? target;
    const key = this.clickKey(el).slice(0, MAX_CLICK_KEY_LEN);
    this.clickCounts.set(key, (this.clickCounts.get(key) ?? 0) + 1);
  }

  private onMove(e: MouseEvent): void {
    this.lastCursor = { x: Math.round(e.clientX), y: Math.round(e.clientY) };
  }
}
