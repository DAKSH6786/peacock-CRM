"use client";

import { notifyBrowserStorage } from "@/lib/browser-storage-store";

export type RecentRecord = {
  id: string;
  title: string;
  subtitle?: string;
  href: string;
  category?: string;
  viewedAt: number;
};

const RECENT_SEARCHES_KEY = "peacock:recent-searches";
const RECENTLY_VIEWED_KEY = "peacock:recently-viewed";
const MAX_ITEMS = 8;

function readJson<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function writeJson(key: string, value: unknown) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
    notifyBrowserStorage();
  } catch {
    // Ignore quota / private mode failures.
  }
}

export function getRecentSearches(): string[] {
  return readJson<string[]>(RECENT_SEARCHES_KEY, []);
}

export function pushRecentSearch(query: string) {
  const trimmed = query.trim();
  if (trimmed.length < 2) return;
  const next = [
    trimmed,
    ...getRecentSearches().filter(
      (item) => item.toLowerCase() !== trimmed.toLowerCase(),
    ),
  ].slice(0, MAX_ITEMS);
  writeJson(RECENT_SEARCHES_KEY, next);
}

export function getRecentlyViewed(): RecentRecord[] {
  return readJson<RecentRecord[]>(RECENTLY_VIEWED_KEY, []);
}

export function pushRecentlyViewed(
  record: Omit<RecentRecord, "viewedAt"> & { viewedAt?: number },
) {
  const entry: RecentRecord = {
    ...record,
    viewedAt: record.viewedAt ?? Date.now(),
  };
  const next = [
    entry,
    ...getRecentlyViewed().filter(
      (item) => !(item.id === entry.id && item.href === entry.href),
    ),
  ].slice(0, MAX_ITEMS);
  writeJson(RECENTLY_VIEWED_KEY, next);
}
