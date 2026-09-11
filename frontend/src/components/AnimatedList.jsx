import { useRef, useState } from "react";
import { AnimatePresence, useReducedMotion } from "motion/react";
import * as m from "motion/react-m";

export default function AnimatedList({
  items,
  renderItem,
  getKey,
  scrollClassName = "",
  itemClassName = "",
  showGradients = true,
  displayScrollbar = true,
  ariaLabel = "Animated list"
}) {
  const listRef = useRef(null);
  const [edges, setEdges] = useState({ top: 0, bottom: 1 });
  const shouldReduceMotion = useReducedMotion();

  function updateEdges(event) {
    const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
    const bottom = scrollHeight - scrollTop - clientHeight;
    setEdges({ top: Math.min(scrollTop / 32, 1), bottom: Math.min(bottom / 32, 1) });
  }

  function moveWithArrow(event) {
    if (!listRef.current || !["ArrowDown", "ArrowUp"].includes(event.key)) return;
    event.preventDefault();
    listRef.current.scrollBy({ top: event.key === "ArrowDown" ? 88 : -88, behavior: "smooth" });
  }

  return (
    <div className="animated-list">
      <div
        ref={listRef}
        className={"animated-list-scroll " + scrollClassName + (displayScrollbar ? "" : " no-scrollbar")}
        role="list"
        aria-label={ariaLabel}
        tabIndex="0"
        onScroll={updateEdges}
        onKeyDown={moveWithArrow}
      >
        <AnimatePresence initial={false}>
          {items.map((item, index) => (
            <m.div
              layout="position"
              className={"animated-list-item " + itemClassName}
              key={getKey(item)}
              role="listitem"
              initial={shouldReduceMotion ? false : { opacity: 0, y: 10, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: -8, scale: 0.985 }}
              whileHover={shouldReduceMotion ? undefined : { x: 3 }}
              transition={{
                duration: shouldReduceMotion ? 0 : 0.2,
                delay: shouldReduceMotion ? 0 : Math.min(index, 5) * 0.04
              }}
            >
              {renderItem(item)}
            </m.div>
          ))}
        </AnimatePresence>
      </div>
      {showGradients && <>
        <span className="animated-list-gradient top" style={{ opacity: edges.top }} />
        <span className="animated-list-gradient bottom" style={{ opacity: edges.bottom }} />
      </>}
    </div>
  );
}
