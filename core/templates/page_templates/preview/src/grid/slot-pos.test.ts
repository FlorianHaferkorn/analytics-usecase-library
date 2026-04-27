import { describe, it, expect } from "vitest";
import { slotPos, validateSlot, slotsOverlap } from "./slot-pos.js";

describe("slotPos()", () => {
  it("produces a calc() string for top-left origin slot", () => {
    const s = slotPos({ col: 0, row: 0, cs: 1, rs: 1 });
    expect(s.position).toBe("absolute");
    expect(s.left).toContain("calc(");
    expect(s.left).toContain("var(--outer)");
    expect(s.left).toContain("0");
    expect(s.top).toContain("var(--outer)");
    expect(s.width).toContain("var(--lu-w)");
    expect(s.height).toContain("var(--lu-h)");
  });

  it("multiplies lu-w / lu-h correctly for larger spans", () => {
    const s = slotPos({ col: 2, row: 3, cs: 4, rs: 5 });
    expect(s.width).toContain("4 * var(--lu-w)");
    expect(s.width).toContain("3 * var(--gutter)");
    expect(s.height).toContain("5 * var(--lu-h)");
    expect(s.height).toContain("4 * var(--gutter)");
  });

  it("handles fractional coords (T4 detail matrix case)", () => {
    const s = slotPos({ col: 2, row: 1.3, cs: 8, rs: 10.7 });
    expect(s.top).toContain("1.3 * (var(--lu-h) + var(--gutter))");
    expect(s.height).toContain("10.7 * var(--lu-h)");
  });
});

describe("validateSlot()", () => {
  it("accepts a full-grid slot (12 cols x 12 rows)", () => {
    expect(validateSlot({ col: 0, row: 0, cs: 12, rs: 12 })).toEqual([]);
  });

  it("accepts fractional coords that sum exactly to 12", () => {
    expect(validateSlot({ col: 2, row: 1.3, cs: 8, rs: 10.7 })).toEqual([]);
  });

  it("flags col overflow (col + cs > 12)", () => {
    const errors = validateSlot({ col: 8, row: 0, cs: 5, rs: 1 });
    expect(errors).toHaveLength(1);
    expect(errors[0]!.field).toBe("colOverflow");
  });

  it("flags row overflow (row + rs > 12)", () => {
    const errors = validateSlot({ col: 0, row: 10, cs: 1, rs: 3 });
    expect(errors).toHaveLength(1);
    expect(errors[0]!.field).toBe("rowOverflow");
  });

  it("flags negative col", () => {
    const errors = validateSlot({ col: -1, row: 0, cs: 1, rs: 1 });
    expect(errors.some((e) => e.field === "col")).toBe(true);
  });

  it("flags zero cs", () => {
    const errors = validateSlot({ col: 0, row: 0, cs: 0, rs: 1 });
    expect(errors.some((e) => e.field === "cs")).toBe(true);
  });

  it("flags multiple errors at once", () => {
    const errors = validateSlot({ col: -1, row: 20, cs: 0, rs: 0 });
    expect(errors.length).toBeGreaterThanOrEqual(3);
  });
});

describe("slotsOverlap()", () => {
  it("non-adjacent slots do not overlap", () => {
    expect(
      slotsOverlap(
        { col: 0, row: 0, cs: 4, rs: 4 },
        { col: 4, row: 0, cs: 4, rs: 4 },
      ),
    ).toBe(false);
  });

  it("slots sharing an edge do not overlap", () => {
    expect(
      slotsOverlap(
        { col: 0, row: 0, cs: 6, rs: 6 },
        { col: 6, row: 0, cs: 6, rs: 6 },
      ),
    ).toBe(false);
  });

  it("overlapping slots are detected", () => {
    expect(
      slotsOverlap(
        { col: 0, row: 0, cs: 6, rs: 6 },
        { col: 3, row: 3, cs: 6, rs: 6 },
      ),
    ).toBe(true);
  });

  it("fully contained slot overlaps parent", () => {
    expect(
      slotsOverlap(
        { col: 0, row: 0, cs: 12, rs: 12 },
        { col: 2, row: 2, cs: 4, rs: 4 },
      ),
    ).toBe(true);
  });

  it("T4 layout: SlicerPane | Matrix | ActionPanel do not overlap", () => {
    const slicerPane = { col: 0, row: 0, cs: 2, rs: 12 };
    const smartNarrative = { col: 2, row: 0, cs: 8, rs: 1.2 };
    const detailMatrix = { col: 2, row: 1.3, cs: 8, rs: 10.7 };
    const actionPanel = { col: 10, row: 0, cs: 2, rs: 12 };
    expect(slotsOverlap(slicerPane, smartNarrative)).toBe(false);
    expect(slotsOverlap(slicerPane, detailMatrix)).toBe(false);
    expect(slotsOverlap(slicerPane, actionPanel)).toBe(false);
    expect(slotsOverlap(smartNarrative, detailMatrix)).toBe(false);
    expect(slotsOverlap(smartNarrative, actionPanel)).toBe(false);
    expect(slotsOverlap(detailMatrix, actionPanel)).toBe(false);
  });
});
