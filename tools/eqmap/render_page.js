// Renders a list of TeX strings to self-contained SVG with MathJax.
// Input JSON: [{"tex": "...", "display": true|false}, ...]; output JSON: list of <svg> strings.
// The page uses static SVG instead of in-browser KaTeX, which some Safari versions lay out wrongly.
// Usage: npm i mathjax-full@3.2.2 && node render_page.js in.json out.json
const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
require('mathjax-full/js/input/tex/AllPackages.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
const fs = require('fs');
const adaptor = liteAdaptor(); RegisterHTMLHandler(adaptor);
const doc = mathjax.document('', {InputJax: new TeX({packages: ['base', 'ams', 'html', 'newcommand']}),
                                  OutputJax: new SVG({fontCache: 'none'})});
const items = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = items.map(it => adaptor.innerHTML(doc.convert(it.tex, {display: it.display})));
fs.writeFileSync(process.argv[3], JSON.stringify(out));
