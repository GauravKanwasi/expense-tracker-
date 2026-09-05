import { CardHeading } from "./ui";

export default function CategoriesPanel({
  categories,
  categoryName,
  onCategoryNameChange,
  actionLoading,
  onSubmit,
  onDelete
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
          {actionLoading === "category" ? "Adding..." : "Add category"}
        </button>
      </form>
      <div className="category-grid">
        {categories.map((category) => (
          <div className="category-chip" key={category.id}>
            <span className="category-dot" />
            <span>{category.name}</span>
            <button
              className="chip-delete"
              onClick={() => onDelete(category.id)}
              disabled={actionLoading === "category-" + category.id}
              aria-label={"Delete " + category.name}
            >
              ×
            </button>
          </div>
        ))}
        {!categories.length && (
          <p className="muted-copy">Add a category before creating transactions.</p>
        )}
      </div>
    </section>
  );
}
