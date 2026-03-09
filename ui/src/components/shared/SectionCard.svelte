<script>
  let { title = "", children } = $props();
</script>

<div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
  {#if title}
    <h3 class="text-lg font-semibold text-[var(--navy)] mb-4">{title}</h3>
  {/if}
  {@render children()}
</div>
