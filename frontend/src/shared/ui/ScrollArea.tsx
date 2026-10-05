"use client";

import { useEffect, useRef } from "react";

/** A box that scrolls on its own, so long lists don't push the rest of the page down.
 * `stickToBottom` keeps the newest item (at the bottom, like a chat) in view. */
export function ScrollArea({
  className = "max-h-96",
  stickToBottom = false,
  children,
}: {
  className?: string;
  stickToBottom?: boolean;
  children: React.ReactNode;
}) {
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (stickToBottom && box.current) box.current.scrollTop = box.current.scrollHeight;
  });
  return (
    <div
      ref={box}
      tabIndex={0}
      className={`overflow-y-auto overscroll-contain rounded-lg focus-visible:outline-2 focus-visible:outline-indigo-500 ${className}`}
    >
      {children}
    </div>
  );
}
