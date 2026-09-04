import { useCallback, useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";
import "./AnimatedList.css";

function AnimatedItem({
  children,
  delay,
  index,
  selected,
  root,
  onMouseEnter,
  onClick
}) {
  const ref = useRef(null);
  const reduceMotion = useReducedMotion();
  const inView = useInView(ref, { root, amount: 0.2, once: true });

  return (
    <motion.div
      ref={ref}
      data-index={index}
      onMouseEnter={onMouseEnter}
      onClick={onClick}
      initial={reduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: 12 }}
      animate={reduceMotion || inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 12 }}
      transition={reduceMotion ? { duration: 0 } : { duration: 0.28, delay, ease: "easeOut" }}
      className="animated-list-entry"
      role="option"
      aria-selected={selected}
    >
      {children}
    </motion.div>
  );
}

export default function AnimatedList({
  items = [],
  renderItem,
  onItemSelect,
  showGradients = true,
  enableArrowNavigation = true,
  className = "",
  itemClassName = "",
  displayScrollbar = true,
  initialSelectedIndex = -1
}) {
  const listRef = useRef(null);
  const [selectedIndex, setSelectedIndex] = useState(initialSelectedIndex);
  const [keyboardNav, setKeyboardNav] = useState(false);
  const [topGradientOpacity, setTopGradientOpacity] = useState(0);
  const [bottomGradientOpacity, setBottomGradientOpacity] = useState(1);

  const handleScroll = useCallback((event) => {
    const { scrollTop, scrollHeight, clientHeight } = event.currentTarget;
    setTopGradientOpacity(Math.min(scrollTop / 50, 1));
    const bottomDistance = scrollHeight - (scrollTop + clientHeight);
    setBottomGradientOpacity(
      scrollHeight <= clientHeight ? 0 : Math.min(bottomDistance / 50, 1)
    );
  }, []);

  const handleKeyDown = useCallback((event) => {
    // Keyboard navigation sirf focused list ke andar rakho, poore page par nahi.
    if (!enableArrowNavigation || !items.length) {
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setKeyboardNav(true);
      setSelectedIndex((current) => Math.min(current + 1, items.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setKeyboardNav(true);
      setSelectedIndex((current) => Math.max(current - 1, 0));
    } else if (event.key === "Enter" && selectedIndex >= 0) {
      event.preventDefault();
      onItemSelect?.(items[selectedIndex], selectedIndex);
    }
  }, [enableArrowNavigation, items, onItemSelect, selectedIndex]);

  useEffect(() => {
    if (!keyboardNav || selectedIndex < 0 || !listRef.current) {
      return;
    }

    const selectedItem = listRef.current.querySelector(
      `[data-index="${selectedIndex}"]`
    );

    selectedItem?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    setKeyboardNav(false);
  }, [keyboardNav, selectedIndex]);

  return (
    <div className={`scroll-list-container ${className}`}>
      <div
        ref={listRef}
        className={`scroll-list ${!displayScrollbar ? "no-scrollbar" : ""}`}
        onScroll={handleScroll}
        onKeyDown={handleKeyDown}
        tabIndex={enableArrowNavigation ? 0 : undefined}
        role="listbox"
        aria-label="Animated list"
      >
        {items.map((item, index) => (
          <AnimatedItem
            key={item?.id ?? index}
            index={index}
            delay={Math.min(index * 0.025, 0.15)}
            selected={selectedIndex === index}
            root={listRef}
            onMouseEnter={() => setSelectedIndex(index)}
            onClick={() => {
              setSelectedIndex(index);
              onItemSelect?.(item, index);
            }}
          >
            <div
              className={`item ${selectedIndex === index ? "selected" : ""} ${itemClassName}`}
            >
              {renderItem ? renderItem(item, index) : <p className="item-text">{item}</p>}
            </div>
          </AnimatedItem>
        ))}
      </div>
      {showGradients && (
        <>
          <div className="top-gradient" style={{ opacity: topGradientOpacity }} />
          <div className="bottom-gradient" style={{ opacity: bottomGradientOpacity }} />
        </>
      )}
    </div>
  );
}
