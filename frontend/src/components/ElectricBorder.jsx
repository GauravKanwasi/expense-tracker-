export default function ElectricBorder({
  children,
  color = "#34d399",
  speed = 1,
  thickness = 2,
  borderRadius = 20,
  className = "",
  style
}) {
  const normalizedSpeed = Math.max(0.25, Number(speed) || 1);
  const variables = {
    "--electric-border-color": color,
    "--electric-border-duration": `${6 / normalizedSpeed}s`,
    "--electric-border-width": `${thickness}px`,
    "--electric-border-radius": `${borderRadius}px`,
    ...style
  };

  return <div className={"electric-border " + className} style={variables}>{children}</div>;
}
