<script>
  import MetricCard from "../shared/MetricCard.svelte";
  import ConfirmButton from "../shared/ConfirmButton.svelte";
  import SectionCard from "../shared/SectionCard.svelte";
  import { confirmStage } from "../../api/client.js";

  let { data = null, status, onconfirmed } = $props();

  let threshold = $state(0.5);
  let primaryMetric = $state("recall");
  let initialized = $state(false);

  $effect(() => {
    if (data?.eval_report && !initialized) {
      const opt = data.eval_report.optimal_threshold_tuning;
      if (opt?.optimal_threshold) {
        threshold = opt.optimal_threshold;
      }
      initialized = true;
    }
  });

  let defaultMetrics = $derived(data?.eval_report?.["default_threshold_0.5"]);
  let optimalMetrics = $derived(data?.eval_report?.optimal_threshold_tuning);

  async function confirm() {
    await confirmStage("evaluate", { threshold, primary_metric: primaryMetric });
    onconfirmed();
  }
</script>

{#if !data}
  <div class="text-gray-400 text-center py-12">Run this stage to see results</div>
{:else}
  <div class="space-y-6">
    {#if data.eval_report}
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="ROC-AUC" value={data.eval_report.roc_auc?.toFixed(4)} />
        <MetricCard
          label="Recall (0.5)"
          value={(defaultMetrics?.target_recall * 100)?.toFixed(1) + "%"}
        />
        <MetricCard
          label="Precision (0.5)"
          value={(defaultMetrics?.classification_report?.["1"]?.precision * 100)?.toFixed(1) + "%"}
        />
        <MetricCard
          label="Optimal Threshold"
          value={optimalMetrics?.optimal_threshold?.toFixed(2)}
        />
      </div>
    {/if}

    <!-- Threshold slider -->
    {#if status === "awaiting_review"}
      <SectionCard title="Threshold Selection">
        {#snippet children()}
          <div class="space-y-3">
            <div class="flex items-center gap-4">
              <input type="range" min="0.1" max="0.95" step="0.05"
                bind:value={threshold} class="flex-1 accent-[var(--navy)]" />
              <span class="text-lg font-mono font-bold text-[var(--navy)] w-12">{threshold.toFixed(2)}</span>
            </div>
            <div>
              <span class="text-sm text-gray-500">Primary metric:
                <select bind:value={primaryMetric} class="ml-2 rounded border border-gray-200 px-2 py-1 text-sm">
                  <option value="recall">Recall</option>
                  <option value="precision">Precision</option>
                  <option value="f1">F1 Score</option>
                </select>
              </span>
            </div>
          </div>
        {/snippet}
      </SectionCard>
    {/if}

    <!-- Threshold comparison -->
    {#if defaultMetrics && optimalMetrics}
      <SectionCard title="Threshold Comparison">
        {#snippet children()}
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b text-left text-gray-500">
                  <th class="pb-2 pr-4">Metric</th>
                  <th class="pb-2 pr-4">Default (0.5)</th>
                  <th class="pb-2">Optimal ({optimalMetrics.optimal_threshold?.toFixed(2)})</th>
                </tr>
              </thead>
              <tbody>
                <tr class="border-b border-gray-50">
                  <td class="py-2 pr-4 font-medium">Target Recall</td>
                  <td class="py-2 pr-4">{(defaultMetrics.target_recall * 100).toFixed(1)}%</td>
                  <td class="py-2">{(optimalMetrics.target_recall * 100).toFixed(1)}%</td>
                </tr>
                <tr class="border-b border-gray-50">
                  <td class="py-2 pr-4 font-medium">Precision (1)</td>
                  <td class="py-2 pr-4">{(defaultMetrics.classification_report["1"].precision * 100).toFixed(1)}%</td>
                  <td class="py-2">{(optimalMetrics.classification_report["1"].precision * 100).toFixed(1)}%</td>
                </tr>
                <tr class="border-b border-gray-50">
                  <td class="py-2 pr-4 font-medium">False Positives</td>
                  <td class="py-2 pr-4">{defaultMetrics.confusion_matrix[0][1].toLocaleString()}</td>
                  <td class="py-2">{optimalMetrics.confusion_matrix[0][1].toLocaleString()}</td>
                </tr>
                <tr class="border-b border-gray-50">
                  <td class="py-2 pr-4 font-medium">False Negatives</td>
                  <td class="py-2 pr-4">{defaultMetrics.confusion_matrix[1][0].toLocaleString()}</td>
                  <td class="py-2">{optimalMetrics.confusion_matrix[1][0].toLocaleString()}</td>
                </tr>
                <tr>
                  <td class="py-2 pr-4 font-medium">F1 (Class 1)</td>
                  <td class="py-2 pr-4">{defaultMetrics.classification_report["1"]["f1-score"]?.toFixed(4)}</td>
                  <td class="py-2">{optimalMetrics.best_f1_score?.toFixed(4)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        {/snippet}
      </SectionCard>

      <!-- Confusion matrices -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {#each [{ label: "Default (0.5)", cm: defaultMetrics.confusion_matrix }, { label: `Optimal (${optimalMetrics.optimal_threshold?.toFixed(2)})`, cm: optimalMetrics.confusion_matrix }] as { label, cm }}
          <SectionCard title="Confusion Matrix — {label}">
            {#snippet children()}
              <div class="inline-grid grid-cols-2 gap-1 text-center">
                <div class="bg-green-50 rounded-lg p-3">
                  <div class="font-bold text-green-700">{cm[0][0]?.toLocaleString()}</div>
                  <div class="text-xs text-green-600">TN</div>
                </div>
                <div class="bg-red-50 rounded-lg p-3">
                  <div class="font-bold text-red-700">{cm[0][1]?.toLocaleString()}</div>
                  <div class="text-xs text-red-600">FP</div>
                </div>
                <div class="bg-red-50 rounded-lg p-3">
                  <div class="font-bold text-red-700">{cm[1][0]?.toLocaleString()}</div>
                  <div class="text-xs text-red-600">FN</div>
                </div>
                <div class="bg-green-50 rounded-lg p-3">
                  <div class="font-bold text-green-700">{cm[1][1]?.toLocaleString()}</div>
                  <div class="text-xs text-green-600">TP</div>
                </div>
              </div>
            {/snippet}
          </SectionCard>
        {/each}
      </div>
    {/if}

    {#if status === "awaiting_review"}
      <div class="flex justify-end">
        <ConfirmButton onclick={confirm} />
      </div>
    {/if}
  </div>
{/if}
