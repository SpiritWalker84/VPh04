/**
 * Сбор поведенческих метрик без тяжёлых слушателей: дебаунс, лимиты, passive где можно.
 */

const STORAGE_KEY_VISITS = "vph04:landing:visit_count";
const CURSOR_SAMPLE_MS = 400;
const MAX_CURSOR_SAMPLES = 80;
const MAX_CLICK_EVENTS = 60;

export type ClickEvent = { t: number; tag: string; id?: string; text?: string };

export class BehaviorCollector {
  private readonly startedAt = performance.now();
  /** Число завершённых визитов до текущего (для первого визита — 0). */
  private readonly returnVisits: number;
  private readonly clicks: ClickEvent[] = [];
  private cursorSamples: Array<{ t: number; x: number; y: number }> = [];
  private lastCursorSample = 0;
  private moveHandler: ((e: MouseEvent) => void) | null = null;
  private clickHandler: ((e: MouseEvent) => void) | null = null;

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
  }

  snapshot(): {
    time_on_page_seconds: number;
    return_visits: number;
    button_events: { events: ClickEvent[] };
    cursor_metrics: { samples: Array<{ t: number; x: number; y: number }> };
    raw_payload: Record<string, unknown>;
  } {
    const elapsedSec = Math.max(0, Math.round((performance.now() - this.startedAt) / 1000));
    return {
      time_on_page_seconds: elapsedSec,
      return_visits: this.returnVisits,
      button_events: { events: [...this.clicks] },
      cursor_metrics: { samples: [...this.cursorSamples] },
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

  private onClick(e: MouseEvent): void {
    if (this.clicks.length >= MAX_CLICK_EVENTS) return;
    const target = e.target;
    if (!(target instanceof Element)) return;
    const interactive = target.closest("button,a,input,select,textarea,[data-track='1']");
    const el = interactive ?? target;
    this.clicks.push({
      t: Math.round(performance.now() - this.startedAt),
      tag: el instanceof HTMLElement ? el.tagName.toLowerCase() : "node",
      id: el.id || undefined,
      text: el.textContent?.trim().slice(0, 80) || undefined,
    });
  }

  private onMove(e: MouseEvent): void {
    if (this.cursorSamples.length >= MAX_CURSOR_SAMPLES) return;
    const now = performance.now();
    if (now - this.lastCursorSample < CURSOR_SAMPLE_MS) return;
    this.lastCursorSample = now;
    this.cursorSamples.push({
      t: Math.round(now - this.startedAt),
      x: e.clientX,
      y: e.clientY,
    });
  }
}
