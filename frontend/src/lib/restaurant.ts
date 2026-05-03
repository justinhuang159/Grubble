export function formatRestaurantPrice(price: string | null): string | null {
  if (!price) {
    return null;
  }

  const trimmedPrice = price.trim();
  if (!trimmedPrice) {
    return null;
  }

  if (/^\d+$/.test(trimmedPrice)) {
    const level = Number.parseInt(trimmedPrice, 10);
    if (level > 0) {
      return "$".repeat(level);
    }
  }

  return trimmedPrice;
}
