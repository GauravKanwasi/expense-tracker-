import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AuthScreen from "./AuthScreen";

describe("AuthScreen", () => {
  it("submits sign-in details and lets the user reveal the password", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn((event) => event.preventDefault());
    const onChange = vi.fn();

    render(
      <AuthScreen
        mode="login"
        form={{ name: "", email: "sapna@example.com", password: "secure-pass" }}
        error=""
        loading={false}
        onModeChange={vi.fn()}
        onChange={onChange}
        onSubmit={onSubmit}
      />
    );

    await user.click(screen.getByRole("button", { name: "Show password" }));

    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "text");

    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(onSubmit).toHaveBeenCalledOnce();
  });
});
