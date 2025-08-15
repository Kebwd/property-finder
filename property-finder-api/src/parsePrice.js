export function parseChinesePrice(input) {
  if (typeof input === 'number') {
    return input;
  }

  if (typeof input !== 'string') {
    throw new Error(`Price must be a string or number, got ${typeof input}`);
  }

  const s = input.replace(/,/g, '').trim();
  if (!s) throw new Error('Price cannot be empty');

  const match = /^(\d+(?:\.\d+)?)(萬|億)?$/.exec(s);
  if (!match) {
    throw new Error(`Invalid price format: "${input}"`);
  }

  const [, numPart, unit] = match;
  const base = Number(numPart);
  if (isNaN(base)) throw new Error(`Cannot parse number: "${numPart}"`);

  switch (unit) {
    case '萬': return base * 1e4;
    case '億': return base * 1e8;
    default:   return base;
  }
}