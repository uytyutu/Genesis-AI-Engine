/** Voice commands that stop TTS — shared by mic input and interrupt listener. */

const INTERRUPT_EXACT_RE =
  /^(стоп|остановись|подожди|подождите|не надо|хватит|стой|stop|wait|нет|тише|замолчи)[.!?,]*$/i;

const INTERRUPT_PREFIX_RE =
  /^(стоп|остановись|подожди|не надо|хватит|стой|замолчи)\b/i;

export function isInterruptPhrase(text: string): boolean {
  const t = text.trim();
  if (!t) return false;
  if (INTERRUPT_EXACT_RE.test(t)) return true;
  return INTERRUPT_PREFIX_RE.test(t) && t.length < 48;
}
