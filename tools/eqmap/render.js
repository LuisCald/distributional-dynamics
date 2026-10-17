// Renders the data-map equations (tools/eqmap/equations.json) to self-contained SVG, pasted into index.html.
// Static SVG instead of KaTeX: some Safari versions mis-lay out KaTeX in this block. const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js'); require('mathjax-full/js/input/tex/AllPackages.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
const fs = require('fs');
const adaptor = liteAdaptor(); RegisterHTMLHandler(adaptor);
const doc = mathjax.document('', {InputJax: new TeX({packages: ['base','ams','html','newcommand']}), OutputJax: new SVG({fontCache: 'none'})});
const eqs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = {};
for (const [k, tex] of Object.entries(eqs)) {
  const node = doc.convert(tex, {display: true});
  out[k] = adaptor.innerHTML(node);   // the <svg>
}
fs.writeFileSync(process.argv[3], JSON.stringify(out));
