import { useEffect, useRef } from "react";
import "./ElectricBorder.css";

function random(value) {
  const result = Math.sin(value * 12.9898) * 43758.5453;
  return result - Math.floor(result);
}

function noise2D(x, y) {
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const fx = x - x0;
  const fy = y - y0;
  const smoothX = fx * fx * (3 - 2 * fx);
  const smoothY = fy * fy * (3 - 2 * fy);
  const top = random(x0 + y0 * 57) * (1 - smoothX) + random(x0 + 1 + y0 * 57) * smoothX;
  const bottom = random(x0 + (y0 + 1) * 57) * (1 - smoothX) + random(x0 + 1 + (y0 + 1) * 57) * smoothX;
  return top * (1 - smoothY) + bottom * smoothY;
}

function roundedRectPoint(progress, left, top, width, height, radius) {
  const straightWidth = width - 2 * radius;
  const straightHeight = height - 2 * radius;
  const cornerArc = (Math.PI * radius) / 2;
  const perimeter = 2 * straightWidth + 2 * straightHeight + 4 * cornerArc;
  let distance = progress * perimeter;

  if (distance <= straightWidth) {
    return { x: left + radius + distance, y: top };
  }
  distance -= straightWidth;

  if (distance <= cornerArc) {
    const angle = -Math.PI / 2 + (distance / cornerArc) * (Math.PI / 2);
    return { x: left + width - radius + radius * Math.cos(angle), y: top + radius + radius * Math.sin(angle) };
  }
  distance -= cornerArc;

  if (distance <= straightHeight) {
    return { x: left + width, y: top + radius + distance };
  }
  distance -= straightHeight;

  if (distance <= cornerArc) {
    const angle = (distance / cornerArc) * (Math.PI / 2);
    return { x: left + width - radius + radius * Math.cos(angle), y: top + height - radius + radius * Math.sin(angle) };
  }
  distance -= cornerArc;

  if (distance <= straightWidth) {
    return { x: left + width - radius - distance, y: top + height };
  }
  distance -= straightWidth;

  if (distance <= cornerArc) {
    const angle = Math.PI / 2 + (distance / cornerArc) * (Math.PI / 2);
    return { x: left + radius + radius * Math.cos(angle), y: top + height - radius + radius * Math.sin(angle) };
  }
  distance -= cornerArc;

  if (distance <= straightHeight) {
    return { x: left, y: top + height - radius - distance };
  }

  const angle = Math.PI + (distance - straightHeight) / cornerArc * (Math.PI / 2);
  return { x: left + radius + radius * Math.cos(angle), y: top + radius + radius * Math.sin(angle) };
}

export default function ElectricBorder({
  children,
  color = "#5227FF",
  speed = 1,
  chaos = 0.12,
  thickness = 2,
  borderRadius = 24,
  className = "",
  style
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) {
      return undefined;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      return undefined;
    }

    const borderOffset = 10;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // Tab switch hone par canvas animation pause karke battery aur CPU bachao.
    let animationId = null;
    let lastTime = performance.now();
    let time = 0;
    let dimensions = { width: 0, height: 0, dpr: 1 };

    function resize() {
      const rect = container.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      dimensions = {
        width: rect.width + borderOffset * 2,
        height: rect.height + borderOffset * 2,
        dpr
      };
      canvas.width = dimensions.width * dpr;
      canvas.height = dimensions.height * dpr;
      canvas.style.width = `${dimensions.width}px`;
      canvas.style.height = `${dimensions.height}px`;
    }

    function draw(currentTime) {
      const delta = Math.max(0, currentTime - lastTime) / 1000;
      time += delta * speed;
      lastTime = currentTime;

      const { width, height, dpr } = dimensions;
      const borderWidth = width - borderOffset * 2;
      const borderHeight = height - borderOffset * 2;
      const radius = Math.min(borderRadius, borderWidth / 2, borderHeight / 2);
      const sampleCount = Math.max(40, Math.floor((borderWidth + borderHeight) * 1.4));

      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      context.clearRect(0, 0, width, height);
      context.beginPath();
      context.strokeStyle = color;
      context.lineWidth = thickness;
      context.lineCap = "round";
      context.lineJoin = "round";
      context.shadowColor = color;
      context.shadowBlur = 5 + chaos * 12;

      for (let index = 0; index <= sampleCount; index += 1) {
        const progress = index / sampleCount;
        const point = roundedRectPoint(
          progress,
          borderOffset,
          borderOffset,
          borderWidth,
          borderHeight,
          radius
        );
        const noiseX = (noise2D(progress * 8 + time * 0.7, 0) - 0.5) * chaos * 18;
        const noiseY = (noise2D(progress * 8 + time * 0.7, 1) - 0.5) * chaos * 18;

        if (index === 0) {
          context.moveTo(point.x + noiseX, point.y + noiseY);
        } else {
          context.lineTo(point.x + noiseX, point.y + noiseY);
        }
      }

      context.closePath();
      context.stroke();
      context.shadowBlur = 0;
    }

    const stopAnimation = () => {
      if (animationId !== null) {
        cancelAnimationFrame(animationId);
        animationId = null;
      }
    };

    const startAnimation = () => {
      if (!reducedMotion && !document.hidden && animationId === null) {
        animationId = requestAnimationFrame(frame);
      }
    };

    const frame = (currentTime) => {
      animationId = null;
      draw(currentTime);
      startAnimation();
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopAnimation();
      } else {
        startAnimation();
      }
    };

    resize();
    if (reducedMotion) {
      draw(lastTime);
    } else {
      startAnimation();
    }

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      stopAnimation();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      resizeObserver.disconnect();
    };
  }, [borderRadius, chaos, color, speed, thickness]);

  const rootStyle = {
    ...style,
    "--electric-border-color": color,
    borderRadius: style?.borderRadius ?? `${borderRadius}px`
  };

  return (
    <div ref={containerRef} className={`electric-border ${className}`} style={rootStyle}>
      <div className="eb-canvas-container" aria-hidden="true">
        <canvas ref={canvasRef} className="eb-canvas" />
      </div>
      <div className="eb-layers" aria-hidden="true">
        <div className="eb-glow-1" />
        <div className="eb-glow-2" />
        <div className="eb-background-glow" />
      </div>
      <div className="eb-content">{children}</div>
    </div>
  );
}
