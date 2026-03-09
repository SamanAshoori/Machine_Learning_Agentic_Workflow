<script>
  import MetricCard from "../shared/MetricCard.svelte";
  import ConfirmButton from "../shared/ConfirmButton.svelte";
  import SectionCard from "../shared/SectionCard.svelte";
  import { confirmStage } from "../../api/client.js";

  let { data = null, status, onconfirmed, onrun, canRun = false } = $props();

  let nEstimators = $state(100);
  let maxDepth = $state(10);
  let classWeight = $state("balanced");
  let testSplit = $state(0.2);

  function handleTrain() {
    onrun({
      n_estimators: nEstimators,
      max_depth: maxDepth,
      class_weight: classWeight,
      test_split: testSplit,
    });
  }

  async function confirm() {
    await confirmStage("model", {
      model_type: "RandomForest",
      hyperparameters: {
        n_estimators: nEstimators,
        max_depth: maxDepth,
        class_weight: classWeight,
      },
    });
    onconfirmed();
  }

  let metrics = $derived(data?.model_metrics);
</script>

<div class="space-y-6">
  <!-- Hyperparameter config — always visible -->
  <SectionCard title="Model Configuration">
    {#snippet children()}
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <span class="block text-sm text-gray-500 mb-1">Model Type</span>
          <input type="text" value="Random Forest" disabled
            class="w-full px-3 py-2 rounded-lg border border-gray-200 bg-gray-50 text-sm" />
        </div>
        <div>
          <span class="block text-sm text-gray-500 mb-1">n_estimators</span>
          <input type="number" bind:value={nEstimators}
            disabled={status === "confirmed"}
            class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-[var(--navy)] focus:outline-none" />
        </div>
        <div>
          <span class="block text-sm text-gray-500 mb-1">max_depth</span>
          <input type="number" bind:value={maxDepth}
            disabled={status === "confirmed"}
            class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-[var(--navy)] focus:outline-none" />
        </div>
        <div>
          <span class="block text-sm text-gray-500 mb-1">test_split</span>
          <input type="number" bind:value={testSplit} step="0.05" min="0.1" max="0.5"
            disabled={status === "confirmed"}
            class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-[var(--navy)] focus:outline-none" />
        </div>
      </div>
      <div class="mt-4">
        <span class="block text-sm text-gray-500 mb-1">class_weight</span>
        <select bind:value={classWeight}
          disabled={status === "confirmed"}
          class="px-3 py-2 rounded-lg border border-gray-200 text-sm focus:border-[var(--navy)] focus:outline-none">
          <option value="balanced">balanced</option>
          <option value="balanced_subsample">balanced_subsample</option>
        </select>
      </div>

      {#if canRun && status === "pending"}
        <div class="mt-4">
          <button
            onclick={handleTrain}
            class="px-6 py-2.5 bg-[var(--accent)] text-[var(--navy)] font-semibold rounded-lg hover:bg-[#6bb8d3] transition-colors shadow-md"
          >
            Train Model
          </button>
        </div>
      {/if}
    {/snippet}
  </SectionCard>

  <!-- Results (shown after training) -->
  {#if metrics}
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricCard label="ROC-AUC" value={metrics.roc_auc.toFixed(4)} />
      <MetricCard label="Target Recall" value={(metrics.target_recall * 100).toFixed(1) + "%"} />
      <MetricCard
        label="Precision (1)"
        value={(metrics.classification_report?.["1"]?.precision * 100).toFixed(1) + "%"}
      />
      <MetricCard label="Train / Val" value={`${metrics.train_shape?.[0]?.toLocaleString()} / ${metrics.val_shape?.[0]?.toLocaleString()}`} />
    </div>

    <!-- Confusion matrix -->
    {#if metrics.confusion_matrix}
      <SectionCard title="Validation Confusion Matrix">
        {#snippet children()}
          {@const cm = metrics.confusion_matrix}
          <div class="inline-grid grid-cols-2 gap-1 text-center">
            <div class="bg-green-50 rounded-lg p-4 min-w-[120px]">
              <div class="text-lg font-bold text-green-700">{cm[0][0]?.toLocaleString()}</div>
              <div class="text-xs text-green-600">True Neg</div>
            </div>
            <div class="bg-red-50 rounded-lg p-4 min-w-[120px]">
              <div class="text-lg font-bold text-red-700">{cm[0][1]?.toLocaleString()}</div>
              <div class="text-xs text-red-600">False Pos</div>
            </div>
            <div class="bg-red-50 rounded-lg p-4 min-w-[120px]">
              <div class="text-lg font-bold text-red-700">{cm[1][0]?.toLocaleString()}</div>
              <div class="text-xs text-red-600">False Neg</div>
            </div>
            <div class="bg-green-50 rounded-lg p-4 min-w-[120px]">
              <div class="text-lg font-bold text-green-700">{cm[1][1]?.toLocaleString()}</div>
              <div class="text-xs text-green-600">True Pos</div>
            </div>
          </div>
        {/snippet}
      </SectionCard>
    {/if}

    <!-- Feature importances -->
    {#if metrics.feature_importances}
      <SectionCard title="Feature Importances">
        {#snippet children()}
          <div class="space-y-2">
            {#each Object.entries(metrics.feature_importances) as [feat, imp]}
              <div class="flex items-center gap-3 text-sm">
                <span class="w-28 text-right text-gray-600 truncate">{feat}</span>
                <div class="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div class="h-full rounded-full bg-[var(--navy)]" style="width: {imp * 100 / Object.values(metrics.feature_importances)[0] * 100}%"></div>
                </div>
                <span class="w-14 text-xs text-gray-400">{(imp * 100).toFixed(1)}%</span>
              </div>
            {/each}
          </div>
        {/snippet}
      </SectionCard>
    {/if}

    {#if status === "awaiting_review"}
      <div class="flex justify-end">
        <ConfirmButton onclick={confirm} />
      </div>
    {/if}
  {/if}
</div>
