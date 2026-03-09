<script>
  import StatusBadge from "./shared/StatusBadge.svelte";

  let { stages, stageStatus, activeStage, onselect } = $props();

  const stageLabels = {
    etl: "Column Review & Cleaning",
    stats: "Feature Selection",
    model: "Model Training",
    evaluate: "Evaluation",
  };

  const stageIcons = {
    etl: "1",
    stats: "2",
    model: "3",
    evaluate: "4",
  };
</script>

<nav class="space-y-1">
  {#each stages as stage, i}
    {@const status = stageStatus[stage] || "pending"}
    {@const isActive = stage === activeStage}
    {@const isDone = status === "confirmed" || status === "complete"}
    <button
      onclick={() => onselect(stage)}
      class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all
             {isActive
               ? 'bg-white shadow-md border border-[var(--ice-blue)]'
               : 'hover:bg-white/60'}"
    >
      <!-- Step number / check -->
      <div
        class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0
               {isDone
                 ? 'bg-green-100 text-green-700'
                 : isActive
                   ? 'bg-[var(--navy)] text-white'
                   : 'bg-gray-100 text-gray-400'}"
      >
        {#if isDone}
          &#10003;
        {:else}
          {stageIcons[stage]}
        {/if}
      </div>

      <div class="flex-1 min-w-0">
        <div class="text-sm font-medium truncate {isActive ? 'text-[var(--navy)]' : 'text-gray-600'}">
          {stageLabels[stage]}
        </div>
        <div class="mt-0.5">
          <StatusBadge {status} />
        </div>
      </div>
    </button>

    <!-- Connector line -->
    {#if i < stages.length - 1}
      <div class="ml-[1.45rem] w-px h-3 {isDone ? 'bg-green-200' : 'bg-gray-200'}"></div>
    {/if}
  {/each}
</nav>
