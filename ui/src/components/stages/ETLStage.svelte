<script>
  import MetricCard from "../shared/MetricCard.svelte";
  import ConfirmButton from "../shared/ConfirmButton.svelte";
  import SectionCard from "../shared/SectionCard.svelte";
  import { getColumns, analyzeTarget, confirmStage } from "../../api/client.js";

  let { status, onconfirmed } = $props();

  let columns = $state(null);
  let loading = $state(false);
  let targetCol = $state("");
  let statsResults = $state(null);
  let analyzingTarget = $state(false);
  let error = $state(null);

  // Per-column decisions: "keep" | "drop" | "" (blank/unsure)
  let decisions = $state({});
  // Per-column notes (required when decision is keep or drop)
  let notes = $state({});
  // Track which columns have validation errors
  let noteErrors = $state({});

  // Load columns on mount
  $effect(() => {
    if (!columns && !loading) {
      loading = true;
      getColumns()
        .then((cols) => {
          columns = cols;
          // Init decisions to blank
          const d = {};
          const n = {};
          for (const c of cols) {
            d[c.name] = "";
            n[c.name] = "";
          }
          decisions = d;
          notes = n;
        })
        .catch((e) => (error = e.message))
        .finally(() => (loading = false));
    }
  });

  async function handleAnalyzeTarget() {
    if (!targetCol) return;
    analyzingTarget = true;
    error = null;
    try {
      statsResults = await analyzeTarget(targetCol);
    } catch (e) {
      error = e.message;
    }
    analyzingTarget = false;
  }

  function setDecision(col, value) {
    decisions[col] = decisions[col] === value ? "" : value;
    // Clear note error when decision changes to blank
    if (decisions[col] === "") {
      noteErrors[col] = false;
    }
  }

  function getTestForColumn(colName) {
    if (!statsResults?.tests) return null;
    return statsResults.tests.find((t) => t.column === colName);
  }

  // Validate: notes required for keep/drop decisions
  function validate() {
    let valid = true;
    const errs = {};
    for (const col of columns) {
      if (col.name === targetCol) continue;
      const d = decisions[col.name];
      if (d === "keep" || d === "drop") {
        if (!notes[col.name]?.trim()) {
          errs[col.name] = true;
          valid = false;
        }
      }
    }
    noteErrors = errs;
    return valid;
  }

  let decidedCount = $derived(() => {
    if (!columns) return { keep: 0, drop: 0, unsure: 0 };
    let keep = 0, drop = 0, unsure = 0;
    for (const c of columns) {
      if (c.name === targetCol) continue;
      const d = decisions[c.name];
      if (d === "keep") keep++;
      else if (d === "drop") drop++;
      else unsure++;
    }
    return { keep, drop, unsure };
  });

  async function confirm() {
    if (!validate()) {
      error = "Notes are required for all Keep/Drop decisions.";
      return;
    }
    error = null;
    try {
      await confirmStage("etl", {
        target: targetCol,
        columns: columns
          .filter((c) => c.name !== targetCol)
          .map((c) => ({
            column: c.name,
            decision: decisions[c.name] || "",
            note: notes[c.name] || "",
          })),
      });
      onconfirmed();
    } catch (e) {
      error = e.message;
    }
  }

  let canConfirm = $derived(() => {
    if (!targetCol || !columns) return false;
    // Need at least one keep decision
    return decidedCount().keep > 0;
  });
</script>

