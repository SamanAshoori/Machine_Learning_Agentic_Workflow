<script>
  let { status } = $props();

  const config = {
    pending: { label: "Pending", bg: "bg-gray-100", text: "text-gray-500" },
    running: { label: "Running", bg: "bg-amber-100", text: "text-amber-700" },
    awaiting_review: { label: "Awaiting Review", bg: "bg-blue-100", text: "text-blue-700" },
    confirmed: { label: "Confirmed", bg: "bg-green-100", text: "text-green-700" },
    complete: { label: "Complete", bg: "bg-green-100", text: "text-green-700" },
  };

  let c = $derived(config[status] || config.pending);
</script>

<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium {c.bg} {c.text}">
  {#if status === "running"}
    <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
  {/if}
  {c.label}
</span>
