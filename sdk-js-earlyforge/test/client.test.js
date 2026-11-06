import assert from "node:assert/strict"
import { test } from "node:test"
import { PulseClient, PulseApiError } from "../dist/client.js"

function mockFetchOnce(status, body) {
  const calls = []
  globalThis.fetch = async (url, init) => {
    calls.push({ url: url.toString(), headers: init?.headers ?? {} })
    return new Response(JSON.stringify(body), { status })
  }
  return calls
}

test("topTrends sends the bearer token and hits the right path", async () => {
  const calls = mockFetchOnce(200, { trends: [], total: 0 })
  const client = new PulseClient("ef_live_test", { baseUrl: "https://api.test" })
  const result = await client.topTrends({ locale: "fr" })

  assert.deepEqual(result, { trends: [], total: 0 })
  assert.equal(calls.length, 1)
  assert.equal(calls[0].headers.Authorization, "Bearer ef_live_test")
  assert.ok(calls[0].url.startsWith("https://api.test/v1/api/trends/top"))
  assert.ok(calls[0].url.includes("locale=fr"))
})

test("trendsByRegion builds the region path segment", async () => {
  mockFetchOnce(200, { trends: [], total: 0 })
  const client = new PulseClient("ef_live_test", { baseUrl: "https://api.test" })
  await client.trendsByRegion("US")
})

test("getTrend raises PulseApiError on 404", async () => {
  mockFetchOnce(404, { detail: "Not found" })
  const client = new PulseClient("ef_live_test", { baseUrl: "https://api.test" })
  await assert.rejects(
    () => client.getTrend("tr_missing"),
    (error) => {
      assert.ok(error instanceof PulseApiError)
      assert.equal(error.statusCode, 404)
      return true
    },
  )
})

test("constructor requires an api key", () => {
  assert.throws(() => new PulseClient(""))
})

test("fullTrends hits /v1/api/trends/full with filters", async () => {
  const calls = mockFetchOnce(200, { items: [{ trend_id: "tr_1" }], total: 1, page: 1, per_page: 20 })
  const client = new PulseClient("ef_live_test", { baseUrl: "https://api.test" })
  const result = await client.fullTrends({ region: "US", limit: 50 })

  assert.equal(result.total, 1)
  assert.ok(calls[0].url.startsWith("https://api.test/v1/api/trends/full"))
  assert.ok(calls[0].url.includes("region=US"))
  assert.ok(calls[0].url.includes("limit=50"))
})

test("fullTrends raises PulseApiError with structured detail on 402", async () => {
  mockFetchOnce(402, { detail: { error: "upgrade_required", upgrade_url: "/settings/billing" } })
  const client = new PulseClient("ef_live_test", { baseUrl: "https://api.test" })
  await assert.rejects(
    () => client.fullTrends(),
    (error) => {
      assert.ok(error instanceof PulseApiError)
      assert.equal(error.statusCode, 402)
      assert.equal(error.detail.error, "upgrade_required")
      return true
    },
  )
})

test("getFullTrend raises PulseApiError on 402 trend_locked", async () => {
  mockFetchOnce(402, { detail: { error: "This trend is locked on your plan", code: "trend_locked" } })
  const client = new PulseClient("ef_live_test", { baseUrl: "https://api.test" })
  await assert.rejects(
    () => client.getFullTrend("tr_locked"),
    (error) => {
      assert.equal(error.detail.code, "trend_locked")
      return true
    },
  )
})