{#if loading}
  <div class="flex items-center justify-center py-20">
    <div class="w-10 h-10 border-4 border-[var(--ice-blue)] border-t-[var(--navy)] rounded-full animate-spin"></div>
    <span class="ml-3 text-gray-500">Loading columns...</span>
  </div>
{:else if columns}
  <div class="space-y-6">
    {#if error}
      <div class="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
        {error}
        <button onclick={() => error = null} class="ml-2 text-red-400 hover:text-red-600">&times;</button>
      </div>
    {/if}

    <!-- Target variable selection -->
    <SectionCard title="1. Select Target Variable">
      {#snippet children()}
        <div class="flex items-end gap-4">
          <div class="flex-1">
            <select
              bind:value={targetCol}
              class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-[var(--navy)] focus:outline-none"
            >
              <option value="">Choose the target column...</option>
              {#each columns as col}
                <option value={col.name}>{col.name} ({col.dtype}, {col.n_unique} unique)</option>
              {/each}
            </select>
          </div>
          <button
            onclick={handleAnalyzeTarget}
            disabled={!targetCol || analyzingTarget}
            class="px-5 py-2 rounded-lg font-medium text-white transition-all
                   {!targetCol || analyzingTarget
                     ? 'bg-gray-300 cursor-not-allowed'
                     : 'bg-[var(--accent)] hover:bg-[#5bb0c8] text-[var(--navy)]'}"
          >
            {#if analyzingTarget}
              Analyzing...
            {:else}
              Run Tests
            {/if}
          </button>
        </div>
        {#if statsResults}
          <p class="mt-2 text-sm text-green-600">
            Statistical tests completed against <strong>{statsResults.target}</strong>.
          </p>
        {/if}
      {/snippet}
    </SectionCard>

    <!-- Summary counts -->
    {#if targetCol}
      <div class="grid grid-cols-3 gap-4">
        <MetricCard label="Keeping" value={decidedCount().keep} />
        <MetricCard label="Dropping" value={decidedCount().drop} />
        <MetricCard label="Undecided" value={decidedCount().unsure} />
      </div>
    {/if}

    <!-- Column review list -->
    {#if targetCol}
      <SectionCard title="2. Review Each Column">
        {#snippet children()}
          <p class="text-sm text-gray-500 mb-4">
            For each column, decide Keep, Drop, or leave blank if unsure. A note is required for Keep/Drop.
          </p>
          <div class="space-y-3">
            {#each columns as col}
              {#if col.name !== targetCol}
                {@const test = getTestForColumn(col.name)}
                {@const d = decisions[col.name]}
                <div class="border rounded-xl p-4 transition-colors
                            {d === 'keep' ? 'border-green-300 bg-green-50/30' :
                             d === 'drop' ? 'border-red-300 bg-red-50/30' :
                             'border-gray-200 bg-white'}">

                  <!-- Column header row -->
                  <div class="flex items-start gap-4">
                    <!-- Column info -->
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="font-semibold text-[var(--navy)]">{col.name}</span>
                        <span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">{col.dtype}</span>
                      </div>
                      <div class="flex gap-4 mt-1 text-xs text-gray-400">
                        <span>{col.n_unique.toLocaleString()} unique</span>
                        <span>{col.null_pct}% null</span>
                        <span>{col.total_rows.toLocaleString()} rows</span>
                      </div>
                    </div>

                    <!-- Decision buttons -->
                    <div class="flex gap-1 shrink-0">
                      <button
                        onclick={() => setDecision(col.name, "keep")}
                        class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
                               {d === 'keep'
                                 ? 'bg-green-600 text-white shadow-sm'
                                 : 'bg-gray-100 text-gray-500 hover:bg-green-100 hover:text-green-700'}"
                      >Keep</button>
                      <button
                        onclick={() => setDecision(col.name, "drop")}
                        class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all
                               {d === 'drop'
                                 ? 'bg-red-600 text-white shadow-sm'
                                 : 'bg-gray-100 text-gray-500 hover:bg-red-100 hover:text-red-700'}"
                      >Drop</button>
                    </div>
                  </div>

                  <!-- Detail row: stats + samples + test result -->
                  <div class="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500">
                    {#if col.stats}
                      <span>mean: {col.stats.mean}</span>
                      <span>median: {col.stats.median}</span>
                      <span>std: {col.stats.std}</span>
                      <span>range: [{col.stats.min}, {col.stats.max}]</span>
                    {:else if col.top_values}
                      <span>top: {Object.entries(col.top_values).slice(0, 3).map(([k, v]) => `${k} (${v})`).join(", ")}</span>
                    {/if}
                  </div>

                  <div class="mt-1 text-xs text-gray-400">
                    samples: {col.sample_values?.join(", ")}
                  </div>

                  <!-- Statistical test result -->
                  {#if test}
                    <div class="mt-2 flex items-center gap-2 text-xs">
                      <span class="text-gray-400">{test.test}:</span>
                      {#if test.p_value !== null}
                        <span class="font-mono {test.significant ? 'text-green-600' : 'text-red-500'}">
                          p = {test.p_value < 0.001 ? "< 0.001" : test.p_value.toFixed(4)}
                        </span>
                        <span class="w-2 h-2 rounded-full {test.significant ? 'bg-green-400' : 'bg-red-400'}"></span>
                        <span class="text-gray-400">{test.significant ? "significant" : "not significant"}</span>
                      {:else}
                        <span class="text-gray-400">could not compute</span>
                      {/if}
                    </div>
                  {/if}

                  <!-- Note input (required for keep/drop) -->
                  {#if d === "keep" || d === "drop"}
                    <div class="mt-3">
                      <input
                        type="text"
                        bind:value={notes[col.name]}
                        placeholder="Note required — why {d}?"
                        class="w-full px-3 py-1.5 text-sm rounded-lg border transition-colors
                               {noteErrors[col.name]
                                 ? 'border-red-400 bg-red-50'
                                 : 'border-gray-200'} focus:border-[var(--navy)] focus:outline-none"
                      />
                      {#if noteErrors[col.name]}
                        <p class="text-xs text-red-500 mt-1">Note is required for this decision.</p>
                      {/if}
                    </div>
                  {/if}
                </div>
              {/if}
            {/each}
          </div>
        {/snippet}
      </SectionCard>
    {/if}

    <!-- Confirm -->
    {#if targetCol}
      <div class="flex justify-end">
        <ConfirmButton
          onclick={confirm}
          disabled={!canConfirm()}
          label="Confirm Selections & Clean Data"
        />
      </div>
    {/if}
  </div>
{/if}
