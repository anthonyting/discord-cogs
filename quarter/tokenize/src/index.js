import jsTokens from 'js-tokens';

process.stdout.setEncoding('utf-8');

const DELIMITER = "DONE";

/**
 * 
 * @param {string} data 
 * @param {boolean} newLine
 */
function output(data, newLine = true) {
  process.stdout.write(Buffer.from(`${data}${newLine ? '\n' : ''}`, 'utf-8'));
}

output(`STARTED TOKENIZER`);

process.stdin.on('data', (data) => {
  const script = data.toString('utf-8');
  const tokenized = jsTokens(script);

  for (const token of tokenized) {
    /** @type {import('js-tokens').Token} */
    const typedToken = token;
    if (typedToken.type === "StringLiteral") {
      output(typedToken.value);
    }
  }

  output(DELIMITER);
});
