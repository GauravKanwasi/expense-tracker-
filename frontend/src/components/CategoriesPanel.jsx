import { CardHeading } from "./ui";

export default function CategoriesPanel({
  categories,
  categoryName,
  editing,
  onCategoryNameChange,
  actionLoading,
  onSubmit,
  onDelete,
  onEdit,
  onCancelEdit
}) {
  return (
    <section id="categories" className="card section-card">
      <CardHeading
        eyebrow="ORGANIZE"
        title="Categories"
        action={categories.length + " total"}
      />
      <form className="category-form" onSubmit={onSubmit}>
        <input
          type="text"
          placeholder="Create a category, e.g. Travel"
          value={categoryName}
          maxLength="100"
          onChange={(event) => onCategoryNameChange(event.target.value)}
        />
        <button className="button button-dark" disabled={actionLoading === "category"}>
          {actionLoading === "category"
            ? editing ? "Saving..." : "Adding..."
            : editing ? "Save category" : "Add category"}
        </button>
        {editing && (
          <button type="button" className="button button-ghost" onClick={onCancelEdit}>Cancel</button>
        )}
      </form>
      <div className="category-grid">
        {categories.map((category, motionIndex) => (
          <div
            className="category-chip"
            key={category.id}
            style={{ "--motion-index": motionIndex }}
          >
            <span className="category-dot" />
            <span>{category.name}</span>
            <div className="chip-actions">
              <button
                className="text-button"
                onClick={() => onEdit(category)}
                disabled={actionLoading === "category-" + category.id}
              >
                Edit
              </button>
              <button
                className="chip-delete"
                onClick={() => onDelete(category.id)}
                disabled={actionLoading === "category-" + category.id}
                aria-label={"Delete " + category.name}
              >
                ×
              </button>
            </div>
          </div>
        ))}
        {!categories.length && (
          <p className="muted-copy">Add a category before creating transactions.</p>
        )}
      </div>
    </section>
  );
}
