const NORMAL = ['#8a9285', '#e58f85', '#a6c295', '#e1bd7e', '#92b5d2', '#c9a2cd', '#91c4bb', '#d4d9cb'];
const BRIGHT = ['#a4ab9c', '#ffaca1', '#c1dfa9', '#f3d296', '#b3d2ef', '#e0bce6', '#b0e0d5', '#f0f2e7'];
const ESC = '\u001b';
const MAX_PARAMETERS = 64;

/**
 * Parse a stream into inert text/style tokens. No HTML or terminal operations are
 * emitted. Keep one parser per connection, and reset it when that connection ends.
 * Control sequences may span any number of calls without retaining their bodies.
 */
export function createAnsiParser() {
  let mode = 'text';
  let parameters = '';
  let overflow = false;
  let color;
  let bold = false;

  function reset() {
    mode = 'text';
    parameters = '';
    overflow = false;
    color = undefined;
    bold = false;
  }

  function applySgr() {
    if (overflow || !/^\d*(?:;\d*)*$/.test(parameters)) return;
    const codes = parameters.split(';').map(value => Number(value || 0));
    for (let i = 0; i < codes.length; i++) {
      const code = codes[i];
      if (code === 0) { color = undefined; bold = false; }
      else if (code === 1) bold = true;
      else if (code === 22) bold = false;
      else if (code === 39) color = undefined;
      else if (code >= 30 && code <= 37) color = NORMAL[code - 30];
      else if (code >= 90 && code <= 97) color = BRIGHT[code - 90];
      // Extended foreground/background colors are unsupported. Consume their
      // arguments so RGB values cannot accidentally become unrelated SGR codes.
      else if (code === 38 || code === 48 || code === 58) {
        if (codes[i + 1] === 5) i += 2;
        else if (codes[i + 1] === 2) i += 4;
      }
    }
  }

  function push(text) {
    if (typeof text !== 'string') throw new TypeError('ANSI input must be a string.');
    const tokens = [];
    let pending = '';
    const flush = () => {
      if (!pending) return;
      const previous = tokens[tokens.length - 1];
      if (previous && previous.color === color && !!previous.bold === bold) previous.text += pending;
      else tokens.push({ text: pending, ...(color ? { color } : {}), ...(bold ? { bold: true } : {}) });
      pending = '';
    };
    const startCsi = () => { mode = 'csi'; parameters = ''; overflow = false; };

    for (const character of text) {
      const code = character.codePointAt(0);
      if (mode === 'string' || mode === 'osc') {
        if (character === ESC) mode = mode === 'osc' ? 'osc-escape' : 'string-escape';
        else if (code === 0x9c || (mode === 'osc' && code === 7)) mode = 'text';
        continue;
      }
      if (mode === 'string-escape' || mode === 'osc-escape') {
        const isOsc = mode === 'osc-escape';
        if (character === '\\' || code === 0x9c || (isOsc && code === 7)) mode = 'text';
        else if (character !== ESC) mode = isOsc ? 'osc' : 'string';
        continue;
      }
      if (mode === 'escape' || mode === 'escape-intermediate') {
        if (character === ESC) mode = 'escape';
        else if (mode === 'escape' && character === '[') startCsi();
        else if (mode === 'escape' && character === ']') mode = 'osc';
        else if (mode === 'escape' && ['P', '^', '_', 'X'].includes(character)) mode = 'string';
        else if (code >= 0x20 && code <= 0x2f) mode = 'escape-intermediate';
        else if (code >= 0x30 && code <= 0x7e) mode = 'text';
        else if (code > 0x7f) mode = 'text';
        continue;
      }
      if (mode === 'csi') {
        if (character === ESC) { mode = 'escape'; parameters = ''; overflow = false; }
        else if (code >= 0x40 && code <= 0x7e) {
          if (character === 'm') applySgr();
          mode = 'text'; parameters = ''; overflow = false;
        } else if (code >= 0x20 && code <= 0x3f) {
          if (parameters.length < MAX_PARAMETERS) parameters += character;
          else overflow = true;
        }
        continue;
      }

      if (character === ESC) { flush(); mode = 'escape'; }
      else if (code === 0x9b) { flush(); startCsi(); }
      else if (code === 0x9d) { flush(); mode = 'osc'; }
      else if ([0x90, 0x98, 0x9e, 0x9f].includes(code)) { flush(); mode = 'string'; }
      else if (character === '\n' || character === '\t' || (code >= 0x20 && code !== 0x7f && !(code >= 0x80 && code <= 0x9f))) pending += character;
      // Drop CR, BEL, backspace, DEL and all other C0/C1 terminal controls.
    }
    flush();
    return tokens;
  }

  return { push, reset };
}
