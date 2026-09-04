import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import "./GridMotion.css";

const TOTAL_ITEMS = 28;

export default function GridMotion({ items = [], gradientColor = "#0b1d1b" }) {
  const rowRefs = useRef([]);
  const fallbackItems = ["Plan", "Track", "Save", "Invest", "Balance"];
  const sourceItems = items.length ? items : fallbackItems;
  const combinedItems = Array.from(
    { length: TOTAL_ITEMS },
    (_, index) => sourceItems[index % sourceItems.length]
  );

  useEffect(() => {
    // User ne reduced motion choose kiya ho to decorative movement skip karo.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return undefined;
    }

    const rowMovers = rowRefs.current.map((row) => (
      row
        ? gsap.quickTo(row, "x", {
            duration: 0.9,
            ease: "power3.out"
          })
        : null
    ));

    // Ticker ke har frame chalne ki zaroorat nahi; mouse move par hi rows update karo.
    const handleMouseMove = (event) => {
      const viewportWidth = Math.max(window.innerWidth, 1);
      const maxMoveAmount = 120;
      const normalizedX = event.clientX / viewportWidth - 0.5;

      rowMovers.forEach((moveRow, index) => {
        if (!moveRow) {
          return;
        }

        const direction = index % 2 === 0 ? 1 : -1;
        moveRow(normalizedX * maxMoveAmount * direction);
      });
    };

    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      gsap.killTweensOf(rowRefs.current.filter(Boolean));
    };
  }, []);

  return (
    <div className="grid-motion" aria-hidden="true">
      <section
        className="grid-motion-intro"
        style={{
          background: `radial-gradient(circle at center, ${gradientColor} 0%, transparent 68%)`
        }}
      >
        <div className="grid-motion-container">
          {[0, 1, 2, 3].map((rowIndex) => (
            <div
              key={rowIndex}
              className="grid-motion-row"
              ref={(element) => {
                rowRefs.current[rowIndex] = element;
              }}
            >
              {[0, 1, 2, 3, 4, 5, 6].map((itemIndex) => {
                const content = combinedItems[rowIndex * 7 + itemIndex];

                return (
                  <div className="grid-motion-item" key={itemIndex}>
                    <div className="grid-motion-item-inner">
                      <span>{content}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
