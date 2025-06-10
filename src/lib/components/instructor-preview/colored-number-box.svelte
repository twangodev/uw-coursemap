<script lang="ts">
  interface Props {
    amount: number | undefined;
    description: string;
    scale?: number;
    invert?: boolean;
  }

  let { amount, description, scale = 1, invert = false }: Props = $props();

  let scaledAmount = (amount ?? -1) / scale;
  let invertedAmount = invert ? 1 - scaledAmount : scaledAmount;

  function getColorClass(rating: number | undefined) {
    if (!rating || rating < 0 || rating > 1) {
      return "bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-200"; // Unknown or invalid rating
    } else if (rating >= 0.0 && rating < 0.2) {
      return "bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200"; // Very poor rating
    } else if (rating >= 0.2 && rating < 0.4) {
      return "bg-orange-200 text-orange-800 dark:bg-orange-800 dark:text-orange-200"; // Poor rating
    } else if (rating >= 0.4 && rating < 0.6) {
      return "bg-yellow-400 text-yellow-900 dark:bg-yellow-900 dark:text-yellow-200"; // Average rating
    } else if (rating >= 0.6 && rating < 0.8) {
      return "bg-yellow-200 text-yellow-900 dark:bg-yellow-900 dark:text-yellow-400"; // Good rating
    } else if (rating >= 0.8 && rating <= 1) {
      return "bg-green-200 text-green-900 dark:bg-green-900 dark:text-green-300"; // Excellent rating
    } else {
      return "bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-200"; // Fallback
    }
  }
</script>

<div class="flex flex-col items-center">
  <div
    class="flex h-full min-w-14 items-center justify-center rounded-lg py-4 text-xl font-bold {getColorClass(
      invertedAmount,
    )}"
  >
    {amount?.toFixed(1) || "?"}
  </div>
  <span class="text-muted-foreground mt-1 text-xs">{description}</span>
</div>
