// concatenates src/ + vendor libs + world data into ONE html file
const fs = require('fs'), path = require('path');
const r = p => fs.readFileSync(path.join(__dirname, p), 'utf8');
const nm = p => fs.readFileSync(path.join(__dirname, 'node_modules', p), 'utf8');
const js = fs.readdirSync(path.join(__dirname, 'src/js')).filter(f => f.endsWith('.js')).sort().map(f => `\n/* ---- ${f} ---- */\n` + r('src/js/' + f)).join('\n');
const world = JSON.stringify(JSON.parse(fs.readFileSync(path.join(__dirname, 'node_modules/world-atlas/countries-50m.json'), 'utf8')));
const vendor = [nm('three/build/three.min.js'), nm('topojson-client/dist/topojson-client.min.js'), nm('satellite.js/dist/satellite.min.js')].join(';\n').replace(/<\/script/gi, '<\\/script');
let html = r('src/index.html');
const put = (k, v) => { html = html.replace(k, () => v); };
put('/*__CSS__*/', r('src/style.css'));
put('/*__VENDOR__*/', vendor);
put('/*__DATA__*/', 'window.__WORLD=' + world + ';');
put('/*__JS__*/', js.replace(/<\/script/gi, '<\\/script'));
fs.writeFileSync(path.join(__dirname, 'helix-ui.html'), html);
console.log('built helix-ui.html', (html.length / 1048576).toFixed(2) + ' MB');
