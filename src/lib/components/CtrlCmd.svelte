<script>
    // Detect the user's operating system
    let isMac = false;

    if (typeof navigator !== 'undefined') {
        if ('userAgent' in navigator) {
            isMac = navigator.userAgent.toLowerCase().includes('mac');
        }
    }
</script>

{#if isMac}
    <span class="text-xs">⌘</span>
{:else}
    Ctrl+
{/if}

