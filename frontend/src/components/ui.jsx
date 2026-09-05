export function CardHeading({ eyebrow, title, action }) {
  return (
    <div className="card-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {action && <span className="card-action">{action}</span>}
    </div>
  );
}

export function EmptyState({ title, copy, action }) {
  return (
    <div className="empty-state">
      <div className="empty-mark">○</div>
      <h3>{title}</h3>
      <p>{copy}</p>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  note,
  tone,
  symbol,
  statId,
  draggedStat,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd
}) {
  return (
    <article
      className={"stat-card " + tone + (draggedStat === statId ? " dragging" : "")}
      draggable
      onDragStart={(event) => onDragStart(event, statId)}
      onDragOver={onDragOver}
      onDrop={(event) => onDrop(event, statId)}
      onDragEnd={onDragEnd}
      title="Drag to reorder this card"
    >
      <div className="stat-top">
        <span className="eyebrow">{label}</span>
        <span className="drag-handle" aria-hidden="true">⠿</span>
        <span className="stat-symbol">{symbol}</span>
      </div>
      <strong className="stat-value">{value}</strong>
      <span className="stat-note">{note}</span>
    </article>
  );
}
