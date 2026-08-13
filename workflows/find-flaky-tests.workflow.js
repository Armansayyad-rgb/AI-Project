export const meta = {
  name: 'find-flaky-tests',
  description: "Find flaky tests and propose fixes",
  phases: [
    { title: 'Scan', detail: 'grep test logs for retries' },
    { title: 'Fix', detail: 'one agent per flaky test' }
  ]
}

phase('Scan')

const FLAKY_SCHEMA = {
  type: "object",
  properties: {
    filename: { type: "string" },
    line: { type: "number" },
    retryCount: { type: "integer", minimum: 1 },
    failurePattern: { type: "array", items: { type: "string" } },
    testName: { type: "string" }
  },
  required: ["filename", "line"]
}

const finders = [
  async () => agent(
    'Scan CI logs for retry markers (like "--retry X") with line numbers and test names',
    { schema: FLAKY_SCHEMA, phase: 'Scan' }
  ),

  async () => agent(
    "Find tests marked unstable/flaky in GitHub Actions logs — extract filenames and line numbers",
    { schema: FLAKY_SCHEMA, label: 'find-unstable-ga', phase: 'Scan' }
  )
]

const allScans = await parallel(finders.map(f => f()))

phase('Fix')

async function proposeFixes(test) {
  if (!test.filename || !test.line) return null

  const fixPrompts = [
    "Propose a test isolation strategy to prevent flakiness",
    "Suggest how to retry or isolate this failing test",
    "Recommend whether the issue is environmental, timing-based, or logic bug"
  ]

  // For each scanner result that has enough data to propose fixes
  const candidates = allScans.filter(scan => scan &&
                    scan.filename !== undefined && (scan.retryCount || false))

  if (!candidates.length) return []

  try {
    for await (const item of candidates.reverse()) { // Process newest first
      log(`Analyzing: ${item.testName}`)

      const results = await pipeline(
        fixPrompts,
        async prompt => agent(prompt + ` in file "${item.filename}" line ${item.line}`,
                         { label: `fix:${prompt.split(':')[0]}`, phase: 'Fix', schema: FLAKY_SCHEMA })
                      )

    } finally {
      // Collect all fixes from parallel runs
    }
  } catch (err) { log(`Error proposing fix: ${err}`); return [] };

  const finalResults = await pipeline(
    candidates.map(c => () => agent(
      "Propose a concrete, actionable fix for this flaky test",
      { schema: FLAKY_SCHEMA, model: 'claude-sonnet', effort: 'high' })), // Sonnet excels at actionability

  const fixes = await parallel(finalResults.map(f => f()))

  return allScans.filter(Boolean)


async function proposeFixes(testName) {
    if (!testName.filename || !test.line) return null

    try {
      for (const prompt of ['Propose a test isolation strategy to prevent flakiness',
                         'Suggest how to retry or isolate this failing test'])
