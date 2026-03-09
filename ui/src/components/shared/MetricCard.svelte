<script>
  let { label, value, sublabel = "" } = $props();
</script>

<div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-center">
  <div class="text-2xl font-bold text-[var(--navy)]">{value}</div>
  <div class="text-sm text-gray-500 mt-1">{label}</div>
  {#if sublabel}
    <div class="text-xs text-gray-400 mt-0.5">{sublabel}</div>
  {/if}
</div>
