// Pure-function unit tests for js/list-input.js's parser (design review 2026-09-21, "missing
// input for a list of scalars"). No DOM, no server, no Playwright -- `node --test` runs this file
// directly against the real shipped module (not a copy):
//   node --test tests/e2e/list_input_parse.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import {
  parseListText,
  formatListText,
  listBoundsMessage,
  listTokenErrorMessage,
} from "../../src/strutture/web/static_next/js/list-input.js";

test("parseListText splits on comma, semicolon, space and newline", () => {
  assert.deepEqual(parseListText("5; 10; 15,5").values, [5, 10, 15.5]);
  assert.deepEqual(parseListText("5,10,15").values, [5, 10, 15]);
  assert.deepEqual(parseListText("5 10 15").values, [5, 10, 15]);
  assert.deepEqual(parseListText("5\n10\n15").values, [5, 10, 15]);
  assert.deepEqual(parseListText("5,  10 ;15").values, [5, 10, 15]);
});

test("parseListText accepts a decimal comma", () => {
  assert.deepEqual(parseListText("5; 10; 15,5").values, [5, 10, 15.5]);
  assert.deepEqual(parseListText("0,5").values, [0.5]);
});

test("parseListText also accepts a decimal point", () => {
  assert.deepEqual(parseListText("5.5; 10.25").values, [5.5, 10.25]);
});

test("parseListText ignores blank/whitespace-only input", () => {
  assert.deepEqual(parseListText("").values, []);
  assert.deepEqual(parseListText("   ").values, []);
  assert.deepEqual(parseListText(null).values, []);
});

test("parseListText reports unparseable tokens without dropping them silently", () => {
  const { values, invalidTokens } = parseListText("5; abc; 10");
  assert.deepEqual(values, [5, 10]);
  assert.deepEqual(invalidTokens, ["abc"]);
});

test("parseListText treats items as plain strings when itemKind is 'string'", () => {
  const { values, invalidTokens } = parseListText("rosso, verde; blu", "string");
  assert.deepEqual(values, ["rosso", "verde", "blu"]);
  assert.deepEqual(invalidTokens, []);
});

test("formatListText round-trips through parseListText with a decimal comma", () => {
  const text = formatListText([5, 10, 15.5]);
  assert.equal(text, "5; 10; 15,5");
  assert.deepEqual(parseListText(text).values, [5, 10, 15.5]);
});

test("formatListText joins strings with '; '", () => {
  assert.equal(formatListText(["rosso", "verde"], "string"), "rosso; verde");
});

test("formatListText returns an empty string for non-array input", () => {
  assert.equal(formatListText(undefined), "");
  assert.equal(formatListText(null), "");
});

test("listBoundsMessage flags too few values (minItems)", () => {
  const message = listBoundsMessage({ minItems: 2 }, [5]);
  assert.match(message, /almeno 2/);
});

test("listBoundsMessage flags too many values (maxItems)", () => {
  const message = listBoundsMessage({ minItems: 0, maxItems: 2 }, [5, 10, 15]);
  assert.match(message, /Massimo 2/);
});

test("listBoundsMessage flags a per-item value below the schema minimum", () => {
  const message = listBoundsMessage({ minItems: 0, itemMinimum: 0 }, [5, -1, 10]);
  assert.match(message, />=\s*0/);
});

test("listBoundsMessage flags a per-item value above the schema maximum", () => {
  const message = listBoundsMessage({ minItems: 0, itemMaximum: 120 }, [5, 500]);
  assert.match(message, /<=\s*120/);
});

test("listBoundsMessage returns null when every value is within bounds", () => {
  assert.equal(listBoundsMessage({ minItems: 1, maxItems: 5, itemMinimum: 0, itemMaximum: 200 }, [5, 10, 15.5]), null);
});

test("listTokenErrorMessage names every invalid token in Italian", () => {
  const message = listTokenErrorMessage(["abc", "xyz"]);
  assert.match(message, /abc, xyz/);
  assert.match(message, /virgola/);
});
