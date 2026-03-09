<script>
  let { onclick, disabled = false, label = "Confirm & Continue" } = $props();
</script>

<button
  {onclick}
  {disabled}
  class="px-6 py-2.5 rounded-lg font-medium text-white transition-all
         {disabled
           ? 'bg-gray-300 cursor-not-allowed'
           : 'bg-[var(--navy)] hover:bg-[#2a3580] active:scale-[0.98] shadow-md hover:shadow-lg'}"
>
  {label}
</button>
