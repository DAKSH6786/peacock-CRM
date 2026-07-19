"use client";

import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import * as Dialog from "@radix-ui/react-dialog";
import { useEffect, useRef, useState, useTransition } from "react";

import {
  filterNavByRole,
  navigationSections,
  quickCreateItems,
} from "@/components/layout/nav-config";
import { useShell } from "@/components/layout/shell-context";
import { useBrowserStorageValue } from "@/lib/browser-storage-store";
import { HighlightMatch } from "@/lib/highlight-match";
import {
  getRecentSearches,
  getRecentlyViewed,
  pushRecentSearch,
  pushRecentlyViewed,
} from "@/lib/recent-records";
import type { SearchHit, SearchResponse } from "@/modules/search/types";
import { hasPermission } from "@/permissions/types";

export function CommandPalette({ role }: { role: string | null }) {
  const router = useRouter();
  const { commandOpen, setCommandOpen } = useShell();
  const sections = filterNavByRole(role, hasPermission);
  const creates = quickCreateItems.filter(
    (item) => !item.permission || hasPermission(role as never, item.permission),
  );

  const [query, setQuery] = useState("");
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searching, startSearch] = useTransition();
  const requestId = useRef(0);

  const recentSearches = useBrowserStorageValue(getRecentSearches, []);
  const recentlyViewed = useBrowserStorageValue(getRecentlyViewed, []);

  useEffect(() => {
    if (!commandOpen) return;
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      return;
    }

    const controller = new AbortController();
    const currentRequest = ++requestId.current;
    const timer = window.setTimeout(() => {
      startSearch(() => {
        void (async () => {
          try {
            const response = await fetch(
              `/api/search?q=${encodeURIComponent(trimmed)}`,
              { signal: controller.signal },
            );
            if (currentRequest !== requestId.current) return;
            if (!response.ok) {
              setSearchError("Search unavailable");
              setSearchResult(null);
              return;
            }
            const data = (await response.json()) as SearchResponse;
            setSearchResult(data);
            setSearchError(null);
            pushRecentSearch(trimmed);
          } catch (error) {
            if ((error as Error).name === "AbortError") return;
            if (currentRequest !== requestId.current) return;
            setSearchError("Search unavailable");
            setSearchResult(null);
          }
        })();
      });
    }, 220);

    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [query, commandOpen]);

  const go = (href: string, hit?: SearchHit) => {
    if (hit) {
      pushRecentlyViewed({
        id: hit.id,
        title: hit.title,
        subtitle: hit.subtitle,
        href: hit.href,
        category: hit.category,
      });
    }
    setCommandOpen(false);
    setQuery("");
    setSearchResult(null);
    setSearchError(null);
    router.push(href);
  };

  const handleOpenChange = (open: boolean) => {
    setCommandOpen(open);
    if (!open) {
      setQuery("");
      setSearchResult(null);
      setSearchError(null);
    }
  };

  const showRecordSearch = query.trim().length >= 2;
  const recordGroups =
    showRecordSearch && query.trim().length >= 2 ? (searchResult?.groups ?? []) : [];
  const emptyRecordState =
    showRecordSearch &&
    !searching &&
    !searchError &&
    (searchResult?.groups.length ?? 0) === 0 &&
    query.trim().length >= 2;

  return (
    <Dialog.Root open={commandOpen} onOpenChange={handleOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/55" />
        <Dialog.Content
          className="fixed top-[18%] left-1/2 z-50 w-[min(94vw,40rem)] -translate-x-1/2 overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-soft)]"
          aria-label="Command palette"
        >
          <Command
            className="text-[var(--foreground)]"
            label="Command menu"
            shouldFilter={!showRecordSearch}
          >
            <div className="border-b border-[var(--border)] px-3">
              <Command.Input
                value={query}
                onValueChange={(value) => {
                  setQuery(value);
                  if (value.trim().length < 2) {
                    setSearchResult(null);
                    setSearchError(null);
                  }
                }}
                placeholder="Search pages, actions, and authorized records… (⌘K)"
                className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
              />
            </div>
            <Command.List className="max-h-80 overflow-y-auto p-2">
              <Command.Empty className="px-3 py-8 text-center text-sm text-[var(--muted)]">
                {searching
                  ? "Searching authorized records…"
                  : searchError
                    ? searchError
                    : emptyRecordState
                      ? "No authorized records matched."
                      : "No matches found."}
              </Command.Empty>

              {!showRecordSearch && recentSearches.length > 0 ? (
                <Command.Group
                  heading="Recent searches"
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-[var(--muted)]"
                >
                  {recentSearches.map((item) => (
                    <Command.Item
                      key={`recent-search-${item}`}
                      value={`recent search ${item}`}
                      onSelect={() => setQuery(item)}
                      className="cursor-pointer rounded-xl px-3 py-2 text-sm aria-selected:bg-[var(--accent-soft)] aria-selected:text-[var(--accent-teal)]"
                    >
                      {item}
                    </Command.Item>
                  ))}
                </Command.Group>
              ) : null}

              {!showRecordSearch && recentlyViewed.length > 0 ? (
                <Command.Group
                  heading="Recently viewed"
                  className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-[var(--muted)]"
                >
                  {recentlyViewed.map((item) => (
                    <Command.Item
                      key={`recent-view-${item.id}-${item.href}`}
                      value={`recent viewed ${item.title} ${item.category ?? ""}`}
                      onSelect={() => go(item.href)}
                      className="cursor-pointer rounded-xl px-3 py-2 text-sm aria-selected:bg-[var(--accent-soft)] aria-selected:text-[var(--accent-teal)]"
                    >
                      <span className="font-medium">{item.title}</span>
                      {item.category ? (
                        <span className="ml-2 text-xs text-[var(--muted)]">
                          {item.category}
                        </span>
                      ) : null}
                    </Command.Item>
                  ))}
                </Command.Group>
              ) : null}

              {showRecordSearch
                ? recordGroups.map((group) => (
                    <Command.Group
                      key={group.category}
                      heading={group.category}
                      className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-[var(--muted)]"
                    >
                      {group.hits.map((hit) => (
                        <Command.Item
                          key={`${hit.category}-${hit.id}`}
                          value={`${hit.category} ${hit.title} ${hit.subtitle ?? ""}`}
                          onSelect={() => go(hit.href, hit)}
                          className="cursor-pointer rounded-xl px-3 py-2 text-sm aria-selected:bg-[var(--accent-soft)] aria-selected:text-[var(--accent-teal)]"
                        >
                          <div className="flex flex-col">
                            <span className="font-medium">
                              <HighlightMatch text={hit.title} query={query} />
                            </span>
                            {hit.subtitle ? (
                              <span className="text-xs text-[var(--muted)]">
                                <HighlightMatch
                                  text={hit.subtitle}
                                  query={query}
                                />
                              </span>
                            ) : null}
                          </div>
                        </Command.Item>
                      ))}
                    </Command.Group>
                  ))
                : null}

              {!showRecordSearch ? (
                <>
                  <Command.Group
                    heading="Quick create"
                    className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-[var(--muted)]"
                  >
                    {creates.map((item) => (
                      <Command.Item
                        key={item.href}
                        value={`create ${item.label}`}
                        onSelect={() => go(item.href)}
                        className="cursor-pointer rounded-xl px-3 py-2 text-sm aria-selected:bg-[var(--accent-soft)] aria-selected:text-[var(--accent-teal)]"
                      >
                        Create {item.label}
                      </Command.Item>
                    ))}
                  </Command.Group>

                  {sections.map((section) => (
                    <Command.Group
                      key={section.id}
                      heading={section.label}
                      className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-[var(--muted)]"
                    >
                      {section.items.map((item) => (
                        <Command.Item
                          key={`${section.id}-${item.href}-${item.label}`}
                          value={`${section.label} ${item.label}`}
                          onSelect={() => go(item.href)}
                          className="cursor-pointer rounded-xl px-3 py-2 text-sm aria-selected:bg-[var(--accent-soft)] aria-selected:text-[var(--accent-teal)]"
                        >
                          {item.label}
                        </Command.Item>
                      ))}
                    </Command.Group>
                  ))}

                  <Command.Group heading="All destinations" className="sr-only">
                    {navigationSections.flatMap((section) =>
                      section.items.map((item) => (
                        <Command.Item
                          key={`all-${item.href}-${item.label}`}
                          value={item.label}
                          onSelect={() => go(item.href)}
                        >
                          {item.label}
                        </Command.Item>
                      )),
                    )}
                  </Command.Group>
                </>
              ) : null}
            </Command.List>
          </Command>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
