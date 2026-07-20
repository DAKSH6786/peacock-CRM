/**
 * Calendar integration abstraction.
 *
 * Providers: Google Calendar, Microsoft Outlook Calendar.
 * Sync targets (future): CRM meetings, interviews, leave, project deadlines, follow-ups.
 *
 * Do not claim synchronization works until credentials are configured
 * and an integration test succeeds.
 */

export type CalendarProviderKind = "google" | "microsoft";

export type CalendarEventInput = {
  title: string;
  description?: string;
  startsAt: Date;
  endsAt: Date;
  timezone?: string;
  attendees?: string[];
  entityType:
    | "crm_meeting"
    | "interview"
    | "leave"
    | "project_deadline"
    | "follow_up";
  entityId: string;
};

export type CalendarSyncResult = {
  ok: boolean;
  provider: CalendarProviderKind;
  externalEventId?: string;
  status: "SYNCED" | "PENDING" | "FAILED" | "DISCONNECTED";
  errorMessage?: string;
};

export interface CalendarProvider {
  readonly name: CalendarProviderKind;
  isConfigured(): boolean;
  upsertEvent(input: CalendarEventInput): Promise<CalendarSyncResult>;
  deleteEvent(externalEventId: string): Promise<CalendarSyncResult>;
}

export class UnconfiguredCalendarProvider implements CalendarProvider {
  constructor(public readonly name: CalendarProviderKind) {}

  isConfigured(): boolean {
    return false;
  }

  async upsertEvent(input: CalendarEventInput): Promise<CalendarSyncResult> {
    return {
      ok: false,
      provider: this.name,
      status: "DISCONNECTED",
      errorMessage: `${this.name} calendar is not configured. Store OAuth tokens in the credential vault and run an integration test before enabling sync for ${input.entityType}.`,
    };
  }

  async deleteEvent(_externalEventId: string): Promise<CalendarSyncResult> {
    return {
      ok: false,
      provider: this.name,
      status: "DISCONNECTED",
      errorMessage: `${this.name} calendar is not configured.`,
    };
  }
}

export function createCalendarProvider(
  kind: CalendarProviderKind,
): CalendarProvider {
  // Future: resolve vaultRef from CalendarConnection and return live adapter.
  return new UnconfiguredCalendarProvider(kind);
}

export function calendarSyncSupportedEntityTypes() {
  return [
    "crm_meeting",
    "interview",
    "leave",
    "project_deadline",
    "follow_up",
  ] as const;
}
