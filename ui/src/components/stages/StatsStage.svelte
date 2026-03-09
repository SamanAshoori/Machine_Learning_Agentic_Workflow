<script>
  import MetricCard from "../shared/MetricCard.svelte";
  import ConfirmButton from "../shared/ConfirmButton.svelte";
  import SectionCard from "../shared/SectionCard.svelte";
  import { confirmStage } from "../../api/client.js";

  let { data = null, status, onconfirmed } = $props();

  let selectedFeatures = $state(new Set());
  let initialized = $state(false);

  $effect(() => {
    if (data?.selected_features && !initialized) {
      selectedFeatures = new Set(data.selected_features);
      initialized = true;
    }
  });

  function toggleFeature(f) {
    let next = new Set(selectedFeatures);
    if (next.has(f)) next.delete(f);
    else next.add(f);
    selectedFeatures = next;
  }

  let sortedMetrics = $derived(() => {
    if (!data?.feature_metrics) return [];
    return Object.entries(data.feature_metrics)
      .map(([name, m]) => ({ name, ...m }))
      .sort((a, b) => a.p_value - b.p_value);
  });

  async function confirm() {
    await confirmStage("stats", { selected_features: [...selectedFeatures] });
    onconfirmed();
  }
</script>

{#if !data}
  <div class="text-gray-400 text-center py-12">Run this stage to see results</div>
{:else}
  <div class="space-y-6">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricCard label="Features Selected" value={selectedFeatures.size} />
      <MetricCard label="Total Evaluated" value={data.total_features} />
      <MetricCard label="Excluded" value={Object.keys(data.excluded || {}).length} />
      <MetricCard label="High Corr Pairs" value={data.high_corr_pairs?.length || 0} />
    </div>

    <!-- Excluded features -->
    {#if data.excluded && Object.keys(data.excluded).length > 0}
      <SectionCard title="Auto-Excluded Features">
        {#snippet children()}
          <div class="space-y-1 text-sm">
            {#each Object.entries(data.excluded) as [feat, reason]}
              <div class="flex items-center gap-2 px-3 py-1.5 rounded bg-red-50">
                <span class="font-medium text-red-700">{feat}</span>
                <span class="text-red-400 text-xs">{reason}</span>
              </div>
            {/each}
          </div>
        {/snippet}
      </SectionCard>
    {/if}

    <!-- Feature table -->
    {#if data.feature_metrics}
      <SectionCard title="Feature Metrics">
        {#snippet children()}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 text-left text-gray-500">
                  <th class="pb-2 pr-4">Include</th>
                  <th class="pb-2 pr-4">Feature</th>
                  <th class="pb-2 pr-4">p-value</th>
                  <th class="pb-2 pr-4">VIF</th>
                  <th class="pb-2">Mutual Info</th>
                </tr>
              </thead>
              <tbody>
                {#each sortedMetrics() as feat}
                  <tr class="border-b border-gray-50 hover:bg-gray-50">
                    <td class="py-2 pr-4">
                      <input
                        type="checkbox"
                        checked={selectedFeatures.has(feat.name)}
                        onchange={() => toggleFeature(feat.name)}
                        disabled={status !== "awaiting_review"}
                        class="rounded border-gray-300 text-[var(--navy)]"
                      />
                    </td>
                    <td class="py-2 pr-4 font-medium">{feat.name}</td>
                    <td class="py-2 pr-4">
                      <span class="inline-flex items-center gap-1">
                        {feat.p_value < 0.001 ? "< 0.001" : feat.p_value.toFixed(4)}
                        <span class="w-2 h-2 rounded-full {feat.p_value < 0.05 ? 'bg-green-400' : 'bg-red-400'}"></span>
                      </span>
                    </td>
                    <td class="py-2 pr-4">{feat.vif === Infinity ? "Inf" : feat.vif?.toFixed(3)}</td>
                    <td class="py-2">{feat.mutual_info?.toFixed(4)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/snippet}
      </SectionCard>
    {/if}

    <!-- P-value bars -->
    {#if data.feature_metrics}
      <SectionCard title="P-Value Distribution">
        {#snippet children()}
          <div class="space-y-2">
            {#each sortedMetrics() as feat}
              <div class="flex items-center gap-3 text-sm">
                <span class="w-24 text-right text-gray-600 truncate">{feat.name}</span>
                <div class="flex-1 bg-gray-100 rounded-full h-4 relative overflow-hidden">
                  <div
                    class="h-full rounded-full {feat.p_value < 0.05 ? 'bg-[var(--accent)]' : 'bg-red-300'}"
                    style="width: {Math.max(1, Math.min(100, (1 - Math.min(feat.p_value, 1)) * 100))}%"
                  ></div>
                </div>
                <span class="w-16 text-xs text-gray-400">
                  {feat.p_value < 0.001 ? "< .001" : feat.p_value.toFixed(3)}
                </span>
              </div>
            {/each}
          </div>
        {/snippet}
      </SectionCard>
    {/if}

    {#if status === "awaiting_review"}
      <div class="flex justify-end">
        <ConfirmButton onclick={confirm} disabled={selectedFeatures.size === 0} />
      </div>
    {/if}
  </div>
{/if}
