/**
 * Background-job abstraction for emails, reminders,
 * recurring invoices, and scheduled calculations.
 */

export type JobName =
  | "send-email"
  | "send-reminder"
  | "process-recurring-invoice"
  | "run-scheduled-calculation"
  | "generate-report"
  | "process-import"
  | "process-export"
  | "deliver-webhook"
  | "retry-email";

export type JobPayload = Record<string, unknown>;

export type Job<T extends JobPayload = JobPayload> = {
  id: string;
  name: JobName;
  payload: T;
  runAt?: Date;
  attempts: number;
  maxAttempts: number;
};

export type JobHandler<T extends JobPayload = JobPayload> = (
  job: Job<T>,
) => Promise<void>;

export interface JobQueue {
  enqueue<T extends JobPayload>(
    name: JobName,
    payload: T,
    options?: { runAt?: Date; maxAttempts?: number },
  ): Promise<Job<T>>;
  process<T extends JobPayload>(name: JobName, handler: JobHandler<T>): void;
  start(): Promise<void>;
  stop(): Promise<void>;
}

type RegisteredHandler = {
  name: JobName;
  handler: JobHandler;
};

/**
 * In-memory job queue for local development.
 * Swap for BullMQ / Agenda / cloud queue in production.
 */
export class InMemoryJobQueue implements JobQueue {
  private handlers: RegisteredHandler[] = [];
  private jobs: Job[] = [];
  private running = false;
  private timer: ReturnType<typeof setInterval> | null = null;

  async enqueue<T extends JobPayload>(
    name: JobName,
    payload: T,
    options?: { runAt?: Date; maxAttempts?: number },
  ): Promise<Job<T>> {
    const job: Job<T> = {
      id: crypto.randomUUID(),
      name,
      payload,
      runAt: options?.runAt,
      attempts: 0,
      maxAttempts: options?.maxAttempts ?? 3,
    };
    this.jobs.push(job as Job);
    return job;
  }

  process<T extends JobPayload>(name: JobName, handler: JobHandler<T>): void {
    this.handlers.push({ name, handler: handler as JobHandler });
  }

  async start(): Promise<void> {
    if (this.running) return;
    this.running = true;
    this.timer = setInterval(() => {
      void this.tick();
    }, 1000);
  }

  async stop(): Promise<void> {
    this.running = false;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  private async tick(): Promise<void> {
    const now = Date.now();
    const due = this.jobs.filter(
      (job) => !job.runAt || job.runAt.getTime() <= now,
    );

    for (const job of due) {
      const registered = this.handlers.find((h) => h.name === job.name);
      if (!registered) continue;

      this.jobs = this.jobs.filter((j) => j.id !== job.id);
      job.attempts += 1;

      try {
        await registered.handler(job);
      } catch (error) {
        if (job.attempts < job.maxAttempts) {
          this.jobs.push(job);
        }
        console.error(`[jobs] Failed job ${job.name} (${job.id})`, error);
      }
    }
  }
}

let queue: JobQueue | null = null;

export function getJobQueue(): JobQueue {
  if (!queue) {
    queue = new InMemoryJobQueue();
  }
  return queue;
}
