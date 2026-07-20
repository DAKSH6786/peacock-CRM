export type MyWorkItem = {
  id: string;
  title: string;
  meta?: string;
  href: string;
};

export type MyWorkPayload = {
  tasks: MyWorkItem[];
  deliverables: MyWorkItem[];
  leadFollowUps: MyWorkItem[];
  approvals: MyWorkItem[];
  xymeGoals: MyWorkItem[];
  checkInReminders: MyWorkItem[];
  attendanceExceptions: MyWorkItem[];
  announcements: MyWorkItem[];
};
