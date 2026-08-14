import test from "node:test";
import assert from "node:assert/strict";

import { localApiPath } from "./api.js";

test("localApiPath turns a DRF pagination URL into a proxied API path", () => {
  assert.equal(localApiPath("http://localhost:8000/api/projects/?organization=4&page=2"), "/projects/?organization=4&page=2");
});
