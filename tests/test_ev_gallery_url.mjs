// user_study/HDR_Video_Project_Page/tests/test_ev_gallery_url.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildTileUrl, formatEv } from "../js/ev-gallery.js";

test("formatEv adds explicit + sign for non-negative integers", () => {
  assert.equal(formatEv(0), "+0");
  assert.equal(formatEv(3), "+3");
  assert.equal(formatEv(-3), "-3");
});

test("buildTileUrl substitutes scene, method, and ev placeholders", () => {
  const tpl = "assets/gallery/scene_{scene}/{method}_ev{ev}.webp";
  assert.equal(
    buildTileUrl(tpl, { scene: 71, method: "Ours", ev: 0 }),
    "assets/gallery/scene_71/Ours_ev+0.webp",
  );
  assert.equal(
    buildTileUrl(tpl, { scene: 32, method: "LEDiff", ev: -2 }),
    "assets/gallery/scene_32/LEDiff_ev-2.webp",
  );
});

test("buildTileUrl is order-independent", () => {
  const tpl = "{method}/{scene}/{ev}";
  assert.equal(
    buildTileUrl(tpl, { ev: 1, scene: 5, method: "GT" }),
    "GT/5/+1",
  );
});
